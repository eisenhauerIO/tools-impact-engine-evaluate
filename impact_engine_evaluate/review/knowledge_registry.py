"""Registry for named knowledge base directories."""

from __future__ import annotations

import logging
from pathlib import Path

from impact_engine_evaluate.review.engine import load_knowledge

logger = logging.getLogger(__name__)

_METHODS_DIR = Path(__file__).parent / "methods"
_registry: dict[str, Path] = {}
_defaults_loaded = False


def _ensure_defaults_loaded() -> None:
    """Lazily register built-in knowledge base directories on first access."""
    global _defaults_loaded
    if not _defaults_loaded:
        _registry["experiment"] = _METHODS_DIR / "experiment" / "knowledge"
        _registry["quasi_experimental"] = _METHODS_DIR / "quasi_experimental" / "knowledge"
        _defaults_loaded = True


def register_knowledge_base(name: str, directory: str | Path) -> None:
    """Register a knowledge base directory under *name*.

    Parameters
    ----------
    name : str
        Registry key used to look up this knowledge base.
    directory : str | Path
        Path to a directory containing ``.md`` or ``.txt`` knowledge files.
    """
    _registry[name] = Path(directory)
    logger.debug("Registered knowledge base %r → %s", name, directory)


def load_knowledge_base(name: str) -> str:
    """Load and return concatenated knowledge content registered under *name*.

    Parameters
    ----------
    name : str
        Registered knowledge base name.

    Returns
    -------
    str
        Combined content of all ``.md`` and ``.txt`` files in the directory.

    Raises
    ------
    KeyError
        If *name* is not registered.
    """
    _ensure_defaults_loaded()
    if name not in _registry:
        available = ", ".join(sorted(_registry)) or "(none)"
        msg = f"Knowledge base {name!r} not registered. Available: {available}"
        raise KeyError(msg)
    return load_knowledge(_registry[name])


def list_knowledge_bases() -> list[str]:
    """Return sorted list of registered knowledge base names.

    Returns
    -------
    list[str]
    """
    _ensure_defaults_loaded()
    return sorted(_registry)


def clear_knowledge_registry() -> None:
    """Reset the registry and defaults flag.

    Intended for use in tests to ensure a clean state.
    """
    global _defaults_loaded
    _registry.clear()
    _defaults_loaded = False
