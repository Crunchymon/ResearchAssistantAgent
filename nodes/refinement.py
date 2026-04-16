"""
N9: Final Refinement Node
Polishes the draft into the final report, addressing any review feedback.
Temperature: 0.5 (balanced clarity)
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from state import ResearchState
from config import MODEL_NAME, TEMPERATURES
from prompts.templates import REFINEMENT_PROMPT


def refinement(state: ResearchState) -> dict:
    """Refine the draft into a polished final report."""
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURES["refinement"],
    )

    review_feedback = state.get("review_feedback", {})
    review_feedback_formatted = json.dumps(review_feedback, indent=2)

    prompt = REFINEMENT_PROMPT.format(
        draft=state["draft"],
        review_feedback_formatted=review_feedback_formatted,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    final_report = response.content

    return {
        "final_report": final_report,
        "current_node": "refinement",
        "node_outputs": [{
            "node": "refinement",
            "status": "complete",
            "message": f"Final report ready ({len(final_report)} characters)",
            "data": {"report_length": len(final_report)},
        }],
    }
