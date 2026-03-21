"""Tests for the class-based prompt registry."""

import pytest

from impact_engine_evaluate.review.models import PromptSpec
from impact_engine_evaluate.review.prompt_registry import (
    PROMPT_REGISTRY,
    FilePrompt,
    Prompt,
    PromptRegistry,
)


def setup_function():
    PROMPT_REGISTRY.clear()


def teardown_function():
    PROMPT_REGISTRY.clear()


def test_defaults_loaded_on_first_list():
    names = PROMPT_REGISTRY.list()
    assert "experiment_review" in names
    assert "quasi_experimental_review" in names


def test_defaults_loaded_on_first_load():
    spec = PROMPT_REGISTRY.load("experiment_review")
    assert spec.name == "experiment_review"


def test_register_and_load_custom(tmp_path):
    yaml_path = tmp_path / "custom.yaml"
    yaml_path.write_text(
        "name: custom\nversion: '1.0'\ndescription: Test\ndimensions:\n  - dim_a\nsystem: 'sys'\nuser: 'usr'\n",
        encoding="utf-8",
    )
    PROMPT_REGISTRY.register("custom", FilePrompt(yaml_path))
    spec = PROMPT_REGISTRY.load("custom")
    assert spec.name == "custom"
    assert spec.dimensions == ["dim_a"]


def test_load_unknown_raises_key_error():
    PROMPT_REGISTRY.list()  # trigger defaults
    with pytest.raises(KeyError, match="not registered"):
        PROMPT_REGISTRY.load("no_such_prompt_xyz")


def test_list_sorted():
    names = PROMPT_REGISTRY.list()
    assert names == sorted(names)


def test_register_overwrites_existing(tmp_path):
    yaml_a = tmp_path / "a.yaml"
    yaml_b = tmp_path / "b.yaml"
    for p, name in ((yaml_a, "version_a"), (yaml_b, "version_b")):
        p.write_text(
            f"name: {name}\nversion: '1.0'\ndescription: ''\ndimensions: []\nsystem: ''\nuser: ''\n",
            encoding="utf-8",
        )
    PROMPT_REGISTRY.register("overwrite_test", FilePrompt(yaml_a))
    PROMPT_REGISTRY.register("overwrite_test", FilePrompt(yaml_b))
    spec = PROMPT_REGISTRY.load("overwrite_test")
    assert spec.name == "version_b"


def test_clear_resets_defaults(tmp_path):
    PROMPT_REGISTRY.list()  # trigger defaults
    PROMPT_REGISTRY.clear()
    yaml_path = tmp_path / "only.yaml"
    yaml_path.write_text(
        "name: only\nversion: '1.0'\ndescription: ''\ndimensions: []\nsystem: ''\nuser: ''\n",
        encoding="utf-8",
    )
    PROMPT_REGISTRY.register("only_entry", FilePrompt(yaml_path))
    names = PROMPT_REGISTRY.list()
    assert "only_entry" in names


def test_custom_prompt_class():
    """Users can implement Prompt to serve content from any source."""

    class InMemoryPrompt(Prompt):
        def load(self) -> PromptSpec:
            return PromptSpec(
                name="in_memory",
                version="1.0",
                description="",
                dimensions=[],
                system_template="",
                user_template="",
            )

    PROMPT_REGISTRY.register("in_memory", InMemoryPrompt())
    spec = PROMPT_REGISTRY.load("in_memory")
    assert spec.name == "in_memory"


def test_separate_registry_instances_are_independent(tmp_path):
    """Two PromptRegistry instances do not share state."""
    registry_a = PromptRegistry()
    registry_b = PromptRegistry()
    yaml_path = tmp_path / "p.yaml"
    yaml_path.write_text(
        "name: test\nversion: '1.0'\ndescription: ''\ndimensions: []\nsystem: ''\nuser: ''\n",
        encoding="utf-8",
    )
    registry_a.register("test", FilePrompt(yaml_path))
    with pytest.raises(KeyError):
        registry_b.load("test")
