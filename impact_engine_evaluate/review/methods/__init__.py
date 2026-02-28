"""Method reviewer registry and built-in methods."""

from impact_engine_evaluate.review.methods.base import MethodReviewer, MethodReviewerRegistry

__all__ = ["MethodReviewer", "MethodReviewerRegistry"]

# Auto-register built-in method reviewers on import.


def _auto_register() -> None:
    """Import built-in methods, triggering their registration decorators."""
    import importlib

    for mod in ("experiment",):
        try:
            importlib.import_module(f"impact_engine_evaluate.review.methods.{mod}")
        except ImportError:
            pass


_auto_register()
