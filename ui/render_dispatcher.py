"""Render completed research stages in a single place."""

from __future__ import annotations

from ui.stages import (
    render_decomposition_stage,
    render_draft_stage,
    render_eval_summary_dashboard,
    render_final_report,
    render_outline_stage,
    render_processing_stage,
    render_query_stage,
    render_retrieval_stage,
    render_review_stage,
    render_synthesis_stage,
)


def render_completed_results(
    node_data: dict,
    eval_data: dict,
    research_complete: bool,
    transition_evals: dict,
    aggregate_eval: dict,
    research_query: str = "research",
):
    """Render all completed stages and the evaluation dashboard."""
    stage_renderers = [
        ("query_intake", render_query_stage),
        ("decomposition", render_decomposition_stage),
        ("retrieval", render_retrieval_stage),
        ("processing", render_processing_stage),
        ("synthesis", render_synthesis_stage),
        ("outline", render_outline_stage),
        ("draft", render_draft_stage),
        ("review", render_review_stage),
    ]

    for stage_name, renderer in stage_renderers:
        if stage_name in node_data:
            renderer(node_data[stage_name], eval_data.get(stage_name))

    if "final_report" in node_data:
        render_final_report(
            node_data["final_report"],
            research_query,
            eval_data.get("refinement"),
        )

    if research_complete and eval_data:
        render_eval_summary_dashboard(
            eval_data=eval_data,
            transition_evals=transition_evals,
            aggregate=aggregate_eval,
        )
