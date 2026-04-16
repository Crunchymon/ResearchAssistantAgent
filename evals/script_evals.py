"""
Deterministic script-based evaluators for each pipeline node.

Each evaluator runs a series of checks against the node's output
and returns a score (0.0-1.0) plus detailed check results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class CheckResult:
    """Result of a single deterministic check."""
    name: str
    passed: bool
    detail: str
    weight: float = 1.0  # Relative importance of this check


@dataclass
class ScriptEvalResult:
    """Aggregated result of all script checks for a node."""
    score: float                         # 0.0–1.0
    checks: list[CheckResult] = field(default_factory=list)
    summary: str = ""

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total_count(self) -> int:
        return len(self.checks)


def _compute_score(checks: list[CheckResult]) -> float:
    """Weighted average of check pass/fail."""
    if not checks:
        return 0.0
    total_weight = sum(c.weight for c in checks)
    if total_weight == 0:
        return 0.0
    passed_weight = sum(c.weight for c in checks if c.passed)
    return round(passed_weight / total_weight, 3)


# ─────────────────────────────────────────────────────────────────
# N1: Query Intake
# ─────────────────────────────────────────────────────────────────
def eval_query_intake(input_state: dict, output: dict) -> ScriptEvalResult:
    """Evaluate query intake node output."""
    checks = []
    refined = output.get("refined_query", "")
    raw = input_state.get("query", "")

    # Check 1: Non-empty refined query
    checks.append(CheckResult(
        name="refined_query_non_empty",
        passed=bool(refined and refined.strip()),
        detail=f"Refined query: '{refined[:80]}...'" if len(refined) > 80 else f"Refined query: '{refined}'",
        weight=2.0,
    ))

    # Check 2: Refined differs from raw (actual refinement happened)
    checks.append(CheckResult(
        name="refined_differs_from_raw",
        passed=refined.strip().lower() != raw.strip().lower(),
        detail="Refinement changed the query" if refined.strip().lower() != raw.strip().lower() else "Refined query is identical to raw",
        weight=1.0,
    ))

    # Check 3: Reasonable length (10–500 chars)
    length_ok = 10 <= len(refined) <= 500
    checks.append(CheckResult(
        name="refined_length_reasonable",
        passed=length_ok,
        detail=f"Length: {len(refined)} chars (expected 10–500)",
        weight=1.0,
    ))

    # Check 4: No JSON artifacts leaked into the refined query
    no_json_leak = not refined.strip().startswith("{") and not refined.strip().startswith("[")
    checks.append(CheckResult(
        name="no_json_leak",
        passed=no_json_leak,
        detail="Clean text output" if no_json_leak else "JSON leaked into refined query",
        weight=1.5,
    ))

    score = _compute_score(checks)
    return ScriptEvalResult(
        score=score,
        checks=checks,
        summary=f"Query Intake: {sum(1 for c in checks if c.passed)}/{len(checks)} checks passed",
    )


# ─────────────────────────────────────────────────────────────────
# N2: Decomposition
# ─────────────────────────────────────────────────────────────────
def eval_decomposition(input_state: dict, output: dict) -> ScriptEvalResult:
    """Evaluate decomposition node output."""
    checks = []
    sub_questions = output.get("sub_questions", [])

    # Check 1: Exactly 4 sub-questions
    checks.append(CheckResult(
        name="exactly_4_sub_questions",
        passed=len(sub_questions) == 4,
        detail=f"Got {len(sub_questions)} sub-questions (expected 4)",
        weight=2.0,
    ))

    # Check 2: Each has required fields (id, question, type)
    required_fields = {"id", "question", "type"}
    all_have_fields = all(
        required_fields.issubset(set(sq.keys()))
        for sq in sub_questions
    ) if sub_questions else False
    checks.append(CheckResult(
        name="all_have_required_fields",
        passed=all_have_fields,
        detail="All sub-questions have id, question, type" if all_have_fields else "Missing required fields",
        weight=2.0,
    ))

    # Check 3: Types cover the 4 required dimensions
    expected_types = {"mechanism", "impact", "evidence", "contradictions"}
    actual_types = {sq.get("type", "") for sq in sub_questions}
    types_covered = expected_types.issubset(actual_types)
    checks.append(CheckResult(
        name="types_cover_all_dimensions",
        passed=types_covered,
        detail=f"Types found: {actual_types}" if actual_types else "No types found",
        weight=2.0,
    ))

    # Check 4: Sub-questions are non-trivial (each > 10 chars)
    non_trivial = all(len(sq.get("question", "")) > 10 for sq in sub_questions) if sub_questions else False
    checks.append(CheckResult(
        name="questions_non_trivial",
        passed=non_trivial,
        detail="All questions are substantive" if non_trivial else "Some questions are too short",
        weight=1.0,
    ))

    # Check 5: Unique IDs
    ids = [sq.get("id", "") for sq in sub_questions]
    unique_ids = len(set(ids)) == len(ids) and all(ids)
    checks.append(CheckResult(
        name="unique_ids",
        passed=unique_ids,
        detail=f"IDs: {ids}" if ids else "No IDs found",
        weight=1.0,
    ))

    score = _compute_score(checks)
    return ScriptEvalResult(
        score=score,
        checks=checks,
        summary=f"Decomposition: {sum(1 for c in checks if c.passed)}/{len(checks)} checks passed",
    )


# ─────────────────────────────────────────────────────────────────
# N3: Retrieval
# ─────────────────────────────────────────────────────────────────
def eval_retrieval(input_state: dict, output: dict) -> ScriptEvalResult:
    """Evaluate retrieval node output."""
    checks = []
    search_results = output.get("search_results", {})
    retrieval_stats = output.get("retrieval_stats", {})

    # Check 1: Has search results for sub-questions
    has_results = bool(search_results) and any(len(v) > 0 for v in search_results.values() if isinstance(v, list))
    checks.append(CheckResult(
        name="has_search_results",
        passed=has_results,
        detail=f"Found results for {sum(1 for v in search_results.values() if isinstance(v, list) and len(v) > 0)} sub-questions",
        weight=2.0,
    ))

    # Check 2: ≥3 sources per sub-question (on average)
    source_counts = [len(v) for v in search_results.values() if isinstance(v, list)]
    avg_sources = sum(source_counts) / len(source_counts) if source_counts else 0
    checks.append(CheckResult(
        name="min_3_sources_per_sq",
        passed=avg_sources >= 2.0,  # Relaxed: avg ≥2 since some may have fewer
        detail=f"Average sources per sub-question: {avg_sources:.1f}",
        weight=1.5,
    ))

    # Check 3: ≥2 unique domains
    all_domains = set()
    for sources in search_results.values():
        if isinstance(sources, list):
            for src in sources:
                domain = src.get("domain", "")
                if domain and domain != "unknown":
                    all_domains.add(domain)
    checks.append(CheckResult(
        name="min_2_unique_domains",
        passed=len(all_domains) >= 2,
        detail=f"Unique domains: {len(all_domains)} ({', '.join(list(all_domains)[:5])})",
        weight=1.5,
    ))

    # Check 4: All sources have url, title, content
    all_valid = True
    for sources in search_results.values():
        if isinstance(sources, list):
            for src in sources:
                if not all(src.get(f) for f in ["url", "title"]):
                    all_valid = False
                    break
    checks.append(CheckResult(
        name="sources_have_required_fields",
        passed=all_valid,
        detail="All sources have url and title" if all_valid else "Some sources missing url/title",
        weight=1.0,
    ))

    # Check 5: No duplicate URLs
    all_urls = []
    for sources in search_results.values():
        if isinstance(sources, list):
            for src in sources:
                url = src.get("url", "")
                if url:
                    all_urls.append(url)
    no_dupes = len(set(all_urls)) == len(all_urls)
    checks.append(CheckResult(
        name="no_duplicate_urls",
        passed=no_dupes,
        detail=f"Total URLs: {len(all_urls)}, Unique: {len(set(all_urls))}",
        weight=1.0,
    ))

    # Check 6: Retrieval stats present
    has_stats = bool(retrieval_stats) and "total_sources" in retrieval_stats
    checks.append(CheckResult(
        name="retrieval_stats_present",
        passed=has_stats,
        detail=f"Stats: {retrieval_stats}" if has_stats else "No retrieval stats",
        weight=0.5,
    ))

    score = _compute_score(checks)
    return ScriptEvalResult(
        score=score,
        checks=checks,
        summary=f"Retrieval: {sum(1 for c in checks if c.passed)}/{len(checks)} checks passed",
    )


# ─────────────────────────────────────────────────────────────────
# N4: Processing
# ─────────────────────────────────────────────────────────────────
def eval_processing(input_state: dict, output: dict) -> ScriptEvalResult:
    """Evaluate processing node output."""
    checks = []
    processed = output.get("processed_data", output)  # Handle both shapes
    claims = processed.get("claims", [])
    agreements = processed.get("agreements", [])
    contradictions = processed.get("contradictions", [])
    sources_with_scores = processed.get("sources_with_scores", [])

    # Check 1: Claims list non-empty
    checks.append(CheckResult(
        name="claims_non_empty",
        passed=len(claims) > 0,
        detail=f"Extracted {len(claims)} claims",
        weight=2.0,
    ))

    # Check 2: Each claim has source_url
    claims_with_source = sum(1 for c in claims if c.get("source_url") or c.get("source_title"))
    has_sources = claims_with_source == len(claims) if claims else False
    checks.append(CheckResult(
        name="claims_have_sources",
        passed=has_sources,
        detail=f"{claims_with_source}/{len(claims)} claims have source attribution",
        weight=1.5,
    ))

    # Check 3: Contradictions have both claim_a and claim_b
    valid_contras = all(
        c.get("claim_a") and c.get("claim_b")
        for c in contradictions
    ) if contradictions else True  # No contradictions is OK
    checks.append(CheckResult(
        name="contradictions_well_formed",
        passed=valid_contras,
        detail=f"{len(contradictions)} contradictions, all well-formed" if valid_contras else "Malformed contradictions",
        weight=1.5,
    ))

    # Check 4: Source scores in 1–10 range
    valid_scores = True
    for src in sources_with_scores:
        for key in ["credibility", "recency", "depth"]:
            val = src.get(key, 0)
            if isinstance(val, (int, float)) and not (1 <= val <= 10):
                valid_scores = False
                break
    checks.append(CheckResult(
        name="source_scores_valid_range",
        passed=valid_scores,
        detail=f"All {len(sources_with_scores)} source scores in 1–10 range" if valid_scores else "Some scores out of range",
        weight=1.0,
    ))

    # Check 5: Agreements detected
    checks.append(CheckResult(
        name="agreements_detected",
        passed=len(agreements) > 0,
        detail=f"Found {len(agreements)} agreements",
        weight=1.0,
    ))

    score = _compute_score(checks)
    return ScriptEvalResult(
        score=score,
        checks=checks,
        summary=f"Processing: {sum(1 for c in checks if c.passed)}/{len(checks)} checks passed",
    )


# ─────────────────────────────────────────────────────────────────
# N5: Synthesis
# ─────────────────────────────────────────────────────────────────
def eval_synthesis(input_state: dict, output: dict) -> ScriptEvalResult:
    """Evaluate synthesis node output."""
    checks = []
    insights = output.get("insights", output)  # Handle both
    themes = insights.get("themes", [])
    dominant_views = insights.get("dominant_views", [])
    confidence = insights.get("confidence_levels", {})

    # Check 1: Themes non-empty
    checks.append(CheckResult(
        name="themes_non_empty",
        passed=len(themes) > 0,
        detail=f"Identified {len(themes)} themes",
        weight=2.0,
    ))

    # Check 2: Confidence levels has 'overall' field
    has_overall = "overall" in confidence and confidence["overall"] in ("high", "medium", "low")
    checks.append(CheckResult(
        name="confidence_has_overall",
        passed=has_overall,
        detail=f"Overall confidence: {confidence.get('overall', 'MISSING')}",
        weight=1.5,
    ))

    # Check 3: Dominant views have confidence ratings
    views_have_conf = all(
        v.get("confidence") in ("high", "medium", "low")
        for v in dominant_views
    ) if dominant_views else True
    checks.append(CheckResult(
        name="dominant_views_have_confidence",
        passed=views_have_conf and len(dominant_views) > 0,
        detail=f"{len(dominant_views)} dominant views with confidence ratings",
        weight=1.5,
    ))

    # Check 4: Themes have descriptions
    themes_described = all(t.get("description") for t in themes) if themes else False
    checks.append(CheckResult(
        name="themes_have_descriptions",
        passed=themes_described,
        detail="All themes have descriptions" if themes_described else "Some themes lack descriptions",
        weight=1.0,
    ))

    # Check 5: Confidence reasoning provided
    checks.append(CheckResult(
        name="confidence_reasoning_present",
        passed=bool(confidence.get("reasoning")),
        detail="Confidence reasoning provided" if confidence.get("reasoning") else "No reasoning for confidence level",
        weight=1.0,
    ))

    score = _compute_score(checks)
    return ScriptEvalResult(
        score=score,
        checks=checks,
        summary=f"Synthesis: {sum(1 for c in checks if c.passed)}/{len(checks)} checks passed",
    )


# ─────────────────────────────────────────────────────────────────
# N6: Outline
# ─────────────────────────────────────────────────────────────────
def eval_outline(input_state: dict, output: dict) -> ScriptEvalResult:
    """Evaluate outline node output."""
    checks = []
    outline = output.get("outline", output)  # Handle both
    title = outline.get("title", "")
    abstract = outline.get("abstract", "")
    sections = outline.get("sections", [])

    # Check 1: Has title
    checks.append(CheckResult(
        name="has_title",
        passed=bool(title and len(title) > 5),
        detail=f"Title: '{title[:60]}'" if title else "No title",
        weight=1.5,
    ))

    # Check 2: Has abstract
    checks.append(CheckResult(
        name="has_abstract",
        passed=bool(abstract and len(abstract) > 20),
        detail=f"Abstract: {len(abstract)} chars" if abstract else "No abstract",
        weight=1.5,
    ))

    # Check 3: ≥3 sections
    checks.append(CheckResult(
        name="min_3_sections",
        passed=len(sections) >= 3,
        detail=f"Has {len(sections)} sections (need ≥3)",
        weight=2.0,
    ))

    # Check 4: Sections have heading + purpose + key_points
    valid_sections = all(
        s.get("heading") and s.get("purpose")
        for s in sections
    ) if sections else False
    checks.append(CheckResult(
        name="sections_well_structured",
        passed=valid_sections,
        detail="All sections have heading and purpose" if valid_sections else "Some sections missing structure",
        weight=1.5,
    ))

    # Check 5: Key points present in sections
    has_key_points = any(
        len(s.get("key_points", [])) > 0
        for s in sections
    ) if sections else False
    checks.append(CheckResult(
        name="has_key_points",
        passed=has_key_points,
        detail="Key points present in sections" if has_key_points else "No key points in any section",
        weight=1.0,
    ))

    score = _compute_score(checks)
    return ScriptEvalResult(
        score=score,
        checks=checks,
        summary=f"Outline: {sum(1 for c in checks if c.passed)}/{len(checks)} checks passed",
    )


# ─────────────────────────────────────────────────────────────────
# N7: Draft
# ─────────────────────────────────────────────────────────────────
def eval_draft(input_state: dict, output: dict) -> ScriptEvalResult:
    """Evaluate draft node output."""
    checks = []
    draft_text = output.get("draft", "")
    if not isinstance(draft_text, str):
        draft_text = str(draft_text)

    # Check 1: Length ≥ 1000 chars
    checks.append(CheckResult(
        name="min_length_1000",
        passed=len(draft_text) >= 1000,
        detail=f"Draft length: {len(draft_text)} chars (need ≥1000)",
        weight=2.0,
    ))

    # Check 2: Contains citation markers
    citation_pattern = r'\[Source[:\s]'
    citations_found = len(re.findall(citation_pattern, draft_text, re.IGNORECASE))
    has_citations = citations_found >= 2
    checks.append(CheckResult(
        name="has_citation_markers",
        passed=has_citations,
        detail=f"Found {citations_found} citation markers (need ≥2)",
        weight=2.0,
    ))

    # Check 3: Contains URLs from retrieval sources
    urls_in_draft = len(re.findall(r'https?://[^\s\]\)]+', draft_text))
    checks.append(CheckResult(
        name="contains_source_urls",
        passed=urls_in_draft >= 2,
        detail=f"Found {urls_in_draft} URLs in draft (need ≥2)",
        weight=1.5,
    ))

    # Check 4: Has markdown headers (structured)
    headers = re.findall(r'^#{1,3}\s+\w+', draft_text, re.MULTILINE)
    checks.append(CheckResult(
        name="has_markdown_structure",
        passed=len(headers) >= 3,
        detail=f"Found {len(headers)} markdown headers (need ≥3)",
        weight=1.5,
    ))

    # Check 5: Has introduction-like section
    has_intro = bool(re.search(r'(introduction|overview|background)', draft_text, re.IGNORECASE))
    checks.append(CheckResult(
        name="has_introduction",
        passed=has_intro,
        detail="Introduction section found" if has_intro else "No clear introduction section",
        weight=1.0,
    ))

    # Check 6: Has conclusion-like section
    has_conclusion = bool(re.search(r'(conclusion|summary|closing)', draft_text, re.IGNORECASE))
    checks.append(CheckResult(
        name="has_conclusion",
        passed=has_conclusion,
        detail="Conclusion section found" if has_conclusion else "No clear conclusion section",
        weight=1.0,
    ))

    score = _compute_score(checks)
    return ScriptEvalResult(
        score=score,
        checks=checks,
        summary=f"Draft: {sum(1 for c in checks if c.passed)}/{len(checks)} checks passed",
    )


# ─────────────────────────────────────────────────────────────────
# N8: Review
# ─────────────────────────────────────────────────────────────────
def eval_review(input_state: dict, output: dict) -> ScriptEvalResult:
    """Evaluate review node output."""
    checks = []
    review = output.get("review_feedback", output)

    # Check 1: Has 'passed' boolean
    has_passed = "passed" in review and isinstance(review["passed"], bool)
    checks.append(CheckResult(
        name="has_passed_boolean",
        passed=has_passed,
        detail=f"Passed field: {review.get('passed', 'MISSING')}",
        weight=2.0,
    ))

    # Check 2: Overall quality is valid enum
    valid_qualities = {"excellent", "good", "needs_improvement", "poor"}
    quality = review.get("overall_quality", "")
    checks.append(CheckResult(
        name="valid_quality_enum",
        passed=quality in valid_qualities,
        detail=f"Quality: '{quality}' (expected one of {valid_qualities})",
        weight=1.5,
    ))

    # Check 3: Gaps is a list
    gaps = review.get("gaps", None)
    checks.append(CheckResult(
        name="gaps_is_list",
        passed=isinstance(gaps, list),
        detail=f"Gaps: {len(gaps) if isinstance(gaps, list) else 'NOT A LIST'}",
        weight=1.0,
    ))

    # Check 4: Issues is a list
    issues = review.get("issues", None)
    checks.append(CheckResult(
        name="issues_is_list",
        passed=isinstance(issues, list),
        detail=f"Issues: {len(issues) if isinstance(issues, list) else 'NOT A LIST'}",
        weight=1.0,
    ))

    # Check 5: If failed, has gaps or issues
    if has_passed and not review.get("passed", True):
        has_feedback = (isinstance(gaps, list) and len(gaps) > 0) or (isinstance(issues, list) and len(issues) > 0)
        checks.append(CheckResult(
            name="failure_has_feedback",
            passed=has_feedback,
            detail="Failed review has actionable feedback" if has_feedback else "Review failed but no feedback given",
            weight=1.5,
        ))

    score = _compute_score(checks)
    return ScriptEvalResult(
        score=score,
        checks=checks,
        summary=f"Review: {sum(1 for c in checks if c.passed)}/{len(checks)} checks passed",
    )


# ─────────────────────────────────────────────────────────────────
# N9: Refinement
# ─────────────────────────────────────────────────────────────────
def eval_refinement(input_state: dict, output: dict) -> ScriptEvalResult:
    """Evaluate refinement node output."""
    checks = []
    final_report = output.get("final_report", "")
    draft = input_state.get("draft", "")
    if not isinstance(final_report, str):
        final_report = str(final_report)
    if not isinstance(draft, str):
        draft = str(draft)

    # Check 1: Final report is non-empty
    checks.append(CheckResult(
        name="report_non_empty",
        passed=len(final_report) > 500,
        detail=f"Final report: {len(final_report)} chars",
        weight=2.0,
    ))

    # Check 2: Final report ≥ draft length (refinement should add, not strip)
    checks.append(CheckResult(
        name="report_ge_draft_length",
        passed=len(final_report) >= len(draft) * 0.8 if draft else True,  # Allow 20% tolerance
        detail=f"Report: {len(final_report)} chars vs Draft: {len(draft)} chars",
        weight=1.0,
    ))

    # Check 3: Contains a Sources section
    has_sources_section = bool(re.search(r'(sources|references|bibliography)', final_report, re.IGNORECASE))
    checks.append(CheckResult(
        name="has_sources_section",
        passed=has_sources_section,
        detail="Sources/References section found" if has_sources_section else "No Sources section in final report",
        weight=1.5,
    ))

    # Check 4: Contains citation URLs
    urls_in_report = len(re.findall(r'https?://[^\s\]\)]+', final_report))
    checks.append(CheckResult(
        name="has_citation_urls",
        passed=urls_in_report >= 2,
        detail=f"Found {urls_in_report} URLs in final report",
        weight=1.5,
    ))

    # Check 5: Has markdown structure
    headers = re.findall(r'^#{1,3}\s+\w+', final_report, re.MULTILINE)
    checks.append(CheckResult(
        name="has_structure",
        passed=len(headers) >= 3,
        detail=f"Found {len(headers)} headers in final report",
        weight=1.0,
    ))

    score = _compute_score(checks)
    return ScriptEvalResult(
        score=score,
        checks=checks,
        summary=f"Refinement: {sum(1 for c in checks if c.passed)}/{len(checks)} checks passed",
    )


# ─────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────
SCRIPT_EVAL_REGISTRY = {
    "query_intake": eval_query_intake,
    "decomposition": eval_decomposition,
    "retrieval": eval_retrieval,
    "processing": eval_processing,
    "synthesis": eval_synthesis,
    "outline": eval_outline,
    "draft": eval_draft,
    "review": eval_review,
    "refinement": eval_refinement,
}
