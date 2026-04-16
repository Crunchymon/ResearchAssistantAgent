"""
N3: Autonomous Retrieval Agent Node
The core agentic node — uses tool-calling to dynamically search and retrieve sources.
Temperature: 0.7 (balanced exploration)

This node is a sub-agent within the main graph:
- LLM decides which tool to call (search/extract)
- Loop continues until stopping conditions met or max tool calls hit
- Outputs structured search_results grouped by sub-question
"""

from __future__ import annotations

import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from state import ResearchState
from config import MODEL_NAME, TEMPERATURES, MAX_TOOL_CALLS
from prompts.templates import RETRIEVAL_AGENT_PROMPT
from tools.search_tools import RETRIEVAL_TOOLS


def _format_sub_questions(sub_questions: list[dict]) -> str:
    """Format sub-questions for the retrieval agent prompt."""
    lines = []
    for sq in sub_questions:
        lines.append(f"- [{sq['id']}] ({sq['type']}): {sq['question']}")
    return "\n".join(lines)


def retrieval(state: ResearchState) -> dict:
    """Run the autonomous retrieval agent to gather diverse sources."""
    llm = ChatGroq(
        model=MODEL_NAME,
        temperature=TEMPERATURES["retrieval"],
    )

    # Format the retrieval prompt
    sub_questions_formatted = _format_sub_questions(state["sub_questions"])
    prompt = RETRIEVAL_AGENT_PROMPT.format(
        refined_query=state["refined_query"],
        sub_questions_formatted=sub_questions_formatted,
        max_tool_calls=MAX_TOOL_CALLS,
    )

    # Create a ReAct agent with search tools
    agent = create_react_agent(
        model=llm,
        tools=RETRIEVAL_TOOLS,
    )

    # Run the agent
    result = agent.invoke({
        "messages": [HumanMessage(content=prompt)],
    })

    # Extract the final message content
    final_message = result["messages"][-1].content if result.get("messages") else ""

    # Parse results
    search_results, retrieval_stats = _parse_retrieval_output(
        final_message, result.get("messages", [])
    )

    return {
        "search_results": search_results,
        "retrieval_stats": retrieval_stats,
        "current_node": "retrieval",
        "node_outputs": [{
            "node": "retrieval",
            "status": "complete",
            "message": f"Retrieved {retrieval_stats.get('total_sources', 0)} sources across {retrieval_stats.get('total_searches', 0)} searches",
            "data": {
                "search_results": search_results,
                "retrieval_stats": retrieval_stats,
            },
        }],
    }


def _parse_retrieval_output(final_content: str, messages: list) -> tuple[dict, dict]:
    """Parse the retrieval agent's output into structured format.
    
    Falls back to extracting tool call results if JSON parsing fails.
    """
    # Try to parse the agent's final JSON output
    try:
        # Find JSON in the response
        json_start = final_content.find("{")
        json_end = final_content.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            parsed = json.loads(final_content[json_start:json_end])
            search_results = parsed.get("search_results", {})
            retrieval_stats = parsed.get("retrieval_stats", {
                "total_searches": 0,
                "total_sources": 0,
                "queries_made": [],
            })
            return search_results, retrieval_stats
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: extract results from tool call messages
    search_results = {"sq1": [], "sq2": [], "sq3": [], "sq4": []}
    queries_made = []
    total_searches = 0

    for msg in messages:
        # Check for tool messages (results from tool calls)
        if hasattr(msg, "type") and msg.type == "tool":
            try:
                content = msg.content
                if isinstance(content, str):
                    content = json.loads(content)
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "url" in item:
                            # Assign to first available sub-question bucket
                            for sq_id in search_results:
                                if len(search_results[sq_id]) < 5:
                                    search_results[sq_id].append({
                                        "title": item.get("title", "Untitled"),
                                        "content": item.get("content", ""),
                                        "url": item.get("url", ""),
                                        "domain": item.get("domain", "unknown"),
                                    })
                                    break
                    total_searches += 1
            except (json.JSONDecodeError, TypeError):
                continue

        # Track queries from AI messages with tool calls
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "tavily_search":
                    q = tc.get("args", {}).get("query", "")
                    if q:
                        queries_made.append(q)

    total_sources = sum(len(v) for v in search_results.values())
    retrieval_stats = {
        "total_searches": total_searches,
        "total_sources": total_sources,
        "queries_made": queries_made,
    }

    return search_results, retrieval_stats
