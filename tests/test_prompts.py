"""Tests for prompt registry, rendering, and built-in templates."""

import pytest

from impact_engine_evaluate.review.models import PromptSpec
from impact_engine_evaluate.review.prompts.registry import PromptRegistry
from impact_engine_evaluate.review.prompts.renderer import render


def test_builtin_templates_loaded():
    registry = PromptRegistry()
    available = registry.available()
    assert "study_design_review" in available
    assert "data_quality_review" in available


def test_get_known_prompt():
    registry = PromptRegistry()
    spec = registry.get("study_design_review")
    assert spec.name == "study_design_review"
    assert spec.version == "1.0"
    assert "internal_validity" in spec.dimensions
    assert spec.system_template
    assert spec.user_template


def test_get_unknown_raises():
    registry = PromptRegistry()
    with pytest.raises(KeyError, match="Unknown prompt"):
        registry.get("nonexistent_prompt_xyz")


def test_register_programmatic():
    registry = PromptRegistry()
    spec = PromptSpec(name="custom", version="2.0", description="Custom prompt")
    registry.register(spec)
    assert registry.get("custom").version == "2.0"


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
