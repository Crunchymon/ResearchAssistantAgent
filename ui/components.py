"""
Reusable UI components for the Streamlit app.
Glassmorphism cards, confidence meters, source cards, contradiction pairs.
"""

from __future__ import annotations

import streamlit as st


def inject_custom_css():
    """Inject premium CSS styling with dark theme and glassmorphism."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ─── Global Theme ──────────────────────────────────── */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ─── Hero Title ────────────────────────────────────── */
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }

    .hero-subtitle {
        font-size: 1rem;
        color: #94a3b8;
        font-weight: 400;
        margin-bottom: 2rem;
    }

    /* ─── Glass Card ────────────────────────────────────── */
    .glass-card {
        background: rgba(30, 34, 56, 0.65);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(102, 126, 234, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
    }

    .glass-card:hover {
        border-color: rgba(102, 126, 234, 0.35);
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.1);
        transform: translateY(-2px);
    }

    .glass-card-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.6rem;
    }

    .glass-card-content {
        font-size: 0.9rem;
        color: #94a3b8;
        line-height: 1.6;
    }

    /* ─── Badge ─────────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .badge-mechanism { background: rgba(99, 102, 241, 0.2); color: #818cf8; }
    .badge-impact { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .badge-evidence { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .badge-contradictions { background: rgba(239, 68, 68, 0.2); color: #f87171; }
    .badge-complete { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .badge-running { background: rgba(99, 102, 241, 0.2); color: #818cf8; }
    .badge-pending { background: rgba(100, 116, 139, 0.2); color: #94a3b8; }
    .badge-retry { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }

    /* ─── Pipeline Tracker ──────────────────────────────── */
    .pipeline-step {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.65rem 0.9rem;
        margin-bottom: 0.35rem;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .pipeline-step-pending {
        color: #64748b;
        background: transparent;
    }

    .pipeline-step-running {
        color: #818cf8;
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.25);
        animation: pulse-glow 2s ease-in-out infinite;
    }

    .pipeline-step-complete {
        color: #34d399;
        background: rgba(16, 185, 129, 0.08);
    }

    .pipeline-step-error {
        color: #f87171;
        background: rgba(239, 68, 68, 0.08);
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
        50% { box-shadow: 0 0 12px 2px rgba(99, 102, 241, 0.2); }
    }

    /* ─── Step Icon ─────────────────────────────────────── */
    .step-icon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        flex-shrink: 0;
    }

    .step-icon-pending { background: rgba(100, 116, 139, 0.2); color: #64748b; }
    .step-icon-running { background: rgba(99, 102, 241, 0.3); color: #818cf8; }
    .step-icon-complete { background: rgba(16, 185, 129, 0.3); color: #34d399; }

    /* ─── Confidence Meter ──────────────────────────────── */
    .confidence-meter {
        height: 8px;
        border-radius: 4px;
        background: rgba(100, 116, 139, 0.2);
        overflow: hidden;
        margin-top: 0.3rem;
    }

    .confidence-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .confidence-high { background: linear-gradient(90deg, #34d399, #10b981); width: 90%; }
    .confidence-medium { background: linear-gradient(90deg, #fbbf24, #f59e0b); width: 60%; }
    .confidence-low { background: linear-gradient(90deg, #f87171, #ef4444); width: 30%; }

    /* ─── Contradiction Panel ───────────────────────────── */
    .contradiction-pair {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        gap: 1rem;
        align-items: stretch;
        margin-bottom: 1rem;
    }

    .claim-card-agree {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 12px;
        padding: 1rem;
    }

    .claim-card-disagree {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-radius: 12px;
        padding: 1rem;
    }

    .vs-divider {
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: #64748b;
        font-size: 0.85rem;
    }

    /* ─── Source Card ────────────────────────────────────── */
    .source-card {
        background: rgba(30, 34, 56, 0.5);
        border: 1px solid rgba(100, 116, 139, 0.15);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        transition: all 0.25s ease;
    }

    .source-card:hover {
        border-color: rgba(102, 126, 234, 0.3);
    }

    .source-title {
        font-weight: 600;
        color: #e2e8f0;
        font-size: 0.9rem;
        margin-bottom: 0.3rem;
    }

    .source-url {
        color: #818cf8;
        font-size: 0.78rem;
        text-decoration: none;
        word-break: break-all;
    }

    .source-snippet {
        color: #94a3b8;
        font-size: 0.82rem;
        margin-top: 0.4rem;
        line-height: 1.5;
    }

    .source-score {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }

    .score-high { background: rgba(16, 185, 129, 0.15); color: #34d399; }
    .score-mid { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
    .score-low { background: rgba(239, 68, 68, 0.15); color: #f87171; }

    /* ─── Stats Counter ─────────────────────────────────── */
    .stats-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }

    .stat-box {
        background: rgba(30, 34, 56, 0.6);
        border: 1px solid rgba(102, 126, 234, 0.15);
        border-radius: 12px;
        padding: 0.9rem 1.2rem;
        flex: 1;
        min-width: 120px;
        text-align: center;
    }

    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .stat-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.2rem;
    }

    /* ─── Divider ───────────────────────────────────────── */
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
        margin: 1.5rem 0;
    }

    /* ─── Input Styling ─────────────────────────────────── */
    .stTextInput > div > div > input {
        background: rgba(30, 34, 56, 0.6) !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.8rem 1rem !important;
        font-size: 0.95rem !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: rgba(102, 126, 234, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.15) !important;
    }

    /* ─── Button Styling ────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.7rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.3px !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3) !important;
    }

    /* ─── Expander Styling ──────────────────────────────── */
    .streamlit-expanderHeader {
        background: rgba(30, 34, 56, 0.5) !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }

    /* ─── Eval Score Ring ───────────────────────────────── */
    .eval-score-ring {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        flex-shrink: 0;
    }

    .eval-score-ring svg {
        transform: rotate(-90deg);
    }

    .eval-score-ring .score-text {
        position: absolute;
        font-size: 0.72rem;
        font-weight: 700;
        color: #e2e8f0;
    }

    .eval-score-ring .grade-text {
        position: absolute;
        bottom: -2px;
        font-size: 0.55rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* ─── Eval Badge (inline) ──────────────────────────── */
    .eval-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.25rem 0.65rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        vertical-align: middle;
        margin-left: 0.5rem;
    }

    .eval-badge-pass {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.25);
    }

    .eval-badge-warn {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.25);
    }

    .eval-badge-fail {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.25);
    }

    /* ─── Eval Detail Card ─────────────────────────────── */
    .eval-detail-card {
        background: rgba(30, 34, 56, 0.5);
        border: 1px solid rgba(102, 126, 234, 0.12);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0 1rem 0;
    }

    .eval-check-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.3rem 0;
        font-size: 0.8rem;
    }

    .eval-check-pass { color: #34d399; }
    .eval-check-fail { color: #f87171; }

    .eval-check-icon {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.65rem;
        flex-shrink: 0;
    }

    .eval-check-icon-pass {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
    }

    .eval-check-icon-fail {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
    }

    .eval-score-bar {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        margin-bottom: 0.8rem;
    }

    .eval-score-label {
        font-size: 0.72rem;
        color: #94a3b8;
        min-width: 55px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }

    .eval-bar-track {
        flex: 1;
        height: 6px;
        border-radius: 3px;
        background: rgba(100, 116, 139, 0.2);
        overflow: hidden;
    }

    .eval-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .eval-bar-fill-pass { background: linear-gradient(90deg, #34d399, #10b981); }
    .eval-bar-fill-warn { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
    .eval-bar-fill-fail { background: linear-gradient(90deg, #f87171, #ef4444); }

    .eval-score-num {
        font-size: 0.75rem;
        font-weight: 600;
        color: #e2e8f0;
        min-width: 35px;
        text-align: right;
    }

    /* ─── Eval Summary Dashboard ───────────────────────── */
    .eval-dashboard {
        background: linear-gradient(135deg, rgba(30, 34, 56, 0.8), rgba(20, 24, 46, 0.9));
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
    }

    .eval-dashboard-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .eval-node-row {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.6rem 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.3rem;
        transition: background 0.2s ease;
    }

    .eval-node-row:hover {
        background: rgba(102, 126, 234, 0.06);
    }

    .eval-node-name {
        flex: 1;
        font-size: 0.82rem;
        color: #cbd5e1;
        font-weight: 500;
    }

    .eval-node-scores {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }

    .eval-mini-score {
        font-size: 0.7rem;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-weight: 600;
    }

    /* ─── Sidebar Eval Score ────────────────────────────── */
    .sidebar-eval-score {
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.1rem 0.35rem;
        border-radius: 4px;
        margin-left: auto;
    }

    @keyframes score-fill {
        from { width: 0; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_card(title: str, content: str, badge: str = "", badge_type: str = ""):
    """Render a glassmorphism card."""
    badge_html = ""
    if badge:
        badge_html = f'<span class="badge badge-{badge_type}">{badge}</span>'

    st.markdown(f"""
    <div class="glass-card">
        <div class="glass-card-title">{title} {badge_html}</div>
        <div class="glass-card-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)


