"""
N5: Synthesis Node
Combines all processed data into themes, views, conflicts, and confidence levels.
Temperature: 0.5 (balanced)
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from state import ResearchState
from config import MODEL_NAME, TEMPERATURES
from prompts.templates import SYNTHESIS_PROMPT


def synthesis(state: ResearchState) -> dict:
    """Synthesize processed data into coherent insights."""
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURES["synthesis"],
    )

    processed = state["processed_data"]
    prompt = SYNTHESIS_PROMPT.format(
        refined_query=state["refined_query"],
        claims_formatted=json.dumps(processed.get("claims", []), indent=2),
        agreements_formatted=json.dumps(processed.get("agreements", []), indent=2),
        contradictions_formatted=json.dumps(processed.get("contradictions", []), indent=2),
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        result = json.loads(response.content)
        insights = {
            "themes": result.get("themes", []),
            "dominant_views": result.get("dominant_views", []),
            "minority_views": result.get("minority_views", []),
            "conflicts": result.get("conflicts", []),
            "confidence_levels": result.get("confidence_levels", {"overall": "medium", "reasoning": ""}),
        }
    except (json.JSONDecodeError, AttributeError):
        insights = {
            "themes": [],
            "dominant_views": [],
            "minority_views": [],
            "conflicts": [],
            "confidence_levels": {"overall": "medium", "reasoning": "Could not parse synthesis output"},
        }

    return {
        "insights": insights,
        "current_node": "synthesis",
        "node_outputs": [{
            "node": "synthesis",
            "status": "complete",
            "message": (
                f"Identified {len(insights['themes'])} themes, "
                f"{len(insights['dominant_views'])} dominant views, "
                f"{len(insights['conflicts'])} conflicts"
            ),
            "data": insights,
        }],
    }
