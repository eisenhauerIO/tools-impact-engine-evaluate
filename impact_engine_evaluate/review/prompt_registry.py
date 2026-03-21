"""Class-based registry for named prompt templates."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from impact_engine_evaluate.review.engine import PromptBuilder
from impact_engine_evaluate.review.models import PromptSpec

logger = logging.getLogger(__name__)

_METHODS_DIR = Path(__file__).parent / "methods"
_prompt_builder = PromptBuilder()


class Prompt(ABC):
    """Abstract base class for prompt template implementations.

    Subclass and implement :meth:`load` to provide custom prompt content
    from any source (filesystem, database, generated dynamically, etc.).
    """

    @abstractmethod
    def load(self) -> PromptSpec:
        """Return the prompt specification.

        Returns
        -------
        PromptSpec
        """


class FilePrompt(Prompt):
    """Prompt backed by a YAML template file.

    Parameters
    ----------
    path : str | Path
        Path to a YAML prompt template file.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> PromptSpec:
        """Load and return the :class:`PromptSpec` from the YAML file.

        Returns
        -------
        PromptSpec

        Raises
        ------
        FileNotFoundError
            If the path does not exist.
        """
        return _prompt_builder.load_spec(self._path)


class PromptRegistry:
    """Registry mapping names to :class:`Prompt` instances."""

    def __init__(self) -> None:
        self._registry: dict[str, Prompt] = {}
        self._defaults_loaded = False

    def _ensure_defaults(self) -> None:
        if not self._defaults_loaded:
            self.register(
                "experiment_review",
                FilePrompt(_METHODS_DIR / "experiment" / "prompts" / "experiment_review.yaml"),
            )
            self.register(
                "quasi_experimental_review",
                FilePrompt(_METHODS_DIR / "quasi_experimental" / "prompts" / "quasi_experimental_review.yaml"),
            )
            self._defaults_loaded = True

    def register(self, name: str, prompt: Prompt) -> None:
        """Register a prompt under *name*.

        Parameters
        ----------
        name : str
            Registry key used to look up this prompt.
        prompt : Prompt
            Prompt instance to register.
        """
        self._registry[name] = prompt
        logger.debug("Registered prompt %r", name)

    def load(self, name: str) -> PromptSpec:
        """Load the :class:`PromptSpec` registered under *name*.

        Parameters
        ----------
        name : str
            Registered prompt name.

        Returns
        -------
        PromptSpec

        Raises
        ------
        KeyError
            If *name* is not registered.
        """
        self._ensure_defaults()
        if name not in self._registry:
            available = ", ".join(sorted(self._registry)) or "(none)"
            msg = f"Prompt {name!r} not registered. Available: {available}"
            raise KeyError(msg)
        return self._registry[name].load()

    def list(self) -> list[str]:
        """Return sorted list of registered prompt names.

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


PROMPT_REGISTRY = PromptRegistry()
