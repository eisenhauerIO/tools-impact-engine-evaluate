"""Tests for the class-based knowledge base registry."""

import pytest

from impact_engine_evaluate.review.knowledge_registry import (
    KNOWLEDGE_BASE_REGISTRY,
    DirectoryKnowledgeBase,
    KnowledgeBase,
    KnowledgeBaseRegistry,
)


def setup_function():
    KNOWLEDGE_BASE_REGISTRY.clear()


def teardown_function():
    KNOWLEDGE_BASE_REGISTRY.clear()


def test_defaults_loaded_on_first_list():
    names = KNOWLEDGE_BASE_REGISTRY.list()
    assert "experiment" in names
    assert "quasi_experimental" in names


def test_defaults_loaded_on_first_load():
    content = KNOWLEDGE_BASE_REGISTRY.load("experiment")
    assert isinstance(content, str)
    assert len(content) > 0


def test_register_and_load_custom(tmp_path):
    kb_dir = tmp_path / "my_kb"
    kb_dir.mkdir()
    (kb_dir / "notes.md").write_text("# Custom knowledge\nSome content.", encoding="utf-8")
    KNOWLEDGE_BASE_REGISTRY.register("custom_kb", DirectoryKnowledgeBase(kb_dir))
    content = KNOWLEDGE_BASE_REGISTRY.load("custom_kb")
    assert "Custom knowledge" in content


def test_load_unknown_raises_key_error():
    KNOWLEDGE_BASE_REGISTRY.list()  # trigger defaults
    with pytest.raises(KeyError, match="not registered"):
        KNOWLEDGE_BASE_REGISTRY.load("no_such_kb_xyz")


def test_list_sorted():
    names = KNOWLEDGE_BASE_REGISTRY.list()
    assert names == sorted(names)


def test_empty_directory_returns_empty_string(tmp_path):
    kb_dir = tmp_path / "empty_kb"
    kb_dir.mkdir()
    KNOWLEDGE_BASE_REGISTRY.register("empty_kb", DirectoryKnowledgeBase(kb_dir))
    assert KNOWLEDGE_BASE_REGISTRY.load("empty_kb") == ""


def test_clear_resets_defaults(tmp_path):
    KNOWLEDGE_BASE_REGISTRY.list()  # trigger defaults
    KNOWLEDGE_BASE_REGISTRY.clear()
    kb_dir = tmp_path / "only_kb"
    kb_dir.mkdir()
    (kb_dir / "note.md").write_text("# Only entry", encoding="utf-8")
    KNOWLEDGE_BASE_REGISTRY.register("only_entry", DirectoryKnowledgeBase(kb_dir))
    names = KNOWLEDGE_BASE_REGISTRY.list()
    assert "only_entry" in names


def test_custom_knowledge_base_class():
    """Users can implement KnowledgeBase to serve content from any source."""

    class InMemoryKnowledgeBase(KnowledgeBase):
        def __init__(self, content: str) -> None:
            self._content = content

        def load(self) -> str:
            return self._content

    KNOWLEDGE_BASE_REGISTRY.register("in_memory", InMemoryKnowledgeBase("custom content"))
    assert KNOWLEDGE_BASE_REGISTRY.load("in_memory") == "custom content"


def test_separate_registry_instances_are_independent(tmp_path):
    """Two KnowledgeBaseRegistry instances do not share state."""
    registry_a = KnowledgeBaseRegistry()
    registry_b = KnowledgeBaseRegistry()
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    registry_a.register("shared_name", DirectoryKnowledgeBase(kb_dir))
    with pytest.raises(KeyError):
        registry_b.load("shared_name")
