"""
LangGraph State Schema for the Agentic AI Research Assistant.

Critical Rule: If it is not in state, it does not exist.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class ResearchState(TypedDict):
    """Central state flowing through the entire LangGraph pipeline.
    
    Provenance guarantee: source URLs flow through
    search_results → processed_data → draft → final_report
    """

    # ─── Input ────────────────────────────────────────────────────
    query: str                          # Original user query

    # ─── N1: Query Intake ─────────────────────────────────────────
    refined_query: str                  # Normalized, unambiguous query

    # ─── N2: Decomposition ────────────────────────────────────────
    sub_questions: list[dict]           # [{id, question, type}]

    # ─── N3: Retrieval ────────────────────────────────────────────
    search_results: dict                # {question_id: [{title, content, url, domain}]}
    retrieval_stats: dict               # {total_searches, total_sources, queries_made}

    # ─── N4: Processing ───────────────────────────────────────────
    processed_data: dict                # {claims, agreements, contradictions, sources_with_scores}

    # ─── N5: Synthesis ────────────────────────────────────────────
    insights: dict                      # {themes, dominant_views, minority_views, conflicts, confidence_levels}

    # ─── N6: Outline ──────────────────────────────────────────────
    outline: dict                       # {title, abstract, sections}

    # ─── N7: Draft ────────────────────────────────────────────────
    draft: str                          # Full markdown draft with citations

    # ─── N8: Review ───────────────────────────────────────────────
    review_feedback: dict               # {passed, gaps, issues, improvements}

    # ─── N9: Refinement ───────────────────────────────────────────
    final_report: str                   # Polished final report

    # ─── Control Flow ─────────────────────────────────────────────
    current_node: str                   # Current node name (for UI tracking)
    retry_count: int                    # Review loop counter

    # ─── UI Logging (append-only) ─────────────────────────────────
    node_outputs: Annotated[list, operator.add]  # [{node, status, message, data}]

    # ─── Eval Results (append-only) ───────────────────────────────
    eval_results: Annotated[list, operator.add]  # [{node, script_score, llm_score, combined_score, ...}]
