"""Tests for the knowledge registry."""

import pytest

from impact_engine_evaluate.review.knowledge_registry import (
    clear_knowledge_registry,
    list_knowledge_bases,
    load_knowledge_base,
    register_knowledge_base,
)


def setup_function():
    clear_knowledge_registry()


def teardown_function():
    clear_knowledge_registry()


def test_clear_resets_defaults(tmp_path):
    # Load defaults, clear, register a single custom entry; it survives after clear.
    list_knowledge_bases()  # trigger defaults
    clear_knowledge_registry()
    kb_dir = tmp_path / "only_kb"
    kb_dir.mkdir()
    (kb_dir / "note.md").write_text("# Only entry", encoding="utf-8")
    register_knowledge_base("only_entry", kb_dir)
    # list re-loads defaults AND includes the custom entry
    names = list_knowledge_bases()
    assert "only_entry" in names


def test_defaults_loaded_on_first_list():
    names = list_knowledge_bases()
    assert "experiment" in names
    assert "quasi_experimental" in names


def test_defaults_loaded_on_first_load():
    content = load_knowledge_base("experiment")
    assert isinstance(content, str)
    assert len(content) > 0


def test_register_and_load_custom(tmp_path):
    kb_dir = tmp_path / "my_kb"
    kb_dir.mkdir()
    (kb_dir / "notes.md").write_text("# Custom knowledge\nSome content.", encoding="utf-8")
    register_knowledge_base("custom_kb", kb_dir)
    content = load_knowledge_base("custom_kb")
    assert "Custom knowledge" in content


def test_load_unknown_raises_key_error():
    list_knowledge_bases()  # trigger defaults
    with pytest.raises(KeyError, match="not registered"):
        load_knowledge_base("no_such_kb_xyz")


def test_list_knowledge_bases_sorted():
    names = list_knowledge_bases()
    assert names == sorted(names)


def test_empty_directory_returns_empty_string(tmp_path):
    kb_dir = tmp_path / "empty_kb"
    kb_dir.mkdir()
    register_knowledge_base("empty_kb", kb_dir)
    assert load_knowledge_base("empty_kb") == ""
