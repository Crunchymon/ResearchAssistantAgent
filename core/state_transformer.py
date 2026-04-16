"""Helpers for shaping graph output into UI-friendly state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NodeEvent:
    """Normalized output for a single streamed graph node."""

    node_name: str
    raw_data: Any
    stage_updates: dict[str, Any] = field(default_factory=dict)
    eval_result: dict | None = None
    retry_triggered: bool = False


def build_initial_state(query: str) -> dict:
    """Create the baseline state that the graph expects."""
    return {
        "query": query,
        "refined_query": "",
        "sub_questions": [],
        "search_results": {},
        "retrieval_stats": {},
        "processed_data": {},
        "insights": {},
        "outline": {},
        "draft": "",
        "review_feedback": {},
        "final_report": "",
        "current_node": "",
        "retry_count": 0,
        "node_outputs": [],
        "eval_results": [],
    }


def _extract_latest_node_data(node_output: dict) -> Any:
    node_outputs = node_output.get("node_outputs", [])
    if node_outputs:
        latest = node_outputs[-1] if isinstance(node_outputs, list) else node_outputs
        if isinstance(latest, dict):
            return latest.get("data", node_output)
    return node_output


def _extract_latest_eval(node_output: dict) -> dict | None:
    eval_results = node_output.get("eval_results", [])
    if not eval_results:
        return None
    latest_eval = eval_results[-1] if isinstance(eval_results, list) else eval_results
    return latest_eval if isinstance(latest_eval, dict) else None


def _build_stage_updates(node_output: dict) -> dict[str, Any]:
    stage_updates: dict[str, Any] = {}

    if node_output.get("refined_query"):
        stage_updates["query_intake"] = {
            "refined_query": node_output["refined_query"],
        }
    if node_output.get("sub_questions"):
        stage_updates["decomposition"] = {
            "sub_questions": node_output["sub_questions"],
        }
    if "search_results" in node_output:
        stage_updates["retrieval"] = {
            "search_results": node_output.get("search_results", {}),
            "retrieval_stats": node_output.get("retrieval_stats", {}),
        }
    if "processed_data" in node_output:
        stage_updates["processing"] = node_output["processed_data"]
    if "insights" in node_output:
        stage_updates["synthesis"] = node_output["insights"]
    if node_output.get("outline"):
        stage_updates["outline"] = node_output["outline"]
    if node_output.get("draft"):
        stage_updates["draft"] = node_output["draft"]
    if "review_feedback" in node_output:
        stage_updates["review"] = node_output["review_feedback"]
    if node_output.get("final_report"):
        stage_updates["final_report"] = node_output["final_report"]

    return stage_updates


def normalize_node_event(node_name: str, node_output: Any) -> NodeEvent:
    """Convert raw graph updates into a predictable shape."""
    if node_name == "increment_retry":
        return NodeEvent(node_name="increment_retry", raw_data={}, retry_triggered=True)

    if not isinstance(node_output, dict):
        return NodeEvent(node_name=node_name, raw_data=node_output)

    return NodeEvent(
        node_name=node_name,
        raw_data=_extract_latest_node_data(node_output),
        stage_updates=_build_stage_updates(node_output),
        eval_result=_extract_latest_eval(node_output),
    )


def build_transition_state(initial_state: dict, completed_nodes: list[str], node_data: dict) -> dict:
    """Reconstruct accumulated state for transition evaluations."""
    accumulated_state = dict(initial_state)

    for node_name in completed_nodes:
        data = node_data.get(node_name, {})
        if isinstance(data, dict):
            accumulated_state.update(data)

    if "query_intake" in node_data:
        accumulated_state["refined_query"] = node_data["query_intake"].get("refined_query", "")
    if "decomposition" in node_data:
        accumulated_state["sub_questions"] = node_data["decomposition"].get("sub_questions", [])
    if "retrieval" in node_data:
        accumulated_state["search_results"] = node_data["retrieval"].get("search_results", {})
        accumulated_state["retrieval_stats"] = node_data["retrieval"].get("retrieval_stats", {})
    if "processing" in node_data:
        processed = node_data["processing"]
        accumulated_state["processed_data"] = processed if isinstance(processed, dict) else {}
    if "synthesis" in node_data:
        insights = node_data["synthesis"]
        accumulated_state["insights"] = insights if isinstance(insights, dict) else {}
    if "review" in node_data:
        review = node_data["review"]
        accumulated_state["review_feedback"] = review if isinstance(review, dict) else {}
    if "draft" in node_data:
        accumulated_state["draft"] = node_data["draft"]
    if "final_report" in node_data:
        accumulated_state["final_report"] = node_data["final_report"]

    return accumulated_state
