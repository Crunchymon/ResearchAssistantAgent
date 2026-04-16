"""
Stage-wise visualization renderers.
Each stage in the pipeline has a dedicated renderer for its output,
plus inline eval score badges and expandable eval detail cards.
"""

from __future__ import annotations

import streamlit as st
from ui.components import (
    render_card,
    render_stats_row,
    render_confidence_meter,
    render_source_card,
    render_contradiction_pair,
    render_section_divider,
    render_eval_badge,
    render_eval_details_card,
)

from config import NODE_NAMES


def _render_stage_header(title: str, eval_result: dict | None = None):
    """Render a stage title with optional inline eval badge."""
    if eval_result:
        score = eval_result.get("combined_score", 0)
        grade = eval_result.get("grade", "?")
        if score >= 0.7:
            color = "#34d399"
            bg = "rgba(16, 185, 129, 0.12)"
            border = "rgba(16, 185, 129, 0.25)"
        elif score >= 0.4:
            color = "#fbbf24"
            bg = "rgba(245, 158, 11, 0.12)"
            border = "rgba(245, 158, 11, 0.25)"
        else:
            color = "#f87171"
            bg = "rgba(239, 68, 68, 0.12)"
            border = "rgba(239, 68, 68, 0.25)"

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.3rem;">
            <span style="font-size:1.17rem;font-weight:600;color:#e2e8f0;">{title}</span>
            <span class="eval-badge" style="background:{bg};color:{color};border:1px solid {border};">
                📊 {grade} · {score:.0%}
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"### {title}")


def render_query_stage(data: dict, eval_result: dict | None = None):
    """Render N1 output: refined query."""
    _render_stage_header("🔍 Query Analysis", eval_result)
    render_card(
        title="Refined Research Query",
        content=data.get("refined_query", "N/A"),
        badge="Complete",
        badge_type="complete",
    )
    reasoning = data.get("reasoning", "")
    if reasoning:
        st.markdown(f"<div style='color:#64748b;font-size:0.82rem;margin-top:-0.5rem;padding-left:1.5rem;'>💡 {reasoning}</div>", unsafe_allow_html=True)
    if eval_result:
        render_eval_details_card(eval_result)
    render_section_divider()


def render_decomposition_stage(data: dict, eval_result: dict | None = None):
    """Render N2 output: sub-question cards."""
    _render_stage_header("🧩 Research Decomposition", eval_result)
    sub_questions = data.get("sub_questions", [])

    cols = st.columns(2)
    for i, sq in enumerate(sub_questions):
        with cols[i % 2]:
            render_card(
                title=sq.get("question", ""),
                content=f"Targeting: {sq.get('type', 'general')} dimension",
                badge=sq.get("type", ""),
                badge_type=sq.get("type", "mechanism"),
            )
    if eval_result:
        render_eval_details_card(eval_result)
    render_section_divider()


def render_retrieval_stage(data: dict, eval_result: dict | None = None):
    """Render N3 output: search results and stats."""
    _render_stage_header("🌐 Autonomous Retrieval", eval_result)

    # Stats row
    stats = data.get("retrieval_stats", {})
    render_stats_row([
        (stats.get("total_searches", 0), "Searches"),
        (stats.get("total_sources", 0), "Sources Found"),
        (len(stats.get("queries_made", [])), "Unique Queries"),
    ])

    # Source cards grouped by sub-question
    search_results = data.get("search_results", {})
    for sq_id, sources in search_results.items():
        if not sources:
            continue
        with st.expander(f"📚 {sq_id.upper()} — {len(sources)} sources", expanded=False):
            for src in sources:
                render_source_card(
                    title=src.get("title", "Untitled"),
                    url=src.get("url", ""),
                    snippet=src.get("content", "")[:200],
                )
    if eval_result:
        render_eval_details_card(eval_result)
    render_section_divider()


