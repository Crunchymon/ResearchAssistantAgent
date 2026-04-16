"""
N1: Query Intake Node
Normalizes the raw user query into a clear, research-ready form.
Temperature: 0.3 (low creativity, high precision)
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from state import ResearchState
from config import MODEL_NAME, TEMPERATURES
from prompts.templates import QUERY_INTAKE_PROMPT


def query_intake(state: ResearchState) -> dict:
    """Normalize and refine the user's raw query."""
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURES["query_intake"],
    )

    prompt = QUERY_INTAKE_PROMPT.format(query=state["query"])
    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        result = json.loads(response.content)
        refined_query = result.get("refined_query", state["query"])
        reasoning = result.get("reasoning", "")
    except (json.JSONDecodeError, AttributeError):
        # Fallback: use the raw response as refined query
        refined_query = response.content.strip()
        reasoning = "Direct refinement"

    return {
        "refined_query": refined_query,
        "current_node": "query_intake",
        "node_outputs": [{
            "node": "query_intake",
            "status": "complete",
            "message": f"Query refined: {refined_query}",
            "data": {"refined_query": refined_query, "reasoning": reasoning},
        }],
    }
