"""
N7: Draft Generation Node
Produces a full, evidence-backed research report following the outline.
Temperature: 0.7 (fluent writing)
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from state import ResearchState
from config import MODEL_NAME, TEMPERATURES
from prompts.templates import DRAFT_PROMPT


def draft(state: ResearchState) -> dict:
    """Generate a comprehensive draft report with citations."""
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURES["draft"],
    )

    # Build the review feedback section if this is a retry
    review_feedback_section = ""
    if state.get("review_feedback") and state.get("retry_count", 0) > 0:
        feedback = state["review_feedback"]
        review_feedback_section = "\n**IMPORTANT — Address these issues from the previous review:**\n"
        for gap in feedback.get("gaps", []):
            review_feedback_section += f"- GAP: {gap.get('description', '')} (severity: {gap.get('severity', 'unknown')})\n"
        for issue in feedback.get("issues", []):
            review_feedback_section += f"- ISSUE ({issue.get('type', '')}): {issue.get('description', '')}\n"
        for imp in feedback.get("improvements", []):
            review_feedback_section += f"- IMPROVE: {imp}\n"

    prompt = DRAFT_PROMPT.format(
        outline_formatted=json.dumps(state["outline"], indent=2),
        insights_formatted=json.dumps(state["insights"], indent=2),
        processed_data_formatted=json.dumps(state["processed_data"], indent=2),
        review_feedback_section=review_feedback_section,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    draft_content = response.content

    retry_count = state.get("retry_count", 0)
    is_retry = retry_count > 0

    return {
        "draft": draft_content,
        "current_node": "draft",
        "node_outputs": [{
            "node": "draft",
            "status": "complete",
            "message": f"Draft {'revised' if is_retry else 'generated'} ({len(draft_content)} characters)",
            "data": {"draft_length": len(draft_content), "is_retry": is_retry},
        }],
    }
