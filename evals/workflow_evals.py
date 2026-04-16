"""
Workflow transition evaluators.

Tests the data handoff between nodes to ensure information flows
correctly through the pipeline. Uses hybrid script + LLM evaluation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from evals.eval_config import EVAL_LLM_TEMPERATURE, EVAL_MODEL_NAME, SCRIPT_WEIGHT, LLM_WEIGHT


@dataclass
class TransitionEvalResult:
    """Result of a workflow transition evaluation."""
    transition_name: str
    from_node: str
    to_node: str
    script_score: float = 0.0
    llm_score: float = 0.0
    combined_score: float = 0.0
    script_details: str = ""
    llm_reasoning: str = ""
    checks_passed: int = 0
    checks_total: int = 0


def _llm_eval_transition(prompt: str) -> tuple[float, str]:
    """Run an LLM eval for a transition and return (score_0_to_1, reasoning)."""
    try:
        llm = ChatGroq(model=EVAL_MODEL_NAME, temperature=EVAL_LLM_TEMPERATURE)
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(content[json_start:json_end])
            raw_score = max(1, min(10, int(result.get("score", 5))))
            return round(raw_score / 10.0, 2), result.get("reasoning", "")
        return 0.5, "Could not parse LLM response"
    except Exception as e:
        return 0.5, f"LLM eval error: {str(e)}"


# ─────────────────────────────────────────────────────────────────
# Transition 1: Decomposition → Retrieval
# ─────────────────────────────────────────────────────────────────
def eval_decomposition_to_retrieval(state: dict) -> TransitionEvalResult:
    """Test that retrieval covers all sub-question IDs from decomposition."""
    sub_questions = state.get("sub_questions", [])
    search_results = state.get("search_results", {})

    # Script checks
    sq_ids = {sq.get("id", "") for sq in sub_questions}
    result_ids = set(search_results.keys()) if isinstance(search_results, dict) else set()

    covered = sq_ids.intersection(result_ids)
    coverage_ratio = len(covered) / len(sq_ids) if sq_ids else 0

    # Check: all sub-questions have results
    all_covered = sq_ids.issubset(result_ids)
    # Check: each covered sub-question has ≥1 source
    all_have_sources = all(
        isinstance(search_results.get(sq_id), list) and len(search_results.get(sq_id, [])) > 0
        for sq_id in covered
    )

    checks_passed = sum([all_covered, all_have_sources])
    checks_total = 2
    script_score = round(checks_passed / checks_total, 3)

    script_details = (
        f"Sub-question IDs: {sq_ids} | "
        f"Result IDs: {result_ids} | "
        f"Coverage: {len(covered)}/{len(sq_ids)} | "
        f"All have sources: {all_have_sources}"
    )

    # LLM eval
    sq_formatted = json.dumps(sub_questions[:4], indent=2)
    results_summary = []
    for sq_id in list(search_results.keys())[:4]:
        sources = search_results.get(sq_id, [])
        if isinstance(sources, list):
            titles = [s.get("title", "?") for s in sources[:3]]
            results_summary.append(f"  {sq_id}: {len(sources)} sources — {titles}")
    results_text = "\n".join(results_summary) if results_summary else "No results"

    prompt = f"""You are evaluating the DATA HANDOFF between Query Decomposition and Retrieval in a research pipeline.

**Sub-Questions generated:**
{sq_formatted}

**Search Results per Sub-Question:**
{results_text}

**Grade (1-10): Were the search queries well-targeted to each sub-question?**
- Are retrieved sources relevant to each specific sub-question (not generic)?
- Does each sub-question have dedicated, distinct sources?
- Is there evidence the retrieval agent adapted its strategy per sub-question type?

Respond with ONLY: {{"score": <1-10>, "reasoning": "explanation"}}"""

    llm_score, llm_reasoning = _llm_eval_transition(prompt)

    combined = round(SCRIPT_WEIGHT * script_score + LLM_WEIGHT * llm_score, 3)

    return TransitionEvalResult(
        transition_name="decomposition_to_retrieval",
        from_node="decomposition",
        to_node="retrieval",
        script_score=script_score,
        llm_score=llm_score,
        combined_score=combined,
        script_details=script_details,
        llm_reasoning=llm_reasoning,
        checks_passed=checks_passed,
        checks_total=checks_total,
    )


# ─────────────────────────────────────────────────────────────────
# Transition 2: Processing → Synthesis
# ─────────────────────────────────────────────────────────────────
def eval_processing_to_synthesis(state: dict) -> TransitionEvalResult:
    """Test that claims from processing propagate into synthesis themes."""
    processed = state.get("processed_data", {})
    insights = state.get("insights", {})

    claims = processed.get("claims", [])
    themes = insights.get("themes", [])

    # Script checks
    # Check 1: themes exist if claims exist
    themes_from_claims = len(themes) > 0 if len(claims) > 0 else True
    # Check 2: contradictions in processing reflect in conflicts in synthesis
    proc_contras = processed.get("contradictions", [])
    synth_conflicts = insights.get("conflicts", [])
    contras_propagated = len(synth_conflicts) > 0 if len(proc_contras) > 0 else True

    checks_passed = sum([themes_from_claims, contras_propagated])
    checks_total = 2
    script_score = round(checks_passed / checks_total, 3)

    script_details = (
        f"Claims→Themes: {len(claims)} claims → {len(themes)} themes | "
        f"Contradictions→Conflicts: {len(proc_contras)} → {len(synth_conflicts)}"
    )

    # LLM eval
    claims_sample = json.dumps(claims[:5], indent=2) if claims else "[]"
    themes_sample = json.dumps(themes[:4], indent=2) if themes else "[]"

    prompt = f"""You are evaluating the DATA HANDOFF between Source Processing and Synthesis in a research pipeline.

