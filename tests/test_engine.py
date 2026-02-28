"""Tests for ReviewEngine."""

from unittest.mock import MagicMock, patch

from impact_engine_evaluate.review import engine as _engine_mod
from impact_engine_evaluate.review.engine import ReviewEngine, render
from impact_engine_evaluate.review.models import (
    ArtifactPayload,
    DimensionResponse,
    PromptSpec,
    ReviewResponse,
)

SAMPLE_PARSED = ReviewResponse(
    dimensions=[
        DimensionResponse(name="internal_validity", score=0.85, justification="Strong randomized design."),
        DimensionResponse(name="external_validity", score=0.70, justification="Limited to one geographic region."),
        DimensionResponse(name="statistical_power", score=0.90, justification="Large sample size (n=500)."),
    ],
    overall=0.82,
)

SAMPLE_SPEC = PromptSpec(
    name="study_design_review",
    version="1.0",
    description="Review study design quality",
    dimensions=["internal_validity", "external_validity", "statistical_power"],
    system_template="You are a reviewer.\n{% if knowledge_context %}Use: {{ knowledge_context }}{% endif %}",
    user_template="Review: {{ artifact }}\nModel: {{ model_type }}\nSample: {{ sample_size }}",
)


# -- Render tests ------------------------------------------------------------


def test_render_basic():
    spec = PromptSpec(
        name="test",
        version="1.0",
        description="Test",
        system_template="You are a {{ role }}.",
        user_template="Review: {{ artifact }}",
    )
    messages = render(spec, {"role": "reviewer", "artifact": "study text"})
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "reviewer" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "study text" in messages[1]["content"]


def test_render_empty_templates():
    spec = PromptSpec(name="empty", version="1.0", description="Empty")
    messages = render(spec, {})
    assert messages == []


def test_render_system_only():
    spec = PromptSpec(
        name="sys",
        version="1.0",
        description="System only",
        system_template="Hello {{ name }}",
    )
    messages = render(spec, {"name": "world"})
    assert len(messages) == 1
    assert messages[0]["role"] == "system"


# -- Engine integration tests ------------------------------------------------


@patch.object(_engine_mod, "litellm")
def test_engine_review(mock_litellm):
    mock_litellm.completion.return_value.choices = [
        MagicMock(message=MagicMock(parsed=SAMPLE_PARSED, content=SAMPLE_PARSED.model_dump_json()))
    ]

    engine = ReviewEngine(default_model="mock-model")
    payload = ArtifactPayload(
        initiative_id="init-test",
        artifact_text="RCT with 500 participants in Kenya",
        model_type="experiment",
        sample_size=500,
    )
    result = engine.review(payload, SAMPLE_SPEC)

    assert result.initiative_id == "init-test"
    assert result.prompt_name == "study_design_review"
    assert result.backend_name == "litellm"
    assert len(result.dimensions) == 3
    assert result.overall_score == 0.82
    assert result.timestamp


@patch.object(_engine_mod, "litellm")
def test_engine_review_with_knowledge(mock_litellm):
    mock_litellm.completion.return_value.choices = [
        MagicMock(message=MagicMock(parsed=SAMPLE_PARSED, content=SAMPLE_PARSED.model_dump_json()))
    ]

    engine = ReviewEngine(default_model="mock-model")
    payload = ArtifactPayload(
        initiative_id="init-test-kb",
        artifact_text="RCT data",
        model_type="experiment",
    )
    result = engine.review(payload, SAMPLE_SPEC, knowledge_context="RCT fundamentals...")
    assert result.prompt_name == "study_design_review"
    assert len(result.dimensions) == 3
