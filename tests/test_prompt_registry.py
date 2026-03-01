"""Tests for the prompt registry."""

import pytest

from impact_engine_evaluate.review.prompt_registry import (
    clear_prompt_registry,
    list_prompts,
    load_prompt,
    register_prompt,
)


def setup_function():
    clear_prompt_registry()


def teardown_function():
    clear_prompt_registry()


def test_clear_resets_defaults(tmp_path):
    # Load defaults, clear, register a single custom entry; it survives after clear.
    list_prompts()  # trigger defaults
    clear_prompt_registry()
    yaml_path = tmp_path / "only.yaml"
    yaml_path.write_text(
        "name: only\nversion: '1.0'\ndescription: ''\ndimensions: []\nsystem: ''\nuser: ''\n",
        encoding="utf-8",
    )
    register_prompt("only_entry", yaml_path)
    # list re-loads defaults AND includes the custom entry
    names = list_prompts()
    assert "only_entry" in names


def test_defaults_loaded_on_first_list():
    names = list_prompts()
    assert "experiment_review" in names
    assert "quasi_experimental_review" in names


def test_defaults_loaded_on_first_load():
    spec = load_prompt("experiment_review")
    assert spec.name == "experiment_review"


def test_register_and_load_custom(tmp_path):
    yaml_path = tmp_path / "custom.yaml"
    yaml_path.write_text(
        "name: custom\nversion: '1.0'\ndescription: Test\ndimensions:\n  - dim_a\nsystem: 'sys'\nuser: 'usr'\n",
        encoding="utf-8",
    )
    register_prompt("custom", yaml_path)
    spec = load_prompt("custom")
    assert spec.name == "custom"
    assert spec.dimensions == ["dim_a"]


def test_load_unknown_raises_key_error():
    list_prompts()  # trigger defaults
    with pytest.raises(KeyError, match="not registered"):
        load_prompt("no_such_prompt_xyz")


def test_list_prompts_sorted():
    names = list_prompts()
    assert names == sorted(names)


def test_register_overwrites_existing(tmp_path):
    yaml_a = tmp_path / "a.yaml"
    yaml_b = tmp_path / "b.yaml"
    for p, name in ((yaml_a, "version_a"), (yaml_b, "version_b")):
        p.write_text(
            f"name: {name}\nversion: '1.0'\ndescription: ''\ndimensions: []\nsystem: ''\nuser: ''\n",
            encoding="utf-8",
        )
    register_prompt("overwrite_test", yaml_a)
    register_prompt("overwrite_test", yaml_b)
    spec = load_prompt("overwrite_test")
    assert spec.name == "version_b"
