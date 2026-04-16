"""Streamlit session state helpers for the research app."""

from __future__ import annotations

import copy

import streamlit as st


SESSION_DEFAULTS = {
    "research_running": False,
    "research_complete": False,
    "completed_nodes": [],
    "current_node": "",
    "node_data": {},
    "eval_data": {},
    "transition_evals": {},
    "aggregate_eval": {},
    "final_state": None,
    "retry_triggered": False,
    "error_message": "",
}


def init_session_state():
    """Initialize all session keys used by the app."""
    for key, default_value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(default_value)


def reset_pipeline_state():
    """Reset run-specific keys before starting a new research query."""
    for key, default_value in SESSION_DEFAULTS.items():
        st.session_state[key] = copy.deepcopy(default_value)
