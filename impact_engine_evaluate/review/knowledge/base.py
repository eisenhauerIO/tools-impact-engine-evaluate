"""Abstract knowledge base protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Chunk:
    """A retrieved knowledge chunk.

    Parameters
    ----------
    content : str
        The text content of the chunk.
    source : str
        Origin identifier (e.g. file path, URL).
    score : float | None
        Relevance score, if available.
    """

    content: str
    source: str
    score: float | None = None


class KnowledgeBase(ABC):
    """Retrieval interface for domain knowledge."""

    name: str = ""

    @abstractmethod
    def retrieve(self, query: str, *, top_k: int = 5) -> list[Chunk]:
        """Return relevant chunks for the query.

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
