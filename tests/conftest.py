"""Shared fixtures for evaluate tests."""

import json

import pytest


@pytest.fixture()
def sample_scorer_event():
    """Scorer event with flat string model_type."""
    return {
        "initiative_id": "init-001",
        "model_type": "experiment",
        "ci_upper": 15.0,
        "effect_estimate": 10.0,
        "ci_lower": 5.0,
        "cost_to_scale": 100.0,
        "sample_size": 50,
    }


@pytest.fixture()
def score_job_dir(tmp_path):
    """Job directory configured for score evaluation."""
    manifest = {
        "model_type": "experiment",
        "evaluate_strategy": "score",
        "created_at": "2025-06-01T12:00:00+00:00",
        "files": {
            "impact_results": {"path": "impact_results.json", "format": "json"},
        },
    }
    results = {
        "ci_upper": 15.0,
        "effect_estimate": 10.0,
        "ci_lower": 5.0,
        "cost_to_scale": 100.0,
        "sample_size": 50,
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "impact_results.json").write_text(json.dumps(results))
    return tmp_path


@pytest.fixture()
def review_job_dir(tmp_path):
    """Job directory configured for review evaluation."""
    job_dir = tmp_path / "review"
    job_dir.mkdir()
    manifest = {
        "model_type": "experiment",
        "evaluate_strategy": "review",
        "created_at": "2025-06-01T12:00:00+00:00",
        "files": {
            "impact_results": {"path": "impact_results.json", "format": "json"},
        },
    }
    results = {
        "ci_upper": 15.0,
        "effect_estimate": 10.0,
        "ci_lower": 5.0,
        "cost_to_scale": 100.0,
        "sample_size": 50,
    }
    (job_dir / "manifest.json").write_text(json.dumps(manifest))
    (job_dir / "impact_results.json").write_text(json.dumps(results))
    return job_dir
