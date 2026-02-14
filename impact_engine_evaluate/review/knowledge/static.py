"""Static file-based knowledge base with keyword matching."""

from __future__ import annotations

import logging
from pathlib import Path

from impact_engine_evaluate.review.knowledge.base import Chunk, KnowledgeBase

logger = logging.getLogger(__name__)


class StaticKnowledgeBase(KnowledgeBase):
    """Knowledge base that loads ``.md`` and ``.txt`` files from a directory.

    Uses simple keyword overlap scoring (no external dependencies).

    Parameters
    ----------
    path : str | Path
        Directory containing knowledge files.
    """

    name = "static"

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._documents: list[tuple[str, str]] = []  # (source, content)
        self._load()

    def _load(self) -> None:
        """Load all .md and .txt files from the configured directory."""
        if not self._path.is_dir():
            logger.warning("Knowledge base path does not exist: %s", self._path)
            return
        for ext in ("*.md", "*.txt"):
            for filepath in sorted(self._path.glob(ext)):
                content = filepath.read_text(encoding="utf-8")
                self._documents.append((str(filepath), content))
                logger.debug("Loaded knowledge file: %s (%d chars)", filepath, len(content))

    def retrieve(self, query: str, *, top_k: int = 5) -> list[Chunk]:
        """Retrieve chunks by keyword overlap scoring.

        Parameters
        ----------
        query : str
            The search query.
        top_k : int
            Maximum number of chunks to return.

        Returns
        -------
        list[Chunk]
        """
        query_tokens = set(query.lower().split())
        if not query_tokens:
            return []

        scored: list[tuple[float, str, str]] = []
        for source, content in self._documents:
            doc_tokens = set(content.lower().split())
            overlap = len(query_tokens & doc_tokens)
            if overlap > 0:
                score = overlap / len(query_tokens)
                scored.append((score, source, content))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [Chunk(content=content, source=source, score=score) for score, source, content in scored[:top_k]]
