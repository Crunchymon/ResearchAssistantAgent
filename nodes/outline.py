"""
N6: Outline Node
Generates a structured report outline with title, abstract, and sections.
Temperature: 0.5 (balanced)
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from state import ResearchState
from config import MODEL_NAME, TEMPERATURES
from prompts.templates import OUTLINE_PROMPT


def outline(state: ResearchState) -> dict:
    """Generate a structured outline for the research report."""
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURES["outline"],
    )

    insights = state["insights"]
    prompt = OUTLINE_PROMPT.format(
        refined_query=state["refined_query"],
        themes_formatted=json.dumps(insights.get("themes", []), indent=2),
        dominant_views_formatted=json.dumps(insights.get("dominant_views", []), indent=2),
        conflicts_formatted=json.dumps(insights.get("conflicts", []), indent=2),
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        result = json.loads(response.content)
        outline_data = {
            "title": result.get("title", "Research Report"),
            "abstract": result.get("abstract", ""),
            "sections": result.get("sections", []),
        }
    except (json.JSONDecodeError, AttributeError):
        outline_data = {
            "title": f"Research Report: {state['refined_query']}",
            "abstract": "A comprehensive analysis based on multi-source research.",
            "sections": [
                {"heading": "Introduction", "purpose": "Set the context", "key_points": [], "maps_to_themes": []},
                {"heading": "Findings", "purpose": "Present key findings", "key_points": [], "maps_to_themes": []},
                {"heading": "Discussion", "purpose": "Analyze implications", "key_points": [], "maps_to_themes": []},
                {"heading": "Conclusion", "purpose": "Summarize insights", "key_points": [], "maps_to_themes": []},
            ],
        }

    return {
        "outline": outline_data,
        "current_node": "outline",
        "node_outputs": [{
            "node": "outline",
            "status": "complete",
            "message": f"Outline created: '{outline_data['title']}' with {len(outline_data['sections'])} sections",
            "data": outline_data,
        }],
    }
