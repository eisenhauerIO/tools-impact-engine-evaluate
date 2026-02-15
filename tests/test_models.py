"""Tests for review data models."""

from impact_engine_evaluate.review.models import (
    ArtifactPayload,
    PromptSpec,
    ReviewDimension,
    ReviewResult,
)


def test_artifact_payload_from_event():
    event = {
        "initiative_id": "init-001",
        "artifact_text": "Study using RCT with n=500",
        "model_type": "experiment",
        "sample_size": 500,
        "extra_field": "extra_value",
    }
    payload = ArtifactPayload.from_event(event)
    assert payload.initiative_id == "init-001"
    assert payload.artifact_text == "Study using RCT with n=500"
    assert payload.model_type == "experiment"
    assert payload.sample_size == 500
    assert payload.metadata == {"extra_field": "extra_value"}


def test_artifact_payload_from_event_minimal():
    event = {"initiative_id": "init-002", "artifact_text": "Some artifact"}
    payload = ArtifactPayload.from_event(event)
    assert payload.model_type == ""
    assert payload.sample_size == 0
    assert payload.metadata == {}


def test_review_dimension_fields():
    dim = ReviewDimension(name="internal_validity", score=0.85, justification="Strong design")
    assert dim.name == "internal_validity"
    assert dim.score == 0.85
    assert dim.justification == "Strong design"


def test_review_result_defaults():
    result = ReviewResult(
        initiative_id="init-001",
        prompt_name="test",
        prompt_version="1.0",
        backend_name="mock",
        model="mock-model",
    )
    assert result.dimensions == []
    assert result.overall_score == 0.0
    assert result.raw_response == ""
    assert result.timestamp == ""


def test_prompt_spec_defaults():
    spec = PromptSpec(name="test", version="1.0", description="A test prompt")
    assert spec.dimensions == []
    assert spec.system_template == ""
    assert spec.user_template == ""
