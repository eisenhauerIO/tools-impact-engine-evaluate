"""Tests for the experiment method reviewer."""

import json
import tempfile
from pathlib import Path

import pytest

from impact_engine_evaluate.review.engine import load_knowledge, load_prompt_spec
from impact_engine_evaluate.review.manifest import FileEntry, Manifest
from impact_engine_evaluate.review.methods import MethodReviewerRegistry


@pytest.fixture()
def experiment_reviewer():
    return MethodReviewerRegistry.create("experiment")


@pytest.fixture()
def sample_job_dir():
    with tempfile.TemporaryDirectory(prefix="job-impact-engine-") as tmpdir:
        results = {
            "initiative_id": "init-exp-001",
            "model_type": "experiment",
            "effect_estimate": 5.2,
            "ci_lower": 2.1,
            "ci_upper": 8.3,
            "sample_size": 500,
        }
        Path(tmpdir, "impact_results.json").write_text(json.dumps(results))
        yield tmpdir


@pytest.fixture()
def sample_manifest():
    return Manifest(
        model_type="experiment",
        files={
            "impact_results": FileEntry(path="impact_results.json", format="json"),
        },
    )


def test_load_artifact(experiment_reviewer, sample_job_dir, sample_manifest):
    payload = experiment_reviewer.load_artifact(sample_manifest, Path(sample_job_dir))
    assert "impact_results" in payload.artifact_text
    assert payload.model_type == "experiment"
    assert payload.sample_size == 500


def test_load_artifact_initiative_from_manifest(experiment_reviewer, sample_job_dir):
    manifest = Manifest(
        model_type="experiment",
        initiative_id="init-explicit",
        files={
            "impact_results": FileEntry(path="impact_results.json", format="json"),
        },
    )
    payload = experiment_reviewer.load_artifact(manifest, Path(sample_job_dir))
    assert payload.initiative_id == "init-explicit"


def test_load_artifact_initiative_from_dir_name(experiment_reviewer, sample_job_dir, sample_manifest):
    payload = experiment_reviewer.load_artifact(sample_manifest, Path(sample_job_dir))
    assert payload.initiative_id == Path(sample_job_dir).name


def test_load_artifact_empty_manifest_raises(experiment_reviewer):
    manifest = Manifest(model_type="experiment", files={})
    with pytest.raises(ValueError, match="no file entries"):
        experiment_reviewer.load_artifact(manifest, Path("/tmp"))


def test_prompt_template_loads(experiment_reviewer):
    template_dir = experiment_reviewer.prompt_template_dir()
    spec = load_prompt_spec(template_dir / "experiment_review.yaml")
    assert spec.name == "experiment_review"
    assert "randomization_integrity" in spec.dimensions
    assert "effect_size_plausibility" in spec.dimensions
    assert len(spec.dimensions) == 5
    assert spec.system_template
    assert spec.user_template


def test_knowledge_loads(experiment_reviewer):
    knowledge_dir = experiment_reviewer.knowledge_content_dir()
    context = load_knowledge(knowledge_dir)
    assert "SUTVA" in context
    assert "attrition" in context.lower()
    assert "R-squared" in context


def test_load_prompt_spec_missing_file():
    with pytest.raises(FileNotFoundError, match="Prompt template not found"):
        load_prompt_spec(Path("/nonexistent/path/xyz.yaml"))
