"""Tests for knowledge base abstraction."""

import tempfile
from pathlib import Path

from impact_engine_evaluate.review.knowledge.base import Chunk
from impact_engine_evaluate.review.knowledge.static import StaticKnowledgeBase


def test_static_kb_loads_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "doc1.md").write_text("experiment design randomized control trial")
        Path(tmpdir, "doc2.txt").write_text("observational study cohort analysis")

        kb = StaticKnowledgeBase(tmpdir)
        chunks = kb.retrieve("randomized experiment", top_k=5)
        assert len(chunks) >= 1
        assert all(isinstance(c, Chunk) for c in chunks)


def test_static_kb_relevance_ordering():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "relevant.md").write_text("randomized control trial experiment design")
        Path(tmpdir, "irrelevant.md").write_text("unrelated topic about cooking recipes")

        kb = StaticKnowledgeBase(tmpdir)
        chunks = kb.retrieve("randomized experiment trial")
        assert len(chunks) >= 1
        assert "randomized" in chunks[0].content.lower()


def test_static_kb_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        kb = StaticKnowledgeBase(tmpdir)
        chunks = kb.retrieve("anything")
        assert chunks == []


def test_static_kb_nonexistent_dir():
    kb = StaticKnowledgeBase("/nonexistent/path/xyz")
    chunks = kb.retrieve("anything")
    assert chunks == []


def test_static_kb_top_k():
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(10):
            Path(tmpdir, f"doc{i}.md").write_text(f"common keyword document {i}")

        kb = StaticKnowledgeBase(tmpdir)
        chunks = kb.retrieve("common keyword", top_k=3)
        assert len(chunks) <= 3


def test_chunk_fields():
    chunk = Chunk(content="text", source="file.md", score=0.95)
    assert chunk.content == "text"
    assert chunk.source == "file.md"
    assert chunk.score == 0.95
