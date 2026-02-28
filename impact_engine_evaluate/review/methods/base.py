"""Abstract method reviewer and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from impact_engine_evaluate.review.manifest import Manifest
from impact_engine_evaluate.review.models import ArtifactPayload


class MethodReviewer(ABC):
    """Base class for methodology-specific artifact reviewers.

    Each method reviewer bundles its own prompt template, knowledge base
    content, and artifact loading logic.

    Attributes
    ----------
    name : str
        Registry key (e.g. ``"experiment"``).
    prompt_name : str
        Filename stem of the prompt template YAML.
    description : str
        Human-readable description of the methodology.
    """

    name: str = ""
    prompt_name: str = ""
    description: str = ""

    @abstractmethod
    def load_artifact(self, manifest: Manifest, job_dir: Path) -> ArtifactPayload:
        """Read artifact files per manifest and return a payload.

        Parameters
        ----------
        manifest : Manifest
            Parsed job manifest.
        job_dir : Path
            Path to the job directory.

        Returns
        -------
        ArtifactPayload
        """

    def prompt_template_dir(self) -> Path | None:
        """Directory containing this reviewer's YAML prompt templates.

        Returns
        -------
        Path | None
            ``None`` means no method-specific templates.
        """
        return None

    def knowledge_content_dir(self) -> Path | None:
        """Directory containing this reviewer's knowledge files.

        Returns
        -------
        Path | None
            ``None`` means no method-specific knowledge.
        """
        return None


class MethodReviewerRegistry:
    """Discover and instantiate registered method reviewers."""

    _methods: dict[str, type[MethodReviewer]] = {}

    @classmethod
    def register(cls, name: str):
        """Class decorator that registers a method reviewer under *name*.

        Parameters
        ----------
        name : str
            Lookup key (typically the ``model_type`` value from manifests).

        Returns
        -------
        Callable
            The original class, unmodified.
        """

        def decorator(klass: type[MethodReviewer]) -> type[MethodReviewer]:
            cls._methods[name] = klass
            return klass

        return decorator

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> MethodReviewer:
        """Instantiate a registered method reviewer.

        Parameters
        ----------
        name : str
            Registered method name.
        **kwargs
            Forwarded to the reviewer constructor.

        Returns
        -------
        MethodReviewer

        Raises
        ------
        KeyError
            If *name* is not registered.
        """
        if name not in cls._methods:
            available = ", ".join(sorted(cls._methods)) or "(none)"
            msg = f"Unknown method {name!r}. Available: {available}"
            raise KeyError(msg)
        return cls._methods[name](**kwargs)

    @classmethod
    def available(cls) -> list[str]:
        """Return sorted list of registered method names."""
        return sorted(cls._methods)