**Claims Extracted (sample):**
{claims_sample}

**Themes Synthesized:**
{themes_sample}

**Grade (1-10): Does the synthesis accurately represent the processed data?**
- Do themes logically emerge from the extracted claims?
- Are contradictions from processing reflected as conflicts in synthesis?
- Is the synthesis faithful to the evidence, not adding unsupported themes?

Respond with ONLY: {{"score": <1-10>, "reasoning": "explanation"}}"""

    llm_score, llm_reasoning = _llm_eval_transition(prompt)

    combined = round(SCRIPT_WEIGHT * script_score + LLM_WEIGHT * llm_score, 3)

    return TransitionEvalResult(
        transition_name="processing_to_synthesis",
        from_node="processing",
        to_node="synthesis",
        script_score=script_score,
        llm_score=llm_score,
        combined_score=combined,
        script_details=script_details,
        llm_reasoning=llm_reasoning,
        checks_passed=checks_passed,
        checks_total=checks_total,
    )


# ─────────────────────────────────────────────────────────────────
# Transition 3: Review → Refinement
# ─────────────────────────────────────────────────────────────────
def eval_review_to_refinement(state: dict) -> TransitionEvalResult:
    """Test that review feedback is addressed in the final report."""
    review = state.get("review_feedback", {})
    final_report = state.get("final_report", "")
    draft = state.get("draft", "")

    if not isinstance(final_report, str):
        final_report = str(final_report)
    if not isinstance(draft, str):
        draft = str(draft)

    # Script checks
    # Check 1: final report length ≥ draft (refinement shouldn't strip)
    length_ok = len(final_report) >= len(draft) * 0.8 if draft else True

    # Check 2: if review had gaps, report should be different from draft
    gaps = review.get("gaps", [])
    report_differs = final_report != draft
    feedback_addressed = report_differs if gaps else True

    checks_passed = sum([length_ok, feedback_addressed])
    checks_total = 2
    script_score = round(checks_passed / checks_total, 3)

    script_details = (
        f"Report ≥ Draft: {len(final_report)} vs {len(draft)} (ok={length_ok}) | "
        f"Feedback addressed: {feedback_addressed} ({len(gaps)} gaps)"
    )

    # LLM eval
    review_formatted = json.dumps(review, indent=2)
    report_preview = final_report[:2000] if final_report else "EMPTY"

    prompt = f"""You are evaluating the DATA HANDOFF between Quality Review and Final Refinement in a research pipeline.

**Review Feedback:**
{review_formatted}

**Final Report (preview):**
{report_preview}

**Grade (1-10): Did the refinement meaningfully improve the draft based on review feedback?**
- Are the specific gaps identified in the review now addressed?
- Are the issues (unsourced claims, vague language, etc.) fixed?
- Does the final report show genuine improvement over what was reviewed?

Respond with ONLY: {{"score": <1-10>, "reasoning": "explanation"}}"""

    llm_score, llm_reasoning = _llm_eval_transition(prompt)

    combined = round(SCRIPT_WEIGHT * script_score + LLM_WEIGHT * llm_score, 3)

    return TransitionEvalResult(
        transition_name="review_to_refinement",
        from_node="review",
        to_node="refinement",
        script_score=script_score,
        llm_score=llm_score,
        combined_score=combined,
        script_details=script_details,
        llm_reasoning=llm_reasoning,
        checks_passed=checks_passed,
        checks_total=checks_total,
    )


# ─────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────
WORKFLOW_EVAL_REGISTRY = {
    "decomposition_to_retrieval": eval_decomposition_to_retrieval,
    "processing_to_synthesis": eval_processing_to_synthesis,
    "review_to_refinement": eval_review_to_refinement,
}
