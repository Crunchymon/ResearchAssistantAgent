"""
🔬 Agentic AI Research Assistant
Main Streamlit application.

Orchestrates the LangGraph pipeline with real-time UI updates,
showing the thinking process — not just the answer.
Includes inline evaluation scores at every pipeline stage.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config — must be first Streamlit call
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config import NODE_NAMES
from core.state_transformer import build_initial_state, build_transition_state, normalize_node_event
from core.orchestrator import PipelineOrchestrator
from ui.components import inject_custom_css, render_section_divider
from ui.render_dispatcher import render_completed_results
from ui.session_state import init_session_state, reset_pipeline_state
from ui.sidebar import render_sidebar_header, render_pipeline_tracker, render_sidebar_stats


PIPELINE = PipelineOrchestrator()


def validate_api_keys() -> bool:
    """Check if required API keys are set."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")

    if not groq_key or groq_key == "your_groq_api_key_here":
        st.error("⚠️ GROQ_API_KEY not set. Please add it to your `.env` file.")
        return False
    if not tavily_key or tavily_key == "your_tavily_api_key_here":
        st.error("⚠️ TAVILY_API_KEY not set. Please add it to your `.env` file.")
        return False
    return True


def _render_live_results(results_placeholder):
    """Render current results into a dedicated live placeholder."""
    if results_placeholder is None:
        return

    with results_placeholder.container():
        if st.session_state.node_data:
            render_completed_results(
                node_data=st.session_state.node_data,
                eval_data=st.session_state.eval_data,
                research_complete=st.session_state.research_complete,
                transition_evals=st.session_state.transition_evals,
                aggregate_eval=st.session_state.aggregate_eval,
                research_query=st.session_state.get("research_query", "research"),
            )


def run_research_pipeline(query: str, results_placeholder=None):
    """Execute the research pipeline with real-time UI updates and evals."""
    reset_pipeline_state()
    st.session_state.research_running = True

    # Reset evaluator for fresh run
    PIPELINE.reset()

    # Initial state
    initial_state = build_initial_state(query)

    try:
        for event in PIPELINE.stream_updates(initial_state):
            for node_name, node_output in event.items():
                if node_name == "__end__":
                    continue

                normalized = normalize_node_event(node_name, node_output)

                if normalized.retry_triggered:
                    st.session_state.retry_triggered = True
                    continue

                # Update tracking state
                st.session_state.current_node = normalized.node_name
                if normalized.node_name not in st.session_state.completed_nodes:
                    st.session_state.completed_nodes.append(normalized.node_name)

                if normalized.eval_result:
                    st.session_state.eval_data[normalized.node_name] = normalized.eval_result

                st.session_state.node_data[normalized.node_name] = normalized.raw_data
                st.session_state.node_data.update(normalized.stage_updates)

                # Progressive stage rendering: show each stage as soon as it arrives.
                _render_live_results(results_placeholder)

        # ─── Run Workflow Transition Evals ────────────────
        try:
            accumulated_state = build_transition_state(
                initial_state,
                st.session_state.completed_nodes,
                st.session_state.node_data,
            )

            # Run transitions
            for transition_name in ["decomposition_to_retrieval", "processing_to_synthesis", "review_to_refinement"]:
                t_result = PIPELINE.evaluate_transition(transition_name, accumulated_state)
                if t_result:
                    st.session_state.transition_evals[transition_name] = {
                        "transition_name": t_result.transition_name,
                        "from_node": t_result.from_node,
                        "to_node": t_result.to_node,
                        "script_score": t_result.script_score,
                        "llm_score": t_result.llm_score,
                        "combined_score": t_result.combined_score,
                        "script_details": t_result.script_details,
                        "llm_reasoning": t_result.llm_reasoning,
                        "checks_passed": t_result.checks_passed,
                        "checks_total": t_result.checks_total,
                    }
        except Exception:
            pass  # Don't fail the pipeline for transition eval errors

        # Get aggregate scores
        st.session_state.aggregate_eval = PIPELINE.aggregate_scores()

        st.session_state.research_complete = True
        st.session_state.research_running = False
        _render_live_results(results_placeholder)

    except Exception as e:
        st.session_state.error_message = str(e)
        st.session_state.research_running = False
        st.error(f"❌ Pipeline error: {e}")


