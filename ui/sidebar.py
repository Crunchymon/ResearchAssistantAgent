"""
Pipeline Tracker Sidebar.
Shows real-time progress through the 9-node research pipeline,
with inline eval scores per node.
"""

from __future__ import annotations

import streamlit as st

from config import NODE_NAMES, NODE_ORDER


# Icons for each node
NODE_ICONS = {
    "query_intake": "🔍",
    "decomposition": "🧩",
    "retrieval": "🌐",
    "processing": "⚙️",
    "synthesis": "🧠",
    "outline": "📋",
    "draft": "✍️",
    "review": "🔎",
    "refinement": "✨",
}

# Status icons
STATUS_ICONS = {
    "pending": "○",
    "running": "◉",
    "complete": "✓",
    "error": "✕",
    "retry": "↻",
}


def _eval_score_html(eval_result: dict | None) -> str:
    """Generate inline HTML for an eval score badge in the sidebar."""
    if not eval_result:
        return ""

    score = eval_result.get("combined_score", 0)
    grade = eval_result.get("grade", "?")

    if score >= 0.7:
        color = "#34d399"
        bg = "rgba(16, 185, 129, 0.15)"
    elif score >= 0.4:
        color = "#fbbf24"
        bg = "rgba(245, 158, 11, 0.15)"
    else:
        color = "#f87171"
        bg = "rgba(239, 68, 68, 0.15)"

    return f'<span class="sidebar-eval-score" style="background:{bg};color:{color};">{grade} {score:.0%}</span>'


def render_pipeline_tracker(
    completed_nodes: list[str],
    current_node: str,
    retry_triggered: bool = False,
    eval_data: dict | None = None,
):
    """Render the pipeline progress tracker in the sidebar with eval scores."""
    if eval_data is None:
        eval_data = {}

    st.sidebar.markdown("""
    <div style="padding: 0.5rem 0;">
        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;
                    letter-spacing: 1px; font-weight: 600; margin-bottom: 1rem;">
            Pipeline Progress
        </div>
    </div>
    """, unsafe_allow_html=True)

    for node_key in NODE_ORDER:
        node_name = NODE_NAMES[node_key]
        icon = NODE_ICONS.get(node_key, "•")

        # Determine status
        if node_key in completed_nodes:
            status = "complete"
            status_icon = STATUS_ICONS["complete"]
        elif node_key == current_node:
            status = "running"
            status_icon = STATUS_ICONS["running"]
        else:
            status = "pending"
            status_icon = STATUS_ICONS["pending"]

        # Special case: review node with retry
        if node_key == "review" and retry_triggered and node_key in completed_nodes:
            status = "complete"  # still complete but with retry note

        # Get eval score HTML
        eval_html = _eval_score_html(eval_data.get(node_key))

        st.sidebar.markdown(f"""
        <div class="pipeline-step pipeline-step-{status}" style="display:flex;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <div class="step-icon step-icon-{status}">{status_icon}</div>
                <span>{icon} {node_name}</span>
            </div>
            {eval_html}
        </div>
        """, unsafe_allow_html=True)

    # Show retry indicator
    if retry_triggered:
        st.sidebar.markdown("""
        <div style="margin-top: 0.8rem; padding: 0.6rem 0.9rem; background: rgba(245, 158, 11, 0.1);
                    border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px;
                    font-size: 0.78rem; color: #fbbf24;">
            ↻ Review triggered re-draft
        </div>
        """, unsafe_allow_html=True)

    # ─── Aggregate Score in Sidebar ──────────────────────
    if eval_data:
        scores = [v.get("combined_score", 0) for v in eval_data.values() if isinstance(v, dict)]
        if scores:
            avg_score = sum(scores) / len(scores)
            if avg_score >= 0.7:
                color = "#34d399"
                bg = "rgba(16, 185, 129, 0.1)"
                border = "rgba(16, 185, 129, 0.2)"
            elif avg_score >= 0.4:
                color = "#fbbf24"
                bg = "rgba(245, 158, 11, 0.1)"
                border = "rgba(245, 158, 11, 0.2)"
            else:
                color = "#f87171"
                bg = "rgba(239, 68, 68, 0.1)"
                border = "rgba(239, 68, 68, 0.2)"

            st.sidebar.markdown(f"""
            <div style="margin-top:1rem;padding:0.8rem;background:{bg};
                        border:1px solid {border};border-radius:10px;text-align:center;">
                <div style="font-size:1.6rem;font-weight:800;color:{color};">{avg_score:.0%}</div>
                <div style="font-size:0.68rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;margin-top:0.2rem;">
                    Pipeline Quality Score
                </div>
                <div style="font-size:0.65rem;color:#64748b;margin-top:0.15rem;">
                    {len(scores)} nodes evaluated
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_sidebar_header():
    """Render the sidebar header with branding."""
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0 1.5rem 0;">
        <div style="font-size: 1.5rem; font-weight: 800;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    background-clip: text; margin-bottom: 0.3rem;">
            🔬 Research AI
        </div>
        <div style="font-size: 0.75rem; color: #64748b;">
            Agentic Research Pipeline
        </div>
    </div>
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)


def render_sidebar_stats(retrieval_stats: dict = None):
    """Render retrieval stats in the sidebar."""
    if not retrieval_stats:
        return

    st.sidebar.markdown("""
    <div style="margin-top: 1rem;">
        <div style="font-size: 0.75rem; color: #64748b; text-transform: uppercase;
                    letter-spacing: 1px; font-weight: 600; margin-bottom: 0.8rem;">
            Retrieval Activity
        </div>
    </div>
    """, unsafe_allow_html=True)

    total_searches = retrieval_stats.get("total_searches", 0)
    total_sources = retrieval_stats.get("total_sources", 0)
    queries = retrieval_stats.get("queries_made", [])

    st.sidebar.markdown(f"""
    <div style="display: flex; gap: 0.5rem; margin-bottom: 0.8rem;">
        <div style="flex: 1; text-align: center; background: rgba(30, 34, 56, 0.6);
                    border: 1px solid rgba(102, 126, 234, 0.15); border-radius: 10px; padding: 0.7rem;">
            <div style="font-size: 1.4rem; font-weight: 700; color: #818cf8;">{total_searches}</div>
            <div style="font-size: 0.68rem; color: #64748b; text-transform: uppercase;">Searches</div>
        </div>
        <div style="flex: 1; text-align: center; background: rgba(30, 34, 56, 0.6);
                    border: 1px solid rgba(102, 126, 234, 0.15); border-radius: 10px; padding: 0.7rem;">
            <div style="font-size: 1.4rem; font-weight: 700; color: #34d399;">{total_sources}</div>
            <div style="font-size: 0.68rem; color: #64748b; text-transform: uppercase;">Sources</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if queries:
        with st.sidebar.expander("🔗 Queries Made", expanded=False):
            for i, q in enumerate(queries[:10], 1):
                st.markdown(f"<div style='font-size:0.78rem;color:#94a3b8;padding:0.2rem 0;'>{i}. {q}</div>", unsafe_allow_html=True)
