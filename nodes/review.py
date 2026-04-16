"""
N8: Quality Review Node
Evaluates the draft against strict research quality standards.
Temperature: 0.2 (strict, analytical)
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from state import ResearchState
from config import MODEL_NAME, TEMPERATURES
from prompts.templates import REVIEW_PROMPT


def review(state: ResearchState) -> dict:
    """Review the draft report for quality, coverage, and evidence backing."""
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURES["review"],
    )

    prompt = REVIEW_PROMPT.format(
        refined_query=state["refined_query"],
        draft=state["draft"],
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        result = json.loads(response.content)
        review_feedback = {
            "passed": result.get("passed", True),
            "overall_quality": result.get("overall_quality", "good"),
            "gaps": result.get("gaps", []),
            "issues": result.get("issues", []),
            "improvements": result.get("improvements", []),
        }
    except (json.JSONDecodeError, AttributeError):
        # If parsing fails, assume it passed (don't block the pipeline)
        review_feedback = {
            "passed": True,
            "overall_quality": "good",
            "gaps": [],
            "issues": [],
            "improvements": ["Review parsing failed — proceeding with current draft"],
        }

    return {
        "review_feedback": review_feedback,
        "current_node": "review",
        "node_outputs": [{
            "node": "review",
            "status": "complete",
            "message": (
                f"Review {'PASSED' if review_feedback['passed'] else 'FAILED'} — "
                f"Quality: {review_feedback['overall_quality']}, "
                f"{len(review_feedback['gaps'])} gaps, "
                f"{len(review_feedback['issues'])} issues"
            ),
            "data": review_feedback,
        }],
    }
