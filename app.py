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

from config import NODE_ORDER, NODE_NAMES
from graph import research_graph, reset_evaluator, get_evaluator
from ui.components import inject_custom_css, render_section_divider
from ui.sidebar import render_sidebar_header, render_pipeline_tracker, render_sidebar_stats
from ui.stages import (
    render_query_stage,
    render_decomposition_stage,
    render_retrieval_stage,
    render_processing_stage,
    render_synthesis_stage,
    render_outline_stage,
    render_draft_stage,
    render_review_stage,
    render_final_report,
    render_eval_summary_dashboard,
)


def init_session_state():
    """Initialize Streamlit session state variables."""
    defaults = {
        "research_running": False,
        "research_complete": False,
        "completed_nodes": [],
        "current_node": "",
        "node_data": {},       # {node_name: output_data}
        "eval_data": {},       # {node_name: eval_result_dict}
        "transition_evals": {},  # {transition_name: transition_result}
        "aggregate_eval": {},  # Overall pipeline eval scores
        "final_state": None,
        "retry_triggered": False,
        "error_message": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


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


def run_research_pipeline(query: str):
    """Execute the research pipeline with real-time UI updates and evals."""
    st.session_state.research_running = True
    st.session_state.research_complete = False
    st.session_state.completed_nodes = []
    st.session_state.current_node = ""
    st.session_state.node_data = {}
    st.session_state.eval_data = {}
    st.session_state.transition_evals = {}
    st.session_state.aggregate_eval = {}
    st.session_state.final_state = None
    st.session_state.retry_triggered = False
    st.session_state.error_message = ""

    # Reset evaluator for fresh run
    reset_evaluator()

    # Initial state
    initial_state = {
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

    try:
        # Stream the graph execution to get node-by-node updates
        progress_placeholder = st.empty()
        stage_container = st.container()

        for event in research_graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                if node_name == "__end__":
                    continue

                # Map internal node names to display names
                display_node = node_name
                if node_name == "increment_retry":
                    st.session_state.retry_triggered = True
                    continue

                # Update tracking state
                st.session_state.current_node = display_node
                if display_node not in st.session_state.completed_nodes:
                    st.session_state.completed_nodes.append(display_node)

                # Store node output data
                if isinstance(node_output, dict):
                    # Extract eval results
                    eval_results = node_output.get("eval_results", [])
                    if eval_results:
                        latest_eval = eval_results[-1] if isinstance(eval_results, list) else eval_results
                        st.session_state.eval_data[display_node] = latest_eval

                    # Extract the actual data from node_outputs log
                    node_outputs = node_output.get("node_outputs", [])
                    if node_outputs:
                        latest = node_outputs[-1] if isinstance(node_outputs, list) else node_outputs
                        st.session_state.node_data[display_node] = latest.get("data", node_output)
                    else:
                        st.session_state.node_data[display_node] = node_output

                    # Store specific fields for stage renderers
                    if "refined_query" in node_output and node_output["refined_query"]:
                        st.session_state.node_data["query_intake"] = {
                            "refined_query": node_output["refined_query"],
                        }
                    if "sub_questions" in node_output and node_output["sub_questions"]:
                        st.session_state.node_data["decomposition"] = {
                            "sub_questions": node_output["sub_questions"],
                        }
                    if "search_results" in node_output:
                        st.session_state.node_data["retrieval"] = {
                            "search_results": node_output.get("search_results", {}),
                            "retrieval_stats": node_output.get("retrieval_stats", {}),
                        }
                    if "processed_data" in node_output:
                        st.session_state.node_data["processing"] = node_output["processed_data"]
                    if "insights" in node_output:
                        st.session_state.node_data["synthesis"] = node_output["insights"]
                    if "outline" in node_output and node_output.get("outline"):
                        st.session_state.node_data["outline"] = node_output["outline"]
                    if "draft" in node_output and node_output.get("draft"):
                        st.session_state.node_data["draft"] = node_output["draft"]
                    if "review_feedback" in node_output:
                        st.session_state.node_data["review"] = node_output["review_feedback"]
                    if "final_report" in node_output and node_output.get("final_report"):
                        st.session_state.node_data["final_report"] = node_output["final_report"]

        # ─── Run Workflow Transition Evals ────────────────
        evaluator = get_evaluator()
        try:
            # Build accumulated state for transition evals
            accumulated_state = dict(initial_state)
            for node_name_key in st.session_state.completed_nodes:
                data = st.session_state.node_data.get(node_name_key, {})
                if isinstance(data, dict):
                    accumulated_state.update(data)

            # Also pull specific top-level fields
            if "query_intake" in st.session_state.node_data:
                accumulated_state["refined_query"] = st.session_state.node_data["query_intake"].get("refined_query", "")
            if "decomposition" in st.session_state.node_data:
                accumulated_state["sub_questions"] = st.session_state.node_data["decomposition"].get("sub_questions", [])
            if "retrieval" in st.session_state.node_data:
                accumulated_state["search_results"] = st.session_state.node_data["retrieval"].get("search_results", {})
                accumulated_state["retrieval_stats"] = st.session_state.node_data["retrieval"].get("retrieval_stats", {})
            if "processing" in st.session_state.node_data:
                proc = st.session_state.node_data["processing"]
                accumulated_state["processed_data"] = proc if isinstance(proc, dict) else {}
            if "synthesis" in st.session_state.node_data:
                syn = st.session_state.node_data["synthesis"]
                accumulated_state["insights"] = syn if isinstance(syn, dict) else {}
            if "review" in st.session_state.node_data:
                rev = st.session_state.node_data["review"]
                accumulated_state["review_feedback"] = rev if isinstance(rev, dict) else {}
            if "draft" in st.session_state.node_data:
                accumulated_state["draft"] = st.session_state.node_data["draft"]
            if "final_report" in st.session_state.node_data:
                accumulated_state["final_report"] = st.session_state.node_data["final_report"]

            # Run transitions
            for transition_name in ["decomposition_to_retrieval", "processing_to_synthesis", "review_to_refinement"]:
                t_result = evaluator.evaluate_transition(transition_name, accumulated_state)
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
        st.session_state.aggregate_eval = evaluator.get_aggregate_scores()

        st.session_state.research_complete = True
        st.session_state.research_running = False

    except Exception as e:
        st.session_state.error_message = str(e)
        st.session_state.research_running = False
        st.error(f"❌ Pipeline error: {e}")


def render_results():
    """Render all completed stage results with eval scores."""
    node_data = st.session_state.node_data
    eval_data = st.session_state.eval_data

    # N1: Query
    if "query_intake" in node_data:
        render_query_stage(node_data["query_intake"], eval_data.get("query_intake"))

    # N2: Decomposition
    if "decomposition" in node_data:
        render_decomposition_stage(node_data["decomposition"], eval_data.get("decomposition"))

    # N3: Retrieval
    if "retrieval" in node_data:
        render_retrieval_stage(node_data["retrieval"], eval_data.get("retrieval"))

    # N4: Processing
    if "processing" in node_data:
        render_processing_stage(node_data["processing"], eval_data.get("processing"))

    # N5: Synthesis
    if "synthesis" in node_data:
        render_synthesis_stage(node_data["synthesis"], eval_data.get("synthesis"))

    # N6: Outline
    if "outline" in node_data:
        render_outline_stage(node_data["outline"], eval_data.get("outline"))

    # N7: Draft
    if "draft" in node_data:
        render_draft_stage(node_data["draft"], eval_data.get("draft"))

    # N8: Review
    if "review" in node_data:
        render_review_stage(node_data["review"], eval_data.get("review"))

    # N9: Final Report
    if "final_report" in node_data:
        render_final_report(
            node_data["final_report"],
            st.session_state.get("research_query", "research"),
            eval_data.get("refinement"),
        )

    # ─── Eval Summary Dashboard ──────────────────────────
    if st.session_state.research_complete and eval_data:
        render_eval_summary_dashboard(
            eval_data=eval_data,
            transition_evals=st.session_state.transition_evals,
            aggregate=st.session_state.aggregate_eval,
        )


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

    # Run pipeline
    if start_button and query and not st.session_state.research_running:
        st.session_state.research_query = query
        run_research_pipeline(query)
        st.rerun()

    # Render results
    if st.session_state.node_data:
        render_results()

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
