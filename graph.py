"""
LangGraph Pipeline Builder.
Wires all 9 nodes with edges and the conditional review loop.
Injects hybrid evaluations after each node completes.

Graph flow:
  N1 → N2 → N3 → N4 → N5 → N6 → N7 → N8 → [conditional] → N9
                                                 ↓ (if issues & retry < 1)
                                                 N7 (re-draft)
"""

from langgraph.graph import StateGraph, END

from state import ResearchState
from config import MAX_REVIEW_RETRIES

from nodes.query_intake import query_intake
from nodes.decomposition import decomposition
from nodes.retrieval import retrieval
from nodes.processing import processing
from nodes.synthesis import synthesis
from nodes.outline import outline
from nodes.draft import draft
from nodes.review import review
from nodes.refinement import refinement

from evals.evaluator import PipelineEvaluator

# Single evaluator instance shared across the pipeline run
_evaluator = None


def get_evaluator() -> PipelineEvaluator:
    """Get or create the pipeline evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = PipelineEvaluator()
    return _evaluator


def reset_evaluator():
    """Reset the evaluator for a new pipeline run."""
    global _evaluator
    _evaluator = PipelineEvaluator()


def _make_eval_wrapper(node_fn, node_name: str):
    """Wrap a node function to run evals after it completes.

    The wrapper:
    1. Captures the input state before the node runs
    2. Runs the node function
    3. Runs hybrid evaluation (script + LLM)
    4. Appends eval results to the state
    """
    def wrapped(state: ResearchState) -> dict:
        # Snapshot input state for eval
        input_snapshot = dict(state)

        # Run the actual node
        output = node_fn(state)

        # Run evaluation
        evaluator = get_evaluator()
        try:
            eval_result = evaluator.evaluate_node(node_name, input_snapshot, output)
            # Append eval result to state
            output["eval_results"] = [eval_result.to_dict()]
        except Exception as e:
            # Don't let eval failures break the pipeline
            output["eval_results"] = [{
                "node": node_name,
                "script_score": 0.0,
                "llm_score": 0.0,
                "combined_score": 0.0,
                "grade": "?",
                "status": "error",
                "eval_time_ms": 0,
                "error": str(e),
                "script_checks": [],
                "script_summary": "",
                "llm_reasoning": f"Eval error: {e}",
                "llm_raw_score": 0,
                "llm_strengths": [],
                "llm_weaknesses": [],
                "llm_error": str(e),
            }]

        return output

    # Preserve the original function name for debugging
    wrapped.__name__ = node_fn.__name__
    wrapped.__qualname__ = node_fn.__qualname__
    return wrapped


def _review_router(state: ResearchState) -> str:
    """Conditional edge after review node.

    Routes to:
    - 'draft' if review failed AND retry_count < MAX_REVIEW_RETRIES
    - 'refinement' otherwise (passed or max retries reached)
    """
    feedback = state.get("review_feedback", {})
    passed = feedback.get("passed", True)
    retry_count = state.get("retry_count", 0)

    if not passed and retry_count < MAX_REVIEW_RETRIES:
        return "draft"
    return "refinement"


def _increment_retry(state: ResearchState) -> dict:
    """Wrapper node that increments retry count before re-drafting."""
    return {
        "retry_count": state.get("retry_count", 0) + 1,
        "node_outputs": [{
            "node": "review",
            "status": "retry",
            "message": f"Review found issues — re-drafting (attempt {state.get('retry_count', 0) + 2})",
            "data": {},
        }],
        "eval_results": [],  # No eval for increment_retry
    }


def build_graph():
    """Build and compile the research pipeline graph with inline evals."""
    workflow = StateGraph(ResearchState)

    # ─── Add Nodes (wrapped with eval) ────────────────────
    workflow.add_node("query_intake", _make_eval_wrapper(query_intake, "query_intake"))
    workflow.add_node("decomposition", _make_eval_wrapper(decomposition, "decomposition"))
    workflow.add_node("retrieval", _make_eval_wrapper(retrieval, "retrieval"))
    workflow.add_node("processing", _make_eval_wrapper(processing, "processing"))
    workflow.add_node("synthesis", _make_eval_wrapper(synthesis, "synthesis"))
    workflow.add_node("outline", _make_eval_wrapper(outline, "outline"))
    workflow.add_node("draft", _make_eval_wrapper(draft, "draft"))
    workflow.add_node("review", _make_eval_wrapper(review, "review"))
    workflow.add_node("increment_retry", _increment_retry)
    workflow.add_node("refinement", _make_eval_wrapper(refinement, "refinement"))

    # ─── Add Edges ────────────────────────────────────────
    workflow.set_entry_point("query_intake")

    workflow.add_edge("query_intake", "decomposition")
    workflow.add_edge("decomposition", "retrieval")
    workflow.add_edge("retrieval", "processing")
    workflow.add_edge("processing", "synthesis")
    workflow.add_edge("synthesis", "outline")
    workflow.add_edge("outline", "draft")
    workflow.add_edge("draft", "review")

    # Conditional edge: review → refinement OR review → retry → draft
    workflow.add_conditional_edges(
        "review",
        _review_router,
        {
            "draft": "increment_retry",
            "refinement": "refinement",
        },
    )
    workflow.add_edge("increment_retry", "draft")

    workflow.add_edge("refinement", END)

    return workflow.compile()


# Pre-compiled graph instance
research_graph = build_graph()