def render_processing_stage(data: dict, eval_result: dict | None = None):
    """Render N4 output: claims, agreements, contradictions."""
    _render_stage_header("⚙️ Source Processing", eval_result)

    processed = data
    claims = processed.get("claims", [])
    agreements = processed.get("agreements", [])
    contradictions = processed.get("contradictions", [])
    sources_with_scores = processed.get("sources_with_scores", [])

    # Stats
    render_stats_row([
        (len(claims), "Claims Extracted"),
        (len(agreements), "Agreements Found"),
        (len(contradictions), "Contradictions"),
        (len(sources_with_scores), "Sources Scored"),
    ])

    # Claims
    if claims:
        with st.expander(f"📌 Key Claims ({len(claims)})", expanded=False):
            for claim in claims[:15]:
                st.markdown(f"""
                <div style="padding:0.5rem 0;border-bottom:1px solid rgba(100,116,139,0.1);">
                    <div style="color:#e2e8f0;font-size:0.85rem;">{claim.get('claim', '')}</div>
                    <div style="color:#818cf8;font-size:0.72rem;margin-top:0.2rem;">
                        {claim.get('source_title', '')} · {claim.get('sub_question_id', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Agreements
    if agreements:
        with st.expander(f"🤝 Agreements ({len(agreements)})", expanded=False):
            for ag in agreements:
                strength = ag.get("strength", "moderate")
                color = "#34d399" if strength == "strong" else ("#fbbf24" if strength == "moderate" else "#f87171")
                st.markdown(f"""
                <div class="glass-card" style="border-left: 3px solid {color};">
                    <div class="glass-card-content">{ag.get('claim', '')}</div>
                    <div style="color:{color};font-size:0.72rem;margin-top:0.4rem;font-weight:600;">
                        Strength: {strength.upper()} · {len(ag.get('supporting_sources', []))} supporting sources
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # 🔥 WOW FEATURE: Contradiction Highlights
    if contradictions:
        st.markdown("#### 🔥 Contradiction Analysis")
        for contra in contradictions:
            render_contradiction_pair(
                claim_a=contra.get("claim_a", ""),
                source_a=contra.get("source_a", ""),
                claim_b=contra.get("claim_b", ""),
                source_b=contra.get("source_b", ""),
                nature=contra.get("nature", ""),
            )

    # Source Scores
    if sources_with_scores:
        with st.expander(f"📊 Source Scores ({len(sources_with_scores)})", expanded=False):
            for src in sources_with_scores:
                render_source_card(
                    title=src.get("title", "Unknown"),
                    url=src.get("url", ""),
                    scores={
                        "credibility": src.get("credibility", 0),
                        "recency": src.get("recency", 0),
                        "depth": src.get("depth", 0),
                    },
                )

    if eval_result:
        render_eval_details_card(eval_result)
    render_section_divider()


def render_synthesis_stage(data: dict, eval_result: dict | None = None):
    """Render N5 output: themes, views, conflicts, confidence."""
    _render_stage_header("🧠 Research Synthesis", eval_result)

    insights = data
    themes = insights.get("themes", [])
    dominant_views = insights.get("dominant_views", [])
    minority_views = insights.get("minority_views", [])
    conflicts = insights.get("conflicts", [])
    confidence = insights.get("confidence_levels", {})

    # 🔥 WOW FEATURE: Confidence Meter
    st.markdown("#### Confidence Assessment")
    overall_confidence = confidence.get("overall", "medium")
    render_confidence_meter(overall_confidence, "Overall Research Confidence")
    if confidence.get("reasoning"):
        st.markdown(f"<div style='color:#94a3b8;font-size:0.78rem;margin-top:0.3rem;padding-left:0.5rem;'>{confidence['reasoning']}</div>", unsafe_allow_html=True)

    st.markdown("")

    # Themes
    if themes:
        st.markdown("#### 🎯 Key Themes")
        for theme in themes:
            related = ", ".join(theme.get("related_sub_questions", []))
            render_card(
                title=theme.get("theme", ""),
                content=theme.get("description", ""),
                badge=related,
                badge_type="evidence",
            )

    # Dominant Views
    if dominant_views:
        with st.expander(f"📢 Dominant Views ({len(dominant_views)})", expanded=True):
            for view in dominant_views:
                conf = view.get("confidence", "medium")
                render_confidence_meter(conf, view.get("view", ""))
                st.markdown(f"<div style='color:#94a3b8;font-size:0.8rem;margin:0.3rem 0 1rem 0.5rem;'>{view.get('supporting_evidence', '')}</div>", unsafe_allow_html=True)

    # Minority Views
    if minority_views:
        with st.expander(f"🔇 Minority Views ({len(minority_views)})", expanded=False):
            for view in minority_views:
                render_card(
                    title=view.get("view", ""),
                    content=f"{view.get('supporting_evidence', '')}<br><em style='color:#fbbf24;'>Why important: {view.get('why_important', '')}</em>",
                    badge="Minority",
                    badge_type="contradictions",
                )

    # Conflicts
    if conflicts:
        with st.expander(f"⚔️ Unresolved Conflicts ({len(conflicts)})", expanded=False):
            for conflict in conflicts:
                positions = conflict.get("positions", [])
                positions_text = " vs ".join(positions) if positions else "N/A"
                render_card(
                    title=conflict.get("topic", ""),
                    content=f"<strong>Positions:</strong> {positions_text}<br><em>Status: {conflict.get('resolution_status', 'unknown')}</em>",
                    badge=conflict.get("resolution_status", "unresolved"),
                    badge_type="contradictions" if conflict.get("resolution_status") == "unresolved" else "impact",
                )

    if eval_result:
        render_eval_details_card(eval_result)
    render_section_divider()


def render_outline_stage(data: dict, eval_result: dict | None = None):
    """Render N6 output: report outline."""
    _render_stage_header("📋 Report Outline", eval_result)

    outline = data
    st.markdown(f"<div style='font-size:1.3rem;font-weight:700;color:#e2e8f0;margin-bottom:0.3rem;'>{outline.get('title', '')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#94a3b8;font-size:0.9rem;margin-bottom:1rem;font-style:italic;'>{outline.get('abstract', '')}</div>", unsafe_allow_html=True)

    sections = outline.get("sections", [])
    for i, section in enumerate(sections, 1):
        key_points = section.get("key_points", [])
        points_html = "".join(f"<li>{p}</li>" for p in key_points) if key_points else "<li>TBD</li>"
        render_card(
            title=f"{i}. {section.get('heading', '')}",
            content=f"<em>{section.get('purpose', '')}</em><ul style='margin-top:0.4rem;color:#94a3b8;font-size:0.82rem;'>{points_html}</ul>",
        )

    if eval_result:
        render_eval_details_card(eval_result)
    render_section_divider()


def render_draft_stage(draft: str, eval_result: dict | None = None):
    """Render N7 output: full draft report."""
    _render_stage_header("✍️ Draft Report", eval_result)
    with st.expander("📄 View Full Draft", expanded=True):
        st.markdown(draft)
    if eval_result:
        render_eval_details_card(eval_result)
    render_section_divider()


def render_review_stage(data: dict, eval_result: dict | None = None):
    """Render N8 output: review feedback panel."""
    _render_stage_header("🔎 Quality Review", eval_result)

    passed = data.get("passed", False)
    quality = data.get("overall_quality", "unknown")
    gaps = data.get("gaps", [])
    issues = data.get("issues", [])
    improvements = data.get("improvements", [])

    # Pass/fail indicator
    if passed:
        st.markdown("""
        <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.25);
                    border-radius:12px; padding:1rem; text-align:center; margin-bottom:1rem;">
            <span style="font-size:1.5rem;">✅</span>
            <div style="color:#34d399;font-weight:600;font-size:1rem;margin-top:0.3rem;">Review Passed</div>
            <div style="color:#94a3b8;font-size:0.82rem;">Quality: {quality}</div>
        </div>
        """.format(quality=quality.upper()), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.25);
                    border-radius:12px; padding:1rem; text-align:center; margin-bottom:1rem;">
            <span style="font-size:1.5rem;">⚠️</span>
            <div style="color:#f87171;font-weight:600;font-size:1rem;margin-top:0.3rem;">Review Found Issues</div>
            <div style="color:#94a3b8;font-size:0.82rem;">Quality: {quality} — Triggering re-draft</div>
        </div>
        """.format(quality=quality.upper()), unsafe_allow_html=True)

    # Gaps
    if gaps:
        with st.expander(f"🕳️ Gaps ({len(gaps)})", expanded=not passed):
            for gap in gaps:
                severity = gap.get("severity", "minor")
                color = "#ef4444" if severity == "critical" else ("#fbbf24" if severity == "moderate" else "#94a3b8")
                st.markdown(f"""
                <div style="padding:0.5rem 0;border-bottom:1px solid rgba(100,116,139,0.1);">
                    <span class="badge" style="background:rgba({('239,68,68' if severity == 'critical' else ('245,158,11' if severity == 'moderate' else '100,116,139'))},0.15);color:{color};">{severity}</span>
                    <span style="color:#e2e8f0;font-size:0.85rem;margin-left:0.5rem;">{gap.get('area', '')}: {gap.get('description', '')}</span>
                </div>
                """, unsafe_allow_html=True)

    # Issues
    if issues:
        with st.expander(f"🐛 Issues ({len(issues)})", expanded=not passed):
            for issue in issues:
                st.markdown(f"""
                <div style="padding:0.5rem 0;border-bottom:1px solid rgba(100,116,139,0.1);">
                    <span class="badge badge-contradictions">{issue.get('type', 'unknown')}</span>
                    <span style="color:#e2e8f0;font-size:0.85rem;margin-left:0.5rem;">{issue.get('description', '')}</span>
                </div>
                """, unsafe_allow_html=True)

    # Improvements
    if improvements:
        with st.expander(f"💡 Improvements ({len(improvements)})", expanded=False):
            for imp in improvements:
                st.markdown(f"<div style='color:#94a3b8;font-size:0.85rem;padding:0.3rem 0;'>• {imp}</div>", unsafe_allow_html=True)

    if eval_result:
        render_eval_details_card(eval_result)
    render_section_divider()


def render_final_report(report: str, query: str, eval_result: dict | None = None):
    """Render N9 output: final polished report with download button."""
    _render_stage_header("✨ Final Research Report", eval_result)

    st.markdown("""
    <div style="background:linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
                border:1px solid rgba(102,126,234,0.2); border-radius:16px; padding:1.5rem; margin-bottom:1.5rem;">
        <div style="text-align:center;margin-bottom:0.8rem;">
            <span style="font-size:2rem;">📄</span>
        </div>
        <div style="text-align:center;color:#e2e8f0;font-weight:600;font-size:1.1rem;">
            Research Complete
        </div>
        <div style="text-align:center;color:#94a3b8;font-size:0.85rem;margin-top:0.3rem;">
            Your comprehensive research report is ready.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(report)

    # Download button
    st.download_button(
        label="📥 Download Report (Markdown)",
        data=report,
        file_name=f"research_report_{query[:30].replace(' ', '_')}.md",
        mime="text/markdown",
    )

    if eval_result:
        render_eval_details_card(eval_result)


# ─────────────────────────────────────────────────────────────────
# Eval Summary Dashboard
# ─────────────────────────────────────────────────────────────────

def _score_color(score: float) -> str:
    if score >= 0.7:
        return "#34d399"
    elif score >= 0.4:
        return "#fbbf24"
    return "#f87171"


def _score_bg(score: float) -> str:
    if score >= 0.7:
        return "rgba(16, 185, 129, 0.12)"
    elif score >= 0.4:
        return "rgba(245, 158, 11, 0.12)"
    return "rgba(239, 68, 68, 0.12)"


def render_eval_summary_dashboard(
    eval_data: dict,
    transition_evals: dict,
    aggregate: dict,
):
    """Render the full evaluation summary dashboard after pipeline completion."""
    st.markdown("---")
    st.markdown("### 📊 Pipeline Evaluation Dashboard")

    overall_score = aggregate.get("overall_score", 0)
    overall_grade = aggregate.get("overall_grade", "?")
    overall_color = _score_color(overall_score)

    # ─── Overall Score Hero ──────────────────────────────
    st.markdown(f"""
    <div class="eval-dashboard">
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:3.5rem;font-weight:800;
                        background:linear-gradient(135deg, {overall_color}, {overall_color}cc);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                        background-clip:text;">
                {overall_grade}
            </div>
            <div style="font-size:1.5rem;font-weight:700;color:{overall_color};margin-top:0.2rem;">
                {overall_score:.0%}
            </div>
            <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.3rem;">
                Overall Pipeline Quality Score
            </div>
            <div style="color:#64748b;font-size:0.75rem;margin-top:0.2rem;">
                {aggregate.get('nodes_evaluated', 0)} nodes · {aggregate.get('transitions_evaluated', 0)} transitions evaluated
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── Per-Node Scores Table ───────────────────────────
    st.markdown("#### 🔬 Node-by-Node Scores")

    node_icons = {
        "query_intake": "🔍", "decomposition": "🧩", "retrieval": "🌐",
        "processing": "⚙️", "synthesis": "🧠", "outline": "📋",
        "draft": "✍️", "review": "🔎", "refinement": "✨",
    }

    from config import NODE_ORDER
    for node_key in NODE_ORDER:
        ev = eval_data.get(node_key)
        if not ev:
            continue

        icon = node_icons.get(node_key, "•")
        name = NODE_NAMES.get(node_key, node_key)
        combined = ev.get("combined_score", 0)
        script_s = ev.get("script_score", 0)
        llm_s = ev.get("llm_score", 0)
        grade = ev.get("grade", "?")
        color = _score_color(combined)
        bg = _score_bg(combined)

        st.markdown(f"""
        <div class="eval-node-row">
            <span style="font-size:1rem;">{icon}</span>
            <span class="eval-node-name">{name}</span>
            <div class="eval-node-scores">
                <span class="eval-mini-score" style="background:rgba(100,116,139,0.12);color:#94a3b8;">S: {script_s:.0%}</span>
                <span class="eval-mini-score" style="background:rgba(100,116,139,0.12);color:#94a3b8;">L: {llm_s:.0%}</span>
                <span class="eval-mini-score" style="background:{bg};color:{color};font-size:0.78rem;">{grade} {combined:.0%}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ─── Workflow Transition Scores ──────────────────────
    if transition_evals:
        st.markdown("")
        st.markdown("#### 🔗 Workflow Transition Scores")

        transition_labels = {
            "decomposition_to_retrieval": ("🧩→🌐", "Decomposition → Retrieval"),
            "processing_to_synthesis": ("⚙️→🧠", "Processing → Synthesis"),
            "review_to_refinement": ("🔎→✨", "Review → Refinement"),
        }

        for t_name, t_data in transition_evals.items():
            icons, label = transition_labels.get(t_name, ("→", t_name))
            combined = t_data.get("combined_score", 0)
            color = _score_color(combined)
            bg = _score_bg(combined)

            st.markdown(f"""
            <div class="eval-node-row">
                <span style="font-size:0.9rem;">{icons}</span>
                <span class="eval-node-name">{label}</span>
                <div class="eval-node-scores">
                    <span class="eval-mini-score" style="background:rgba(100,116,139,0.12);color:#94a3b8;">S: {t_data.get('script_score', 0):.0%}</span>
                    <span class="eval-mini-score" style="background:rgba(100,116,139,0.12);color:#94a3b8;">L: {t_data.get('llm_score', 0):.0%}</span>
                    <span class="eval-mini-score" style="background:{bg};color:{color};font-size:0.78rem;">{combined:.0%}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Expandable details
            with st.expander(f"Details: {label}", expanded=False):
                st.markdown(f"""
                <div class="eval-detail-card">
                    <div style="color:#94a3b8;font-size:0.78rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;">Script Checks</div>
                    <div style="color:#cbd5e1;font-size:0.82rem;line-height:1.6;">{t_data.get('script_details', 'N/A')}</div>
                    <div style="margin-top:0.8rem;color:#94a3b8;font-size:0.78rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;">LLM Assessment</div>
                    <div style="color:#cbd5e1;font-size:0.82rem;line-height:1.6;">{t_data.get('llm_reasoning', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)

    render_section_divider()
