"""Tests for the Evaluate pipeline component."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from impact_engine_evaluate.adapter import (
    EVALUATE_RESULT_FILENAME,
    SCORE_RESULT_FILENAME,
    Evaluate,
)
from impact_engine_evaluate.review import engine as _engine_mod

SAMPLE_RESPONSE = """\
DIMENSION: randomization_integrity
SCORE: 0.85
JUSTIFICATION: Good balance.

DIMENSION: specification_adequacy
SCORE: 0.80
JUSTIFICATION: Appropriate specification.

DIMENSION: statistical_inference
SCORE: 0.75
JUSTIFICATION: CIs reported.

DIMENSION: threats_to_validity
SCORE: 0.70
JUSTIFICATION: Some attrition noted.

DIMENSION: effect_size_plausibility
SCORE: 0.90
JUSTIFICATION: Realistic.

OVERALL: 0.80
"""

EXPECTED_KEYS = {
    "initiative_id",
    "confidence",
    "cost",
    "return_best",
    "return_median",
    "return_worst",
    "model_type",
    "sample_size",
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


def test_score_reads_returns(score_job_dir):
    """Score strategy reads scenario returns from impact_results.json."""
    evaluator = Evaluate()
    result = evaluator.execute({"job_dir": score_job_dir})
    assert result["return_best"] == 15.0
    assert result["return_median"] == 10.0
    assert result["return_worst"] == 5.0
    assert result["cost"] == 100.0
    assert result["sample_size"] == 50


def test_cost_override(score_job_dir):
    """Cost override in the event takes precedence over impact_results.json."""
    evaluator = Evaluate()
    result = evaluator.execute({"job_dir": score_job_dir, "cost_to_scale": 999.0})
    assert result["cost"] == 999.0


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


@patch.object(_engine_mod, "BackendRegistry")
def test_review_returns_correct_keys(mock_registry_cls, review_job_dir):
    """Review strategy returns all expected output keys."""
    mock_backend = mock_registry_cls.create.return_value
    mock_backend.name = "mock"
    mock_backend.complete.return_value = SAMPLE_RESPONSE

    evaluator = Evaluate(config={"backend": {"type": "mock", "model": "mock-model"}})
    result = evaluator.execute({"job_dir": review_job_dir})
    assert set(result.keys()) == EXPECTED_KEYS


@patch.object(_engine_mod, "BackendRegistry")
def test_review_uses_llm_confidence(mock_registry_cls, review_job_dir):
    """Review strategy uses the LLM overall_score as confidence."""
    mock_backend = mock_registry_cls.create.return_value
    mock_backend.name = "mock"
    mock_backend.complete.return_value = SAMPLE_RESPONSE

    evaluator = Evaluate(config={"backend": {"type": "mock"}})
    result = evaluator.execute({"job_dir": review_job_dir})
    assert result["confidence"] == 0.80


@patch.object(_engine_mod, "BackendRegistry")
def test_review_writes_evaluate_result(mock_registry_cls, review_job_dir):
    """Review strategy writes evaluate_result.json without touching manifest."""
    mock_backend = mock_registry_cls.create.return_value
    mock_backend.name = "mock"
    mock_backend.complete.return_value = SAMPLE_RESPONSE

    Evaluate(config={"backend": {"type": "mock"}}).execute({"job_dir": review_job_dir})
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
