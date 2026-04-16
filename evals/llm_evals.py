"""
LLM-based semantic evaluators for each pipeline node.

Each evaluator sends the node's input/output to an LLM with a specific
grading prompt and expects a structured JSON response with score (1-10),
reasoning, strengths, and weaknesses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from evals.eval_config import EVAL_LLM_TEMPERATURE, EVAL_MODEL_NAME


@dataclass
class LLMEvalResult:
    """Result of an LLM-based semantic evaluation."""
    score: float          # 0.0–1.0 (normalized from 1–10)
    raw_score: int        # Original 1–10 score from LLM
    reasoning: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    error: str = ""       # Non-empty if eval failed


def _get_eval_llm() -> ChatGroq:
    """Create a low-temperature LLM for strict grading."""
    return ChatGroq(
        model=EVAL_MODEL_NAME,
        temperature=EVAL_LLM_TEMPERATURE,
    )


def _run_eval_prompt(prompt: str) -> LLMEvalResult:
    """Send an eval prompt to the LLM and parse the structured response."""
    try:
        llm = _get_eval_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        # Parse JSON from response
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(content[json_start:json_end])
            raw_score = int(result.get("score", 5))
            raw_score = max(1, min(10, raw_score))  # Clamp
            return LLMEvalResult(
                score=round(raw_score / 10.0, 2),
                raw_score=raw_score,
                reasoning=result.get("reasoning", ""),
                strengths=result.get("strengths", []),
                weaknesses=result.get("weaknesses", []),
            )
        # Fallback: try to find just a number
        return LLMEvalResult(score=0.5, raw_score=5, reasoning="Could not parse structured response", error="parse_error")

    except Exception as e:
        return LLMEvalResult(score=0.5, raw_score=5, reasoning=f"Eval error: {str(e)}", error=str(e))


# ─── Eval Response Format (shared suffix for all prompts) ────────
_RESPONSE_FORMAT = """
**Respond with ONLY a JSON object:**
{
    "score": <1-10 integer>,
    "reasoning": "2-3 sentence explanation of your score",
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"]
}
"""


# ─────────────────────────────────────────────────────────────────
# N1: Query Intake
# ─────────────────────────────────────────────────────────────────
def llm_eval_query_intake(input_state: dict, output: dict) -> LLMEvalResult:
    """LLM evaluates the quality of query refinement."""
    prompt = f"""You are an expert evaluator assessing the quality of a QUERY REFINEMENT step.

**Original User Query:** {input_state.get("query", "")}
**Refined Query:** {output.get("refined_query", "")}

**Grade on these criteria (1-10):**
1. Did the refinement remove ambiguity while preserving the user's original intent?
2. Is the refined query specific enough to yield targeted search results?
3. Is it suitable for academic-style research (no slang, clear terminology)?
4. Was necessary context added without over-scoping the query?

Score 8+ only if the refinement clearly improves searchability while keeping intent intact.
Score 4-7 if refinement is acceptable but could be better.
Score 1-3 if refinement distorts intent, is too vague, or adds no value.

{_RESPONSE_FORMAT}"""
    return _run_eval_prompt(prompt)


# ─────────────────────────────────────────────────────────────────
# N2: Decomposition
# ─────────────────────────────────────────────────────────────────
def llm_eval_decomposition(input_state: dict, output: dict) -> LLMEvalResult:
    """LLM evaluates the quality of query decomposition."""
    sub_questions = output.get("sub_questions", [])
    sq_formatted = json.dumps(sub_questions, indent=2)
    prompt = f"""You are an expert evaluator assessing the quality of RESEARCH QUERY DECOMPOSITION.

**Refined Query:** {input_state.get("refined_query", "")}
**Generated Sub-Questions:**
{sq_formatted}

**Grade on these criteria (1-10):**
1. Do the 4 sub-questions cover genuinely orthogonal research dimensions (mechanism, impact, evidence, contradictions)?
2. Are they specific enough to yield useful, distinct search results (not generic rewordings)?
3. Would answering all 4 sub-questions provide comprehensive coverage of the research topic?
4. Is each sub-question properly categorized under its type (mechanism/impact/evidence/contradictions)?

Score 8+ only if questions are well-differentiated, specific, and would lead to comprehensive research.
Score 4-7 if questions are acceptable but overlap or are too generic.
Score 1-3 if questions are redundant, miss key dimensions, or are poorly formed.

{_RESPONSE_FORMAT}"""
    return _run_eval_prompt(prompt)


# ─────────────────────────────────────────────────────────────────
# N3: Retrieval
# ─────────────────────────────────────────────────────────────────
def llm_eval_retrieval(input_state: dict, output: dict) -> LLMEvalResult:
    """LLM evaluates the quality of retrieved sources."""
    search_results = output.get("search_results", {})
    stats = output.get("retrieval_stats", {})

    # Build a compact summary of what was retrieved
    summary_lines = []
    for sq_id, sources in search_results.items():
        if isinstance(sources, list):
            titles = [s.get("title", "?") for s in sources[:3]]
            domains = list(set(s.get("domain", "?") for s in sources))
            summary_lines.append(f"  {sq_id}: {len(sources)} sources from {domains[:3]} — Titles: {titles}")

    results_summary = "\n".join(summary_lines) if summary_lines else "No results"

    prompt = f"""You are an expert evaluator assessing the quality of AUTONOMOUS WEB RETRIEVAL for research.

