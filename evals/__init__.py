"""
Evaluation framework for the Agentic AI Research Pipeline.
Provides hybrid (script + LLM) evaluations at every node
and workflow transition tests.
"""

from evals.evaluator import PipelineEvaluator

__all__ = ["PipelineEvaluator"]
