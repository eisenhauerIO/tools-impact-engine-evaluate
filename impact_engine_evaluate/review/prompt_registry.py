"""Registry for named prompt template YAML files."""

from __future__ import annotations

import logging
from pathlib import Path

from impact_engine_evaluate.review.engine import load_prompt_spec
from impact_engine_evaluate.review.models import PromptSpec

logger = logging.getLogger(__name__)

_METHODS_DIR = Path(__file__).parent / "methods"
_registry: dict[str, Path] = {}
_defaults_loaded = False


def _ensure_defaults_loaded() -> None:
    """Lazily register built-in prompt templates on first access."""
    global _defaults_loaded
    if not _defaults_loaded:
        _registry["experiment_review"] = _METHODS_DIR / "experiment" / "templates" / "experiment_review.yaml"
        _registry["quasi_experimental_review"] = (
            _METHODS_DIR / "quasi_experimental" / "templates" / "quasi_experimental_review.yaml"
        )
        _defaults_loaded = True


def register_prompt(name: str, path: str | Path) -> None:
    """Register a prompt YAML file under *name*.

    Parameters
    ----------
    name : str
        Registry key used to look up this prompt.
    path : str | Path
        Path to a YAML prompt template file.
    """
    _registry[name] = Path(path)
    logger.debug("Registered prompt %r → %s", name, path)


def load_prompt(name: str) -> PromptSpec:
    """Load and return the PromptSpec registered under *name*.

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
    _ensure_defaults_loaded()
    if name not in _registry:
        available = ", ".join(sorted(_registry)) or "(none)"
        msg = f"Prompt {name!r} not registered. Available: {available}"
        raise KeyError(msg)
    return load_prompt_spec(_registry[name])


def list_prompts() -> list[str]:
    """Return sorted list of registered prompt names.

    Returns
    -------
    list[str]
    """
    _ensure_defaults_loaded()
    return sorted(_registry)


def clear_prompt_registry() -> None:
    """Reset the registry and defaults flag.

    Intended for use in tests to ensure a clean state.
    """
    global _defaults_loaded
    _registry.clear()
    _defaults_loaded = False
