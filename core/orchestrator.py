"""Optional pipeline runner helpers for future non-UI reuse."""

from __future__ import annotations

from graph import get_evaluator, reset_evaluator, research_graph


class PipelineOrchestrator:
    """Small wrapper around graph execution and evaluation state."""

    def __init__(self, graph=research_graph):
        self.graph = graph

    def reset(self):
        """Reset shared evaluator state before a run."""
        reset_evaluator()

    def evaluator(self):
        """Return the shared evaluator instance."""
        return get_evaluator()

    def stream_updates(self, initial_state: dict):
        """Stream graph updates in the same format the app expects."""
        return self.graph.stream(initial_state, stream_mode="updates")

    def evaluate_transition(self, transition_name: str, state: dict):
        """Evaluate a transition using the shared evaluator."""
        return self.evaluator().evaluate_transition(transition_name, state)

    def aggregate_scores(self):
        """Return the current aggregate evaluation summary."""
        return self.evaluator().get_aggregate_scores()
