"""Tests for the review() public API — end-to-end."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from impact_engine_evaluate.review import engine as _engine_mod
from impact_engine_evaluate.review.api import review

SAMPLE_RESPONSE = """\
DIMENSION: randomization_integrity
SCORE: 0.85
JUSTIFICATION: Good balance across covariates.

DIMENSION: specification_adequacy
SCORE: 0.80
JUSTIFICATION: Appropriate OLS specification.

DIMENSION: statistical_inference
SCORE: 0.75
JUSTIFICATION: CIs reported, no multiple testing correction.

DIMENSION: threats_to_validity
SCORE: 0.70
JUSTIFICATION: Some attrition noted.

DIMENSION: effect_size_plausibility
SCORE: 0.90
JUSTIFICATION: Effect size is realistic.

OVERALL: 0.80
"""


def _make_job_dir():
    tmpdir = tempfile.mkdtemp(prefix="job-impact-engine-test-")
    manifest = {
        "schema_version": "2.0",
        "model_type": "experiment",
        "created_at": "2025-06-01T12:00:00+00:00",
        "files": {
            "impact_results": {"path": "impact_results.json", "format": "json"},
        },
    }
    results = {
        "initiative_id": "init-api-test",
        "model_type": "experiment",
        "effect_estimate": 5.2,
        "ci_lower": 2.1,
        "ci_upper": 8.3,
        "sample_size": 500,
    }
    Path(tmpdir, "manifest.json").write_text(json.dumps(manifest))
    Path(tmpdir, "impact_results.json").write_text(json.dumps(results))
    return tmpdir


@patch.object(_engine_mod, "BackendRegistry")
def test_review_end_to_end(mock_registry_cls):
    mock_backend = mock_registry_cls.create.return_value
    mock_backend.name = "mock"
    mock_backend.complete.return_value = SAMPLE_RESPONSE

    job_dir = _make_job_dir()
    result = review(job_dir, config={"backend": {"type": "mock", "model": "mock-model"}})

    assert result.overall_score == 0.80
    assert len(result.dimensions) == 5
    assert result.prompt_name == "experiment_review"
    assert result.initiative_id  # has identity

    # Result file written
    result_path = Path(job_dir) / "review_result.json"
    assert result_path.exists()
    written = json.loads(result_path.read_text())
    assert written["overall_score"] == 0.80

    # Manifest updated
    with open(Path(job_dir) / "manifest.json") as fh:
        manifest_data = json.load(fh)
    assert "review_result" in manifest_data["files"]


@patch.object(_engine_mod, "BackendRegistry")
def test_review_returns_review_result(mock_registry_cls):
    mock_backend = mock_registry_cls.create.return_value
    mock_backend.name = "mock"
    mock_backend.complete.return_value = SAMPLE_RESPONSE

    job_dir = _make_job_dir()
    result = review(job_dir, config={"backend": {"type": "mock"}})

    from impact_engine_evaluate.review.models import ReviewResult

    assert isinstance(result, ReviewResult)
    assert result.backend_name == "mock"
    assert result.raw_response == SAMPLE_RESPONSE
    assert result.timestamp


def test_review_missing_manifest():
    with pytest.raises(FileNotFoundError, match="Manifest not found"):
        review("/nonexistent/path/xyz")


def test_review_unknown_method():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = {
            "schema_version": "2.0",
            "model_type": "unknown_method_xyz",
            "files": {},
        }
        Path(tmpdir, "manifest.json").write_text(json.dumps(manifest))
        with pytest.raises(KeyError, match="Unknown method"):
            review(tmpdir)
