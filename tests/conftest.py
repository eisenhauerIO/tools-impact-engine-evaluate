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
def deterministic_job_dir(tmp_path):
    """Job directory configured for deterministic evaluation."""
    manifest = {
        "schema_version": "2.0",
        "model_type": "experiment",
        "evaluate_strategy": "deterministic",
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
def agentic_job_dir(tmp_path):
    """Job directory configured for agentic evaluation."""
    job_dir = tmp_path / "agentic"
    job_dir.mkdir()
    manifest = {
        "schema_version": "2.0",
        "model_type": "experiment",
        "evaluate_strategy": "agentic",
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
