"""Tests for the shared job directory reader."""

import json
import tempfile
from pathlib import Path

import pytest

from impact_engine_evaluate.job_reader import load_scorer_event
from impact_engine_evaluate.review.manifest import Manifest


def _make_job_dir(results_data):
    """Create a temporary job directory with impact_results.json."""
    tmpdir = tempfile.mkdtemp(prefix="job-reader-test-")
    Path(tmpdir, "impact_results.json").write_text(json.dumps(results_data))
    return tmpdir


def test_load_scorer_event_happy_path():
    """Reads fields from impact_results.json and combines with manifest."""
    results = {
        "ci_upper": 15.0,
        "effect_estimate": 10.0,
        "ci_lower": 5.0,
        "cost_to_scale": 100.0,
        "sample_size": 50,
    }
    tmpdir = _make_job_dir(results)
    manifest = Manifest(
        model_type="experiment",
        initiative_id="init-reader-test",
    )

    event = load_scorer_event(manifest, tmpdir)

    assert event["initiative_id"] == "init-reader-test"
    assert event["model_type"] == "experiment"
    assert event["ci_upper"] == 15.0
    assert event["effect_estimate"] == 10.0
    assert event["ci_lower"] == 5.0
    assert event["cost_to_scale"] == 100.0
    assert event["sample_size"] == 50


def test_load_scorer_event_overrides():
    """Overrides dict takes precedence over impact_results.json values."""
    results = {"ci_upper": 1.0, "effect_estimate": 0.5, "ci_lower": 0.0, "cost_to_scale": 10.0, "sample_size": 10}
    tmpdir = _make_job_dir(results)
    manifest = Manifest(model_type="experiment", initiative_id="init-override")

    event = load_scorer_event(manifest, tmpdir, overrides={"cost_to_scale": 999.0})

    assert event["cost_to_scale"] == 999.0
    # Other fields unchanged
    assert event["ci_upper"] == 1.0


def test_load_scorer_event_missing_file():
    """Missing impact_results.json raises FileNotFoundError."""
    tmpdir = tempfile.mkdtemp(prefix="job-reader-missing-")
    manifest = Manifest(model_type="experiment")

    with pytest.raises(FileNotFoundError, match="Impact results not found"):
        load_scorer_event(manifest, tmpdir)


def test_load_scorer_event_defaults_missing_fields():
    """Missing fields in impact_results.json default to zero."""
    tmpdir = _make_job_dir({})
    manifest = Manifest(model_type="experiment", initiative_id="init-defaults")

    event = load_scorer_event(manifest, tmpdir)

    assert event["ci_upper"] == 0.0
    assert event["effect_estimate"] == 0.0
    assert event["ci_lower"] == 0.0
    assert event["cost_to_scale"] == 0.0
    assert event["sample_size"] == 0


def test_load_scorer_event_initiative_from_dirname():
    """When manifest has no initiative_id, falls back to directory name."""
    results = {"ci_upper": 1.0, "effect_estimate": 0.5, "ci_lower": 0.0, "cost_to_scale": 10.0, "sample_size": 10}
    tmpdir = _make_job_dir(results)
    manifest = Manifest(model_type="experiment")

    event = load_scorer_event(manifest, tmpdir)

    assert event["initiative_id"] == Path(tmpdir).name
