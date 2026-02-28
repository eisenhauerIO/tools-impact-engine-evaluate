"""Experiment (RCT) method reviewer."""

from __future__ import annotations

from pathlib import Path

from impact_engine_evaluate.review.methods.base import MethodReviewer, MethodReviewerRegistry

_PKG_DIR = Path(__file__).parent


@MethodReviewerRegistry.register("experiment")
class ExperimentReviewer(MethodReviewer):
    """Review experimental (RCT) impact measurement artifacts.

    Evaluates randomization integrity, specification adequacy, statistical
    inference, threats to validity, and effect size plausibility.

    Artifact loading uses the default base-class implementation (reads all
    manifest files, extracts ``sample_size`` from JSON).
    """

    name = "experiment"
    prompt_name = "experiment_review"
    description = "Review experimental (RCT) impact measurement artifacts."
    confidence_range = (0.85, 1.0)

    def prompt_template_dir(self) -> Path:
        """Return the experiment-specific templates directory."""
        return _PKG_DIR / "templates"

    def knowledge_content_dir(self) -> Path:
        """Return the experiment-specific knowledge directory."""
        return _PKG_DIR / "knowledge"
