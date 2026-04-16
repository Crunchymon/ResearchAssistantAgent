"""
Centralized configuration for the evaluation framework.
"""

# ─── Score Blending ──────────────────────────────────────────────
# Final score = SCRIPT_WEIGHT * script_score + LLM_WEIGHT * llm_score
SCRIPT_WEIGHT = 0.4
LLM_WEIGHT = 0.6

# ─── LLM Eval Settings ──────────────────────────────────────────
EVAL_LLM_TEMPERATURE = 0.1   # Very low — strict, consistent grading
EVAL_MODEL_NAME = "llama-3.3-70b-versatile"

# ─── Score Thresholds ────────────────────────────────────────────
SCORE_PASS = 0.7    # ≥ 0.7 = PASS  (green)
SCORE_WARN = 0.4    # ≥ 0.4 = WARN  (yellow)
                     # < 0.4 = FAIL  (red)

# ─── Workflow Transition Tests ───────────────────────────────────
WORKFLOW_TRANSITIONS = [
    {
        "name": "decomposition_to_retrieval",
        "from_node": "decomposition",
        "to_node": "retrieval",
        "description": "Verify sub-question IDs are covered in search results",
    },
    {
        "name": "processing_to_synthesis",
        "from_node": "processing",
        "to_node": "synthesis",
        "description": "Verify claims propagate into synthesis themes",
    },
    {
        "name": "review_to_refinement",
        "from_node": "review",
        "to_node": "refinement",
        "description": "Verify review feedback is addressed in final report",
    },
]

# ─── Human-Readable Grade Labels ────────────────────────────────
def score_to_grade(score: float) -> str:
    """Convert a 0.0-1.0 score to a letter grade."""
    if score >= 0.9:
        return "A+"
    elif score >= 0.8:
        return "A"
    elif score >= 0.7:
        return "B"
    elif score >= 0.6:
        return "C"
    elif score >= 0.4:
        return "D"
    else:
        return "F"


def score_to_status(score: float) -> str:
    """Convert a 0.0-1.0 score to pass/warn/fail status."""
    if score >= SCORE_PASS:
        return "pass"
    elif score >= SCORE_WARN:
        return "warn"
    return "fail"
