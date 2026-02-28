"""Abstract method reviewer and registry."""

from __future__ import annotations

import json
import logging
from abc import ABC
from pathlib import Path
from typing import Any

from impact_engine_evaluate.review.manifest import Manifest
from impact_engine_evaluate.review.models import ArtifactPayload

logger = logging.getLogger(__name__)


class MethodReviewer(ABC):
    """Base class for methodology-specific artifact reviewers.

    Each method reviewer bundles its own prompt template, knowledge base
    content, and artifact loading logic.  The default ``load_artifact``
    reads all files listed in the manifest and attempts to extract
    ``sample_size`` from the first JSON file.  Subclasses may override
    if they need method-specific loading.

    Attributes
    ----------
    name : str
        Registry key (e.g. ``"experiment"``).
    prompt_name : str
        Filename stem of the prompt template YAML.
    description : str
        Human-readable description of the methodology.
    confidence_range : tuple[float, float]
        ``(lower, upper)`` bounds for deterministic confidence scoring.
    """

    name: str = ""
    prompt_name: str = ""
    description: str = ""
    confidence_range: tuple[float, float] = (0.0, 0.0)

    def load_artifact(self, manifest: Manifest, job_dir: Path) -> ArtifactPayload:
        """Read artifact files per manifest and return a payload.

        The default implementation reads every file entry in *manifest*,
        concatenates their contents, and extracts ``sample_size`` from the
        first JSON file that contains one.  Subclasses may override for
        method-specific loading.

        Parameters
        ----------
        manifest : Manifest
            Parsed job manifest.
        job_dir : Path
            Path to the job directory.

        Returns
        -------
        ArtifactPayload

        Raises
        ------
        ValueError
            If the manifest contains no file entries.
        """
        if not manifest.files:
            msg = "Manifest contains no file entries"
            raise ValueError(msg)

        parts: list[str] = []
        sample_size = 0

        for name, entry in manifest.files.items():
            path = job_dir / entry.path
            if not path.exists():
                logger.warning("Artifact file not found: %s", path)
                continue
            content = path.read_text(encoding="utf-8")
            parts.append(f"=== {name} ({entry.format}) ===\n{content}")

            # Try to extract sample_size from JSON results
            if entry.format == "json" and sample_size == 0:
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        sample_size = int(data.get("sample_size", 0))
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

        artifact_text = "\n\n".join(parts)
        initiative_id = manifest.initiative_id or job_dir.name

        return ArtifactPayload(
            initiative_id=initiative_id,
            artifact_text=artifact_text,
            model_type=manifest.model_type,
            sample_size=sample_size,
        )

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

    @classmethod
    def confidence_map(cls) -> dict[str, tuple[float, float]]:
        """Return ``{name: confidence_range}`` for all registered methods."""
        return {name: klass.confidence_range for name, klass in cls._methods.items()}
