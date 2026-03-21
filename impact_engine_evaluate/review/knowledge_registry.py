"""Class-based registry for named knowledge bases."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from impact_engine_evaluate.review.engine import PromptBuilder

logger = logging.getLogger(__name__)

_METHODS_DIR = Path(__file__).parent / "methods"
_prompt_builder = PromptBuilder()


class KnowledgeBase(ABC):
    """Abstract base class for knowledge base implementations.

    Subclass and implement :meth:`load` to provide custom knowledge base
    content from any source (filesystem, database, API, etc.).
    """

    @abstractmethod
    def load(self) -> str:
        """Return the knowledge base content as a string.

        Returns
        -------
        str
            Combined knowledge content.
        """


class DirectoryKnowledgeBase(KnowledgeBase):
    """Knowledge base backed by a directory of ``.md`` and ``.txt`` files.

    Parameters
    ----------
    directory : str | Path
        Path to a directory containing ``.md`` or ``.txt`` knowledge files.
    """

    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)

    def load(self) -> str:
        """Return concatenated content of all ``.md`` and ``.txt`` files in the directory.

        Returns
        -------
        str
            Combined content separated by section dividers.
        """
        return _prompt_builder.load_knowledge(self._directory)


class KnowledgeBaseRegistry:
    """Registry mapping names to :class:`KnowledgeBase` instances."""

    def __init__(self) -> None:
        self._registry: dict[str, KnowledgeBase] = {}
        self._defaults_loaded = False

    def _ensure_defaults(self) -> None:
        if not self._defaults_loaded:
            self.register("experiment", DirectoryKnowledgeBase(_METHODS_DIR / "experiment" / "knowledge"))
            self.register(
                "quasi_experimental",
                DirectoryKnowledgeBase(_METHODS_DIR / "quasi_experimental" / "knowledge"),
            )
            self._defaults_loaded = True

    def register(self, name: str, knowledge_base: KnowledgeBase) -> None:
        """Register a knowledge base under *name*.

        Parameters
        ----------
        name : str
            Registry key used to look up this knowledge base.
        knowledge_base : KnowledgeBase
            Knowledge base instance to register.
        """
        self._registry[name] = knowledge_base
        logger.debug("Registered knowledge base %r", name)

    def load(self, name: str) -> str:
        """Load content from the knowledge base registered under *name*.

        Parameters
        ----------
        name : str
            Registered knowledge base name.

        Returns
        -------
        str
            Combined knowledge content.

        Raises
        ------
        KeyError
            If *name* is not registered.
        """
        self._ensure_defaults()
        if name not in self._registry:
            available = ", ".join(sorted(self._registry)) or "(none)"
            msg = f"Knowledge base {name!r} not registered. Available: {available}"
            raise KeyError(msg)
        return self._registry[name].load()

    def list(self) -> list[str]:
        """Return sorted list of registered knowledge base names.

        Returns
        -------
        list[str]
        """
        self._ensure_defaults()
        return sorted(self._registry)

    def clear(self) -> None:
        """Reset the registry and defaults flag.

        Intended for use in tests to ensure a clean state.
        """
        self._registry.clear()
        self._defaults_loaded = False


KNOWLEDGE_BASE_REGISTRY = KnowledgeBaseRegistry()