def render_stat_box(value: str | int, label: str):
    """Render a single stat counter."""
    return f"""
    <div class="stat-box">
        <div class="stat-value">{value}</div>
        <div class="stat-label">{label}</div>
    </div>
    """


def render_stats_row(stats: list[tuple[str | int, str]]):
    """Render a row of stat counters. Each stat is (value, label)."""
    boxes = "".join(render_stat_box(v, l) for v, l in stats)
    st.markdown(f'<div class="stats-row">{boxes}</div>', unsafe_allow_html=True)


def render_confidence_meter(level: str, label: str = ""):
    """Render a colored confidence bar."""
    level_lower = level.lower() if level else "medium"
    label_text = f"<span style='color:#94a3b8;font-size:0.8rem;'>{label} — <strong>{level.capitalize()}</strong></span>" if label else ""
    st.markdown(f"""
    {label_text}
    <div class="confidence-meter">
        <div class="confidence-fill confidence-{level_lower}"></div>
    </div>
    """, unsafe_allow_html=True)


def render_source_card(title: str, url: str, snippet: str = "", scores: dict = None):
    """Render a source card with optional scores."""
    scores_html = ""
    if scores:
        for key, val in scores.items():
            if key == "overall":
                continue
            css_class = "score-high" if val >= 7 else ("score-mid" if val >= 4 else "score-low")
            scores_html += f'<span class="source-score {css_class}">{key}: {val}</span>'

    snippet_html = f'<div class="source-snippet">{snippet[:200]}...</div>' if snippet and len(snippet) > 0 else ""

    st.markdown(f"""
    <div class="source-card">
        <div class="source-title">{title}</div>
        <a class="source-url" href="{url}" target="_blank">{url}</a>
        {snippet_html}
        <div style="margin-top:0.5rem;">{scores_html}</div>
    </div>
    """, unsafe_allow_html=True)


