"""
PipelineEvaluator — Main orchestrator for the evaluation framework.

Runs hybrid (script + LLM) evaluations for individual nodes and
workflow transitions. Stores all results for frontend rendering.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from evals.eval_config import SCRIPT_WEIGHT, LLM_WEIGHT, score_to_grade, score_to_status
from evals.script_evals import SCRIPT_EVAL_REGISTRY, ScriptEvalResult
from evals.llm_evals import LLM_EVAL_REGISTRY, LLMEvalResult
from evals.workflow_evals import WORKFLOW_EVAL_REGISTRY, TransitionEvalResult


@dataclass
class NodeEvalResult:
    """Complete evaluation result for a single node."""
    node_name: str
    script_eval: ScriptEvalResult | None = None
    llm_eval: LLMEvalResult | None = None
    script_score: float = 0.0
    llm_score: float = 0.0
    combined_score: float = 0.0
    grade: str = "?"
    status: str = "pending"  # pass, warn, fail
    eval_time_ms: float = 0.0

    def to_dict(self) -> dict:
        """Serialize for state storage and UI rendering."""
        return {
            "node": self.node_name,
            "script_score": self.script_score,
            "llm_score": self.llm_score,
            "combined_score": self.combined_score,
            "grade": self.grade,
            "status": self.status,
            "eval_time_ms": self.eval_time_ms,
            "script_checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "detail": c.detail,
                }
                for c in (self.script_eval.checks if self.script_eval else [])
            ],
            "script_summary": self.script_eval.summary if self.script_eval else "",
            "llm_reasoning": self.llm_eval.reasoning if self.llm_eval else "",
            "llm_raw_score": self.llm_eval.raw_score if self.llm_eval else 0,
            "llm_strengths": self.llm_eval.strengths if self.llm_eval else [],
            "llm_weaknesses": self.llm_eval.weaknesses if self.llm_eval else [],
            "llm_error": self.llm_eval.error if self.llm_eval else "",
        }


class PipelineEvaluator:
    """Orchestrates hybrid evaluations across the research pipeline."""

    def __init__(self):
        self.node_results: dict[str, NodeEvalResult] = {}
        self.transition_results: dict[str, TransitionEvalResult] = {}

    def evaluate_node(
        self,
        node_name: str,
        input_state: dict,
        output: dict,
    ) -> NodeEvalResult:
        """Run hybrid evaluation for a single node.

        Args:
            node_name: Pipeline node identifier (e.g. 'query_intake')
            input_state: State before node execution
            output: State updates returned by the node

        Returns:
            NodeEvalResult with blended score
        """
        start_time = time.time()

        # ─── Script Eval ─────────────────────────────────
        script_eval = None
        script_score = 0.0
        if node_name in SCRIPT_EVAL_REGISTRY:
            try:
                script_eval = SCRIPT_EVAL_REGISTRY[node_name](input_state, output)
                script_score = script_eval.score
            except Exception as e:
                script_eval = ScriptEvalResult(score=0.0, summary=f"Script eval error: {e}")

        # ─── LLM Eval ────────────────────────────────────
        llm_eval = None
        llm_score = 0.0
        if node_name in LLM_EVAL_REGISTRY:
            try:
                llm_eval = LLM_EVAL_REGISTRY[node_name](input_state, output)
                llm_score = llm_eval.score
            except Exception as e:
                llm_eval = LLMEvalResult(score=0.5, raw_score=5, error=str(e))
                llm_score = 0.5

        # ─── Blend Scores ────────────────────────────────
        combined = round(SCRIPT_WEIGHT * script_score + LLM_WEIGHT * llm_score, 3)

        elapsed = round((time.time() - start_time) * 1000, 1)

        result = NodeEvalResult(
            node_name=node_name,
            script_eval=script_eval,
            llm_eval=llm_eval,
            script_score=round(script_score, 3),
            llm_score=round(llm_score, 3),
            combined_score=combined,
            grade=score_to_grade(combined),
            status=score_to_status(combined),
            eval_time_ms=elapsed,
        )

        self.node_results[node_name] = result
        return result

    def evaluate_transition(self, transition_name: str, state: dict) -> TransitionEvalResult | None:
        """Run a workflow transition evaluation.

        Args:
            transition_name: Transition identifier (e.g. 'decomposition_to_retrieval')
            state: Full pipeline state at the point of transition

        Returns:
            TransitionEvalResult or None if transition not found
        """
        if transition_name not in WORKFLOW_EVAL_REGISTRY:
            return None

        try:
            result = WORKFLOW_EVAL_REGISTRY[transition_name](state)
            self.transition_results[transition_name] = result
            return result
        except Exception as e:
            result = TransitionEvalResult(
                transition_name=transition_name,
                from_node="?",
                to_node="?",
                combined_score=0.0,
                script_details=f"Error: {e}",
            )
            self.transition_results[transition_name] = result
            return result

    def get_aggregate_scores(self) -> dict:
        """Compute aggregate pipeline quality metrics."""
        if not self.node_results:
            return {
                "overall_score": 0.0,
                "overall_grade": "?",
                "overall_status": "pending",
                "node_scores": {},
                "transition_scores": {},
                "nodes_evaluated": 0,
                "transitions_evaluated": 0,
            }

        # Node scores
        node_scores = {
            name: result.combined_score
            for name, result in self.node_results.items()
        }
        avg_node_score = (
            sum(node_scores.values()) / len(node_scores)
            if node_scores
            else 0.0
        )

        # Transition scores
        transition_scores = {
            name: result.combined_score
            for name, result in self.transition_results.items()
        }
        avg_transition = (
            sum(transition_scores.values()) / len(transition_scores)
            if transition_scores
            else 0.0
        )

        # Overall = 70% node avg + 30% transition avg (if transitions exist)
        if transition_scores:
            overall = round(0.7 * avg_node_score + 0.3 * avg_transition, 3)
        else:
            overall = round(avg_node_score, 3)

        return {
            "overall_score": overall,
            "overall_grade": score_to_grade(overall),
            "overall_status": score_to_status(overall),
            "node_scores": node_scores,
            "transition_scores": transition_scores,
            "nodes_evaluated": len(node_scores),
            "transitions_evaluated": len(transition_scores),
            "avg_node_score": round(avg_node_score, 3),
            "avg_transition_score": round(avg_transition, 3),
        }

    def get_all_results_for_ui(self) -> dict:
        """Get all results formatted for frontend rendering."""
        return {
            "node_evals": {
                name: result.to_dict()
                for name, result in self.node_results.items()
            },
            "transition_evals": {
                name: {
                    "transition_name": result.transition_name,
                    "from_node": result.from_node,
                    "to_node": result.to_node,
                    "script_score": result.script_score,
                    "llm_score": result.llm_score,
                    "combined_score": result.combined_score,
                    "script_details": result.script_details,
                    "llm_reasoning": result.llm_reasoning,
                    "checks_passed": result.checks_passed,
                    "checks_total": result.checks_total,
                    "grade": score_to_grade(result.combined_score),
                    "status": score_to_status(result.combined_score),
                }
                for name, result in self.transition_results.items()
            },
            "aggregate": self.get_aggregate_scores(),
        }