def main():
    """Main application entry point."""
    init_session_state()
    inject_custom_css()

    # ─── Sidebar ──────────────────────────────────────────
    render_sidebar_header()

    if st.session_state.research_running or st.session_state.research_complete:
        render_pipeline_tracker(
            completed_nodes=st.session_state.completed_nodes,
            current_node=st.session_state.current_node if st.session_state.research_running else "",
            retry_triggered=st.session_state.retry_triggered,
            eval_data=st.session_state.eval_data,
        )

        # Show retrieval stats in sidebar
        retrieval_data = st.session_state.node_data.get("retrieval", {})
        if retrieval_data:
            render_sidebar_stats(retrieval_data.get("retrieval_stats", {}))

    # ─── Main Content ─────────────────────────────────────
    st.markdown('<div class="hero-title">Agentic AI Research Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Structured research with transparent reasoning — powered by LangGraph + Groq + Tavily</div>', unsafe_allow_html=True)

    # API key check
    if not validate_api_keys():
        st.markdown("""
        <div class="glass-card" style="border-color: rgba(245, 158, 11, 0.3);">
            <div class="glass-card-title">⚙️ Setup Required</div>
            <div class="glass-card-content">
                <ol>
                    <li>Copy <code>.env.example</code> to <code>.env</code></li>
                    <li>Add your <strong>GROQ_API_KEY</strong> from <a href="https://console.groq.com" target="_blank">console.groq.com</a></li>
                    <li>Add your <strong>TAVILY_API_KEY</strong> from <a href="https://tavily.com" target="_blank">tavily.com</a></li>
                    <li>Restart the app</li>
                </ol>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Query input
    query = st.text_input(
        "Enter your research query",
        placeholder="e.g., What is the impact of large language models on scientific research?",
        key="query_input",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        start_button = st.button("🚀 Start Research", use_container_width=True, disabled=st.session_state.research_running)
    with col2:
        if st.session_state.research_running:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.5rem;padding-top:0.5rem;">
                <div style="width:12px;height:12px;border-radius:50%;background:#818cf8;
                            animation:pulse-glow 1.5s ease-in-out infinite;"></div>
                <span style="color:#818cf8;font-size:0.9rem;font-weight:500;">
                    Processing: {NODE_NAMES.get(st.session_state.current_node, 'Starting...')}
                </span>
            </div>
            """, unsafe_allow_html=True)

    render_section_divider()
    live_results_placeholder = st.empty()

    # Run pipeline
    if start_button and query and not st.session_state.research_running:
        st.session_state.research_query = query
        run_research_pipeline(query, live_results_placeholder)
        st.rerun()

    # Render results
    if st.session_state.node_data:
        render_completed_results(
            node_data=st.session_state.node_data,
            eval_data=st.session_state.eval_data,
            research_complete=st.session_state.research_complete,
            transition_evals=st.session_state.transition_evals,
            aggregate_eval=st.session_state.aggregate_eval,
            research_query=st.session_state.get("research_query", "research"),
        )

    # Error display
    if st.session_state.error_message:
        st.error(f"Pipeline encountered an error: {st.session_state.error_message}")

    # Footer
    if not st.session_state.research_running and not st.session_state.research_complete:
        st.markdown("""
        <div style="text-align:center;margin-top:4rem;color:#475569;font-size:0.82rem;">
            <div style="margin-bottom:0.5rem;">Built with LangGraph · Groq · Tavily · Streamlit</div>
            <div>Enter a query above to begin your research journey</div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