def render_contradiction_pair(claim_a: str, source_a: str, claim_b: str, source_b: str, nature: str = ""):
    """Render a side-by-side contradiction comparison (green vs red)."""
    st.markdown(f"""
    <div class="contradiction-pair">
        <div class="claim-card-agree">
            <div style="font-size:0.75rem;color:#34d399;font-weight:600;margin-bottom:0.4rem;">CLAIM A</div>
            <div style="color:#e2e8f0;font-size:0.85rem;line-height:1.5;">{claim_a}</div>
            <div style="color:#64748b;font-size:0.72rem;margin-top:0.4rem;">Source: {source_a}</div>
        </div>
        <div class="vs-divider">VS</div>
        <div class="claim-card-disagree">
            <div style="font-size:0.75rem;color:#f87171;font-weight:600;margin-bottom:0.4rem;">CLAIM B</div>
            <div style="color:#e2e8f0;font-size:0.85rem;line-height:1.5;">{claim_b}</div>
            <div style="color:#64748b;font-size:0.72rem;margin-top:0.4rem;">Source: {source_b}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if nature:
        st.markdown(f"<div style='text-align:center;color:#94a3b8;font-size:0.78rem;margin-top:-0.5rem;margin-bottom:1rem;'>↑ {nature}</div>", unsafe_allow_html=True)


def render_section_divider():
    """Render a gradient divider line."""
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


# ─── Eval Components ─────────────────────────────────────────────

def _score_color(score: float) -> str:
    """Get color hex for a score value."""
    if score >= 0.7:
        return "#34d399"
    elif score >= 0.4:
        return "#fbbf24"
    return "#f87171"


def _score_status(score: float) -> str:
    """Get status class for a score."""
    if score >= 0.7:
        return "pass"
    elif score >= 0.4:
        return "warn"
    return "fail"


def render_eval_badge(eval_result: dict | None):
    """Render an inline eval score badge next to a stage title."""
    if not eval_result:
        return

    score = eval_result.get("combined_score", 0)
    grade = eval_result.get("grade", "?")
    status = _score_status(score)

    st.markdown(f"""
    <span class="eval-badge eval-badge-{status}">
        📊 {grade} · {score:.0%}
    </span>
    """, unsafe_allow_html=True)


def render_eval_score_bars(eval_result: dict):
    """Render script and LLM score bars side by side."""
    script_score = eval_result.get("script_score", 0)
    llm_score = eval_result.get("llm_score", 0)
    combined = eval_result.get("combined_score", 0)

    script_status = _score_status(script_score)
    llm_status = _score_status(llm_score)
    combined_status = _score_status(combined)

    st.markdown(f"""
    <div class="eval-detail-card">
        <div class="eval-score-bar">
            <span class="eval-score-label">Script</span>
            <div class="eval-bar-track">
                <div class="eval-bar-fill eval-bar-fill-{script_status}" style="width:{script_score*100:.0f}%;animation:score-fill 0.8s ease-out;"></div>
            </div>
            <span class="eval-score-num" style="color:{_score_color(script_score)}">{script_score:.0%}</span>
        </div>
        <div class="eval-score-bar">
            <span class="eval-score-label">LLM</span>
            <div class="eval-bar-track">
                <div class="eval-bar-fill eval-bar-fill-{llm_status}" style="width:{llm_score*100:.0f}%;animation:score-fill 0.8s ease-out;"></div>
            </div>
            <span class="eval-score-num" style="color:{_score_color(llm_score)}">{llm_score:.0%}</span>
        </div>
        <div class="eval-score-bar" style="border-top:1px solid rgba(100,116,139,0.15);padding-top:0.6rem;">
            <span class="eval-score-label" style="color:#e2e8f0;">Blend</span>
            <div class="eval-bar-track" style="height:8px;">
                <div class="eval-bar-fill eval-bar-fill-{combined_status}" style="width:{combined*100:.0f}%;animation:score-fill 0.8s ease-out;"></div>
            </div>
            <span class="eval-score-num" style="color:{_score_color(combined)};font-size:0.82rem;">{combined:.0%}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_eval_details_card(eval_result: dict):
    """Render an expandable eval details card with script checks and LLM reasoning."""
    if not eval_result:
        return

    node_name = eval_result.get("node", "")
    eval_time = eval_result.get("eval_time_ms", 0)

    with st.expander(f"📊 Eval Details — {node_name} ({eval_time:.0f}ms)", expanded=False):
        # Score bars
        render_eval_score_bars(eval_result)

        col1, col2 = st.columns(2)

        # Script checks
        with col1:
            st.markdown("<div style='font-size:0.78rem;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;'>Script Checks</div>", unsafe_allow_html=True)
            checks = eval_result.get("script_checks", [])
            if checks:
                for check in checks:
                    passed = check.get("passed", False)
                    icon_class = "pass" if passed else "fail"
                    icon = "✓" if passed else "✕"
                    st.markdown(f"""
                    <div class="eval-check-item">
                        <span class="eval-check-icon eval-check-icon-{icon_class}">{icon}</span>
                        <span class="eval-check-{icon_class}">{check.get('name', '').replace('_', ' ').title()}</span>
                    </div>
                    <div style="padding-left:1.8rem;font-size:0.72rem;color:#64748b;margin-bottom:0.3rem;">
                        {check.get('detail', '')}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#64748b;font-size:0.8rem;'>No script checks</div>", unsafe_allow_html=True)

        # LLM eval
        with col2:
            st.markdown("<div style='font-size:0.78rem;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.5rem;'>LLM Assessment</div>", unsafe_allow_html=True)

            llm_raw = eval_result.get("llm_raw_score", 0)
            reasoning = eval_result.get("llm_reasoning", "")
            strengths = eval_result.get("llm_strengths", [])
            weaknesses = eval_result.get("llm_weaknesses", [])
            llm_error = eval_result.get("llm_error", "")

            if llm_error:
                st.markdown(f"<div style='color:#f87171;font-size:0.8rem;'>⚠ {llm_error}</div>", unsafe_allow_html=True)

            if reasoning:
                st.markdown(f"""
                <div style="color:#cbd5e1;font-size:0.82rem;line-height:1.6;margin-bottom:0.6rem;">
                    <strong style="color:#818cf8;">Score: {llm_raw}/10</strong><br>
                    {reasoning}
                </div>
                """, unsafe_allow_html=True)

            if strengths:
                for s in strengths[:3]:
                    st.markdown(f"""
                    <div class="eval-check-item">
                        <span class="eval-check-icon eval-check-icon-pass">+</span>
                        <span style="color:#34d399;font-size:0.8rem;">{s}</span>
                    </div>
                    """, unsafe_allow_html=True)

            if weaknesses:
                for w in weaknesses[:3]:
                    st.markdown(f"""
                    <div class="eval-check-item">
                        <span class="eval-check-icon eval-check-icon-fail">−</span>
                        <span style="color:#f87171;font-size:0.8rem;">{w}</span>
                    </div>
                    """, unsafe_allow_html=True)
