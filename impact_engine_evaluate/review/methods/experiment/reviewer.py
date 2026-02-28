"""Experiment (RCT) method reviewer."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from impact_engine_evaluate.review.manifest import Manifest
from impact_engine_evaluate.review.methods.base import MethodReviewer, MethodReviewerRegistry
from impact_engine_evaluate.review.models import ArtifactPayload

logger = logging.getLogger(__name__)

_PKG_DIR = Path(__file__).parent


@MethodReviewerRegistry.register("experiment")
class ExperimentReviewer(MethodReviewer):
    """Review experimental (RCT) impact measurement artifacts.

    Evaluates randomization integrity, specification adequacy, statistical
    inference, threats to validity, and effect size plausibility.
    """

    name = "experiment"
    prompt_name = "experiment_review"
    description = "Review experimental (RCT) impact measurement artifacts."
    confidence_range = (0.85, 1.0)

    def load_artifact(self, manifest: Manifest, job_dir: Path) -> ArtifactPayload:
        """Read artifact files from the job directory.

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

    def prompt_template_dir(self) -> Path:
        """Return the experiment-specific templates directory."""
        return _PKG_DIR / "templates"

    def knowledge_content_dir(self) -> Path:
        """Return the experiment-specific knowledge directory."""
        return _PKG_DIR / "knowledge"
