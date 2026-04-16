"""
N4: Source Processing Node
Summarizes sources, extracts claims, detects agreements/contradictions, scores sources.
Temperature: 0.4 (high accuracy)
"""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from state import ResearchState
from config import MODEL_NAME, TEMPERATURES
from prompts.templates import PROCESSING_PROMPT


def _format_search_results(search_results: dict) -> str:
    """Format search results for the processing prompt."""
    sections = []
    for sq_id, sources in search_results.items():
        if not sources:
            continue
        section = f"\n### Sub-question: {sq_id}\n"
        for i, src in enumerate(sources, 1):
            section += f"\n**Source {i}:** {src.get('title', 'Untitled')}\n"
            section += f"- URL: {src.get('url', 'N/A')}\n"
            section += f"- Domain: {src.get('domain', 'unknown')}\n"
            content = src.get("content", "")
            # Truncate very long content
            if len(content) > 2000:
                content = content[:2000] + "..."
            section += f"- Content: {content}\n"
        sections.append(section)
    return "\n".join(sections)


def processing(state: ResearchState) -> dict:
    """Process search results: extract claims, detect patterns, score sources."""
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURES["processing"],
    )

    search_results_formatted = _format_search_results(state["search_results"])
    prompt = PROCESSING_PROMPT.format(
        refined_query=state["refined_query"],
        search_results_formatted=search_results_formatted,
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        result = json.loads(response.content)
        processed_data = {
            "claims": result.get("claims", []),
            "agreements": result.get("agreements", []),
            "contradictions": result.get("contradictions", []),
            "sources_with_scores": result.get("sources_with_scores", []),
        }
    except (json.JSONDecodeError, AttributeError):
        processed_data = {
            "claims": [],
            "agreements": [],
            "contradictions": [],
            "sources_with_scores": [],
        }

    return {
        "processed_data": processed_data,
        "current_node": "processing",
        "node_outputs": [{
            "node": "processing",
            "status": "complete",
            "message": (
                f"Extracted {len(processed_data['claims'])} claims, "
                f"found {len(processed_data['agreements'])} agreements, "
                f"{len(processed_data['contradictions'])} contradictions"
            ),
            "data": processed_data,
        }],
    }