**Research Query:** {input_state.get("refined_query", "")}
**Sub-Questions:** {json.dumps(input_state.get("sub_questions", [])[:4], indent=2)}

**Retrieval Results Summary:**
{results_summary}

**Retrieval Stats:** {json.dumps(stats)}

**Grade on these criteria (1-10):**
1. Do the sources cover diverse perspectives on the topic (not just one viewpoint)?
2. Is there sufficient depth per sub-question (≥3 quality sources each)?
3. Is there source diversity (multiple domains, not all from the same site)?
4. Are the retrieved sources likely to be credible for academic research?

Score 8+ only if retrieval demonstrates genuine diversity, depth, and relevance.
Score 4-7 if coverage is acceptable but shallow or lacks diversity.
Score 1-3 if sources are irrelevant, redundant, or from low-quality sites.

{_RESPONSE_FORMAT}"""
    return _run_eval_prompt(prompt)


# ─────────────────────────────────────────────────────────────────
# N4: Processing
# ─────────────────────────────────────────────────────────────────
def llm_eval_processing(input_state: dict, output: dict) -> LLMEvalResult:
    """LLM evaluates the quality of source processing."""
    processed = output.get("processed_data", output)
    claims_sample = json.dumps(processed.get("claims", [])[:5], indent=2)
    contras_sample = json.dumps(processed.get("contradictions", [])[:3], indent=2)
    agreements_sample = json.dumps(processed.get("agreements", [])[:3], indent=2)

    prompt = f"""You are an expert evaluator assessing the quality of SOURCE PROCESSING AND ANALYSIS.

**Research Query:** {input_state.get("refined_query", "")}

**Sample Claims Extracted (first 5):**
{claims_sample}

**Sample Agreements (first 3):**
{agreements_sample}

**Sample Contradictions (first 3):**
{contras_sample}

**Source Scores Count:** {len(processed.get("sources_with_scores", []))}

**Grade on these criteria (1-10):**
1. Are claims accurately and precisely extracted (specific, not vague)?
2. Are identified contradictions genuine disagreements between sources (not manufactured)?
3. Are agreements based on actual multi-source consensus (not trivial observations)?
4. Do source scores seem justified given source types (higher for academic, lower for blogs)?

Score 8+ only if processing shows deep analytical quality — precise claims, genuine contradictions.
Score 4-7 if processing is functional but claims are vague or contradictions seem forced.
Score 1-3 if claims are inaccurate, contradictions are manufactured, or analysis is superficial.

{_RESPONSE_FORMAT}"""
    return _run_eval_prompt(prompt)


# ─────────────────────────────────────────────────────────────────
# N5: Synthesis
# ─────────────────────────────────────────────────────────────────
def llm_eval_synthesis(input_state: dict, output: dict) -> LLMEvalResult:
    """LLM evaluates the quality of insight synthesis."""
    insights = output.get("insights", output)
    themes_formatted = json.dumps(insights.get("themes", [])[:4], indent=2)
    views_formatted = json.dumps(insights.get("dominant_views", [])[:3], indent=2)
    confidence = insights.get("confidence_levels", {})

    prompt = f"""You are an expert evaluator assessing the quality of RESEARCH SYNTHESIS.

**Research Query:** {input_state.get("refined_query", "")}

**Themes Identified:**
{themes_formatted}

**Dominant Views:**
{views_formatted}

**Confidence Assessment:** {json.dumps(confidence)}

**Number of conflicts identified:** {len(insights.get("conflicts", []))}
**Number of minority views:** {len(insights.get("minority_views", []))}

**Grade on these criteria (1-10):**
1. Do the identified themes logically follow from the processed data?
2. Are confidence levels appropriately calibrated given the strength of evidence?
3. Are dominant vs. minority views correctly distinguished?
4. Does the synthesis add analytical value beyond just listing findings?

Score 8+ only if synthesis demonstrates genuine intellectual integration across sources.
Score 4-7 if synthesis is reasonable but lacks depth or nuance.
Score 1-3 if themes are disconnected from data or confidence levels are arbitrary.

{_RESPONSE_FORMAT}"""
    return _run_eval_prompt(prompt)


# ─────────────────────────────────────────────────────────────────
# N6: Outline
# ─────────────────────────────────────────────────────────────────
def llm_eval_outline(input_state: dict, output: dict) -> LLMEvalResult:
    """LLM evaluates the quality of the report outline."""
    outline = output.get("outline", output)
    outline_formatted = json.dumps(outline, indent=2)

    prompt = f"""You are an expert evaluator assessing the quality of a RESEARCH REPORT OUTLINE.

**Research Query:** {input_state.get("refined_query", "")}

**Outline:**
{outline_formatted}

