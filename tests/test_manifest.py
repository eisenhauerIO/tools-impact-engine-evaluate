"""Tests for manifest loading, validation, and update."""

import json
import tempfile
from pathlib import Path

import pytest

from impact_engine_evaluate.review.manifest import FileEntry, Manifest, load_manifest

SAMPLE_MANIFEST = {
    "schema_version": "2.0",
    "model_type": "experiment",
    "created_at": "2025-06-01T12:00:00+00:00",
    "files": {
        "impact_results": {"path": "impact_results.json", "format": "json"},
        "config": {"path": "config.yaml", "format": "yaml"},
    },
}


def _write_manifest(tmpdir, data):
    manifest_path = Path(tmpdir) / "manifest.json"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    return manifest_path


def test_load_manifest():
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_manifest(tmpdir, SAMPLE_MANIFEST)
        manifest = load_manifest(tmpdir)

        assert manifest.schema_version == "2.0"
        assert manifest.model_type == "experiment"
        assert manifest.created_at == "2025-06-01T12:00:00+00:00"
        assert "impact_results" in manifest.files
        assert manifest.files["impact_results"].path == "impact_results.json"
        assert manifest.files["impact_results"].format == "json"


def test_load_manifest_derives_initiative_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_manifest(tmpdir, SAMPLE_MANIFEST)
        manifest = load_manifest(tmpdir)
        # initiative_id defaults to directory name when not in manifest
        assert manifest.initiative_id == Path(tmpdir).name


def test_load_manifest_explicit_initiative_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        data = {**SAMPLE_MANIFEST, "initiative_id": "init-explicit"}
        _write_manifest(tmpdir, data)
        manifest = load_manifest(tmpdir)
        assert manifest.initiative_id == "init-explicit"


def test_load_manifest_missing_file():
    with pytest.raises(FileNotFoundError, match="Manifest not found"):
        load_manifest("/nonexistent/path/xyz")


def test_load_manifest_missing_required_field():
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_manifest(tmpdir, {"schema_version": "2.0"})
        with pytest.raises(ValueError, match="model_type"):
            load_manifest(tmpdir)


def test_file_entry_fields():
    entry = FileEntry(path="results.json", format="json")
    assert entry.path == "results.json"
    assert entry.format == "json"


def test_manifest_defaults():
    manifest = Manifest(schema_version="2.0", model_type="experiment")
    assert manifest.created_at == ""
    assert manifest.files == {}
    assert manifest.initiative_id == ""
    assert manifest.evaluate_strategy == "review"


def test_load_manifest_evaluate_strategy():
    """Explicit evaluate_strategy is read from manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data = {**SAMPLE_MANIFEST, "evaluate_strategy": "score"}
        _write_manifest(tmpdir, data)
        manifest = load_manifest(tmpdir)
        assert manifest.evaluate_strategy == "score"


def test_load_manifest_evaluate_strategy_default():
    """Missing evaluate_strategy defaults to review."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_manifest(tmpdir, SAMPLE_MANIFEST)
        manifest = load_manifest(tmpdir)
        assert manifest.evaluate_strategy == "review"
