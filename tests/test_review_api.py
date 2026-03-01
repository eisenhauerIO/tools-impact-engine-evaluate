"""Tests for the review() public API — end-to-end."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from impact_engine_evaluate.review import engine as _engine_mod
from impact_engine_evaluate.review.api import compute_review, review
from impact_engine_evaluate.review.models import DimensionResponse, ReviewResponse

SAMPLE_PARSED = ReviewResponse(
    dimensions=[
        DimensionResponse(name="randomization_integrity", score=0.85, justification="Good balance across covariates."),
        DimensionResponse(name="specification_adequacy", score=0.80, justification="Appropriate OLS specification."),
        DimensionResponse(name="statistical_inference", score=0.75, justification="CIs reported."),
        DimensionResponse(name="threats_to_validity", score=0.70, justification="Some attrition noted."),
        DimensionResponse(name="effect_size_plausibility", score=0.90, justification="Effect size is realistic."),
    ],
    overall=0.80,
)


def _make_job_dir():
    tmpdir = tempfile.mkdtemp(prefix="job-impact-engine-test-")
    manifest = {
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


def _mock_litellm_completion():
    return MagicMock(
        choices=[MagicMock(message=MagicMock(parsed=SAMPLE_PARSED, content=SAMPLE_PARSED.model_dump_json()))]
    )


@patch.object(_engine_mod, "litellm")
def test_review_end_to_end(mock_litellm):
    mock_litellm.completion.return_value = _mock_litellm_completion()

    job_dir = _make_job_dir()
    result = review(job_dir, config={"backend": {"model": "mock-model"}})

    assert result.overall_score == 0.80
    assert len(result.dimensions) == 5
    assert result.prompt_name == "experiment_review"
    assert result.initiative_id

    # Result file written
    result_path = Path(job_dir) / "review_result.json"
    assert result_path.exists()
    written = json.loads(result_path.read_text())
    assert written["overall_score"] == 0.80

    # Manifest must not be mutated
    with open(Path(job_dir) / "manifest.json") as fh:
        manifest_data = json.load(fh)
    assert "review_result" not in manifest_data.get("files", {})


@patch.object(_engine_mod, "litellm")
def test_review_returns_review_result(mock_litellm):
    mock_litellm.completion.return_value = _mock_litellm_completion()

    job_dir = _make_job_dir()
    result = review(job_dir, config={"backend": {"model": "mock-model"}})

    from impact_engine_evaluate.review.models import ReviewResult

    assert isinstance(result, ReviewResult)
    assert result.backend_name == "litellm"
    assert result.timestamp


@patch.object(_engine_mod, "litellm")
def test_compute_review_does_not_write(mock_litellm):
    """compute_review returns a result without writing to the job directory."""
    mock_litellm.completion.return_value = _mock_litellm_completion()

    job_dir = _make_job_dir()
    result = compute_review(job_dir, config={"backend": {"model": "mock-model"}})

    assert result.overall_score == 0.80
    assert not (Path(job_dir) / "review_result.json").exists()


def test_review_missing_manifest():
    with pytest.raises(FileNotFoundError, match="Manifest not found"):
        review("/nonexistent/path/xyz")


def test_review_unknown_method():
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = {
            "model_type": "unknown_method_xyz",
            "files": {},
        }
        Path(tmpdir, "manifest.json").write_text(json.dumps(manifest))
        with pytest.raises(KeyError, match="Unknown method"):
            review(tmpdir)


@patch.object(_engine_mod, "litellm")
def test_compute_review_registry_dispatch(mock_litellm):
    """compute_review resolves prompt via registry when config.methods is set."""
    from impact_engine_evaluate.review.methods.experiment.reviewer import ExperimentReviewer
    from impact_engine_evaluate.review.prompt_registry import clear_prompt_registry, register_prompt

    mock_litellm.completion.return_value = _mock_litellm_completion()

    experiment_template = ExperimentReviewer().prompt_template_dir() / "experiment_review.yaml"
    register_prompt("custom_experiment_prompt", experiment_template)

    config = {"methods": {"experiment": {"prompt": "custom_experiment_prompt"}}}
    job_dir = _make_job_dir()
    result = compute_review(job_dir, config=config)

    assert result.overall_score == 0.80
    assert result.prompt_name == "experiment_review"

    clear_prompt_registry()