**Grade on these criteria (1-10):**
1. Does the outline structure support a logical, persuasive argument flow?
2. Are sections properly scoped — not too broad, not too narrow?
3. Does the outline cover all key themes and perspectives from the research?
4. Would following this outline produce a comprehensive, well-structured report?

Score 8+ only if the outline demonstrates clear narrative structure and comprehensive coverage.
Score 4-7 if the outline is functional but generic or missing key sections.
Score 1-3 if the outline is disorganized, incomplete, or doesn't address the query.

{_RESPONSE_FORMAT}"""
    return _run_eval_prompt(prompt)


# ─────────────────────────────────────────────────────────────────
# N7: Draft
# ─────────────────────────────────────────────────────────────────
def llm_eval_draft(input_state: dict, output: dict) -> LLMEvalResult:
    """LLM evaluates the quality of the draft report."""
    draft = output.get("draft", "")
    if not isinstance(draft, str):
        draft = str(draft)

    # Truncate for LLM context
    draft_preview = draft[:3000] + "..." if len(draft) > 3000 else draft

    prompt = f"""You are an expert evaluator assessing the quality of a RESEARCH DRAFT REPORT.

**Research Query:** {input_state.get("refined_query", "")}
**Draft Report (preview, {len(draft)} total chars):**
{draft_preview}

**Grade on these criteria (1-10):**
1. Is every major claim evidence-backed with a specific source citation?
2. Is the writing fluent, academic, and accessible (not robotic or overly casual)?
3. Are contradictions and opposing views acknowledged and discussed (not one-sided)?
4. Does the report provide specific data, statistics, or expert opinions rather than generic statements?
5. Does it have proper introduction and conclusion sections?

Score 8+ only if the draft reads like a well-researched, properly cited academic review.
Score 4-7 if the draft is passable but has unsourced claims, vague language, or is one-sided.
Score 1-3 if the draft is superficial, uncited, or doesn't address the research query.

{_RESPONSE_FORMAT}"""
    return _run_eval_prompt(prompt)


# ─────────────────────────────────────────────────────────────────
# N8: Review
# ─────────────────────────────────────────────────────────────────
def llm_eval_review(input_state: dict, output: dict) -> LLMEvalResult:
    """LLM evaluates the quality of the review itself."""
    review = output.get("review_feedback", output)
    review_formatted = json.dumps(review, indent=2)

    draft_preview = input_state.get("draft", "")[:1500]

    prompt = f"""You are an expert evaluator assessing the quality of a QUALITY REVIEW of a research report.

**Draft Preview ({len(input_state.get("draft", ""))} total chars):** {draft_preview}...

**Review Output:**
{review_formatted}

**Grade on these criteria (1-10):**
1. Is the review thorough — does it check for coverage, evidence, structure, and clarity?
2. Are identified gaps genuine and actionable (not fabricated or trivial)?
3. Is the pass/fail decision appropriate given the draft quality?
4. Are improvement suggestions specific enough to act on?

Score 8+ only if the review is thorough, identifies real issues, and provides actionable feedback.
Score 4-7 if the review is surface-level but catches some genuine issues.
Score 1-3 if the review is rubber-stamped, misses obvious issues, or provides vague feedback.

{_RESPONSE_FORMAT}"""
    return _run_eval_prompt(prompt)


# ─────────────────────────────────────────────────────────────────
# N9: Refinement
# ─────────────────────────────────────────────────────────────────
def llm_eval_refinement(input_state: dict, output: dict) -> LLMEvalResult:
    """LLM evaluates the quality of the final refined report."""
    final_report = output.get("final_report", "")
    if not isinstance(final_report, str):
        final_report = str(final_report)

    review_feedback = input_state.get("review_feedback", {})
    report_preview = final_report[:3000] + "..." if len(final_report) > 3000 else final_report

    prompt = f"""You are an expert evaluator assessing the quality of a FINAL REFINED RESEARCH REPORT.

**Review Feedback That Should Be Addressed:** {json.dumps(review_feedback, indent=2)}

**Final Report (preview, {len(final_report)} total chars):**
{report_preview}

**Grade on these criteria (1-10):**
1. Did the refinement address the review feedback's identified gaps and issues?
2. Is the final report publication-ready (polished language, proper citations, clear structure)?
3. Does it have a proper Sources/References section listing all cited URLs?
4. Is the overall quality significantly better than what would be expected from a single-pass LLM output?

Score 8+ only if the report is comprehensive, well-cited, and shows evidence of iterative improvement.
Score 4-7 if the report is acceptable but still has minor gaps or rough edges.
Score 1-3 if the report ignored review feedback, lacks citations, or is poorly structured.

{_RESPONSE_FORMAT}"""
    return _run_eval_prompt(prompt)


# ─────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────
LLM_EVAL_REGISTRY = {
    "query_intake": llm_eval_query_intake,
    "decomposition": llm_eval_decomposition,
    "retrieval": llm_eval_retrieval,
    "processing": llm_eval_processing,
    "synthesis": llm_eval_synthesis,
    "outline": llm_eval_outline,
    "draft": llm_eval_draft,
    "review": llm_eval_review,
    "refinement": llm_eval_refinement,
}
