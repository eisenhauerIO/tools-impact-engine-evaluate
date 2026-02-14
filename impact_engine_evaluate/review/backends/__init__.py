"""LLM backend abstraction and registry."""

from impact_engine_evaluate.review.backends.base import Backend, BackendRegistry

__all__ = ["Backend", "BackendRegistry"]

# Auto-register concrete backends that are importable.
# Each module registers itself via @BackendRegistry.register on import.


def _auto_register() -> None:
    """Import concrete backends, silently skipping missing dependencies."""
    import importlib

    for mod in ("anthropic_backend", "openai_backend", "litellm_backend"):
        try:
            importlib.import_module(f"impact_engine_evaluate.review.backends.{mod}")
        except ImportError:
            pass


_auto_register()
