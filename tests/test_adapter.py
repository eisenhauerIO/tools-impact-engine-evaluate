"""Tests for the Evaluate pipeline component."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from impact_engine_evaluate.adapter import (
    EVALUATE_RESULT_FILENAME,
    SCORE_RESULT_FILENAME,
    Evaluate,
)
from impact_engine_evaluate.review.models import DimensionResponse, ReviewResponse

SAMPLE_PARSED = ReviewResponse(
    dimensions=[
        DimensionResponse(name="randomization_integrity", score=0.85, justification="Good balance."),
        DimensionResponse(name="specification_adequacy", score=0.80, justification="Appropriate specification."),
        DimensionResponse(name="statistical_inference", score=0.75, justification="CIs reported."),
        DimensionResponse(name="threats_to_validity", score=0.70, justification="Some attrition noted."),
        DimensionResponse(name="effect_size_plausibility", score=0.90, justification="Realistic."),
    ],
    overall=0.80,
)

EXPECTED_KEYS = {
    "initiative_id",
    "confidence",
    "confidence_range",
    "strategy",
    "report",
}


# -- Shared assertions -------------------------------------------------------


def _assert_evaluate_result_written(job_dir):
    """Both strategies write evaluate_result.json to the job directory."""
    result_path = Path(job_dir) / EVALUATE_RESULT_FILENAME
    assert result_path.exists(), "evaluate_result.json not written"
    written = json.loads(result_path.read_text())
    assert set(written.keys()) == EXPECTED_KEYS

    # Manifest must not be mutated by the evaluate stage
    manifest = json.loads((Path(job_dir) / "manifest.json").read_text())
    assert "evaluate_result" not in manifest.get("files", {})


# -- Score strategy -----------------------------------------------------------


def test_score_returns_correct_keys(score_job_dir):
    """Score strategy returns all expected EvaluateResult keys."""
    evaluator = Evaluate()
    result = evaluator.execute({"job_dir": score_job_dir})
    assert set(result.keys()) == EXPECTED_KEYS


def test_score_confidence_in_range(score_job_dir):
    """Score strategy produces confidence within the experiment range."""
    evaluator = Evaluate()
    result = evaluator.execute({"job_dir": score_job_dir})
    assert 0.85 <= result["confidence"] <= 1.0


def test_score_is_deterministic(score_job_dir):
    """Repeated score calls produce identical results."""
    evaluator = Evaluate()
    r1 = evaluator.execute({"job_dir": score_job_dir})
    r2 = evaluator.execute({"job_dir": score_job_dir})
    assert r1 == r2


def test_score_strategy_and_report(score_job_dir):
    """Score strategy populates strategy, confidence_range, and a descriptive report."""
    evaluator = Evaluate()
    result = evaluator.execute({"job_dir": score_job_dir})
    assert result["strategy"] == "score"
    assert result["confidence_range"] == (0.85, 1.0)
    assert isinstance(result["report"], str)
    assert "0.85" in result["report"]
    assert "1.00" in result["report"]


def test_score_writes_evaluate_result(score_job_dir):
    """Score strategy writes evaluate_result.json without touching manifest."""
    Evaluate().execute({"job_dir": score_job_dir})
    _assert_evaluate_result_written(score_job_dir)


def test_score_writes_score_result(score_job_dir):
    """Score strategy writes score_result.json to the job directory."""
    Evaluate().execute({"job_dir": score_job_dir})
    result_path = Path(score_job_dir) / SCORE_RESULT_FILENAME
    assert result_path.exists(), "score_result.json not written"
    written = json.loads(result_path.read_text())
    assert "confidence" in written
    assert "confidence_range" in written
    assert "initiative_id" in written


# -- Review strategy ----------------------------------------------------------


def _mock_litellm_completion():
    return MagicMock(
        choices=[MagicMock(message=MagicMock(parsed=SAMPLE_PARSED, content=SAMPLE_PARSED.model_dump_json()))]
    )


@patch("impact_engine_evaluate.review.engine.litellm")
def test_review_returns_correct_keys(mock_litellm, review_job_dir):
    """Review strategy returns all expected output keys."""
    mock_litellm.completion.return_value = _mock_litellm_completion()

    evaluator = Evaluate(config={"backend": {"model": "mock-model"}})
    result = evaluator.execute({"job_dir": review_job_dir})
    assert set(result.keys()) == EXPECTED_KEYS


@patch("impact_engine_evaluate.review.engine.litellm")
def test_review_uses_llm_confidence(mock_litellm, review_job_dir):
    """Review strategy uses the LLM overall_score as confidence."""
    mock_litellm.completion.return_value = _mock_litellm_completion()

    evaluator = Evaluate(config={"backend": {"model": "mock-model"}})
    result = evaluator.execute({"job_dir": review_job_dir})
    assert result["confidence"] == 0.80


@patch("impact_engine_evaluate.review.engine.litellm")
def test_review_strategy_and_report(mock_litellm, review_job_dir):
    """Review strategy populates strategy, confidence_range, and a full report."""
    mock_litellm.completion.return_value = _mock_litellm_completion()

    evaluator = Evaluate(config={"backend": {"model": "mock-model"}})
    result = evaluator.execute({"job_dir": review_job_dir})
    assert result["strategy"] == "review"
    assert result["confidence_range"] == (0.85, 1.0)
    report = result["report"]
    assert isinstance(report, dict)
    assert "dimensions" in report
    assert "overall_score" in report
    assert "raw_response" in report


@patch("impact_engine_evaluate.review.engine.litellm")
def test_review_writes_evaluate_result(mock_litellm, review_job_dir):
    """Review strategy writes evaluate_result.json without touching manifest."""
    mock_litellm.completion.return_value = _mock_litellm_completion()

    Evaluate(config={"backend": {"model": "mock-model"}}).execute({"job_dir": review_job_dir})
    _assert_evaluate_result_written(review_job_dir)


# -- Error cases --------------------------------------------------------------


def test_unknown_strategy_raises():
    """Unknown evaluate_strategy raises ValueError."""
    tmpdir = tempfile.mkdtemp(prefix="job-unknown-test-")
    manifest = {
        "schema_version": "2.0",
        "model_type": "experiment",
        "evaluate_strategy": "unknown_xyz",
        "files": {
            "impact_results": {"path": "impact_results.json", "format": "json"},
        },
    }
    results = {"ci_upper": 1.0, "effect_estimate": 0.5, "ci_lower": 0.0, "cost_to_scale": 10.0, "sample_size": 10}
    Path(tmpdir, "manifest.json").write_text(json.dumps(manifest))
    Path(tmpdir, "impact_results.json").write_text(json.dumps(results))

    evaluator = Evaluate()
    with pytest.raises(ValueError, match="Unknown evaluate_strategy"):
        evaluator.execute({"job_dir": tmpdir})


def test_default_strategy_is_review():
    """Manifest without evaluate_strategy defaults to review."""
    tmpdir = tempfile.mkdtemp(prefix="job-default-test-")
    manifest = {
        "schema_version": "2.0",
        "model_type": "experiment",
        "files": {
            "impact_results": {"path": "impact_results.json", "format": "json"},
        },
    }
    results = {"ci_upper": 1.0, "effect_estimate": 0.5, "ci_lower": 0.0, "cost_to_scale": 10.0, "sample_size": 10}
    Path(tmpdir, "manifest.json").write_text(json.dumps(manifest))
    Path(tmpdir, "impact_results.json").write_text(json.dumps(results))

    from impact_engine_evaluate.review.manifest import load_manifest

    m = load_manifest(tmpdir)
    assert m.evaluate_strategy == "review"
