"""Tests for the Evaluate pipeline component."""

from impact_engine_evaluate.adapter import Evaluate
from impact_engine_evaluate.scorer import score_initiative


def test_execute_returns_correct_keys(sample_measure_event):
    """Execute returns all expected EvaluateResult keys."""
    evaluator = Evaluate()
    result = evaluator.execute(sample_measure_event)
    expected_keys = {
        "initiative_id",
        "confidence",
        "cost",
        "return_best",
        "return_median",
        "return_worst",
        "model_type",
        "sample_size",
    }
    assert set(result.keys()) == expected_keys


def test_execute_matches_scorer(sample_measure_event):
    """Adapter result matches direct scorer output."""
    evaluator = Evaluate()
    adapter_result = evaluator.execute(sample_measure_event)
    scorer_result = score_initiative(sample_measure_event)
    assert adapter_result == scorer_result


def test_execute_deterministic(sample_measure_event):
    """Repeated calls produce identical results."""
    evaluator = Evaluate()
    r1 = evaluator.execute(sample_measure_event)
    r2 = evaluator.execute(sample_measure_event)
    assert r1 == r2
