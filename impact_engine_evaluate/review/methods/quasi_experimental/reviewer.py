"""Quasi-experimental method reviewer."""

from __future__ import annotations

from pathlib import Path

from impact_engine_evaluate.review.methods.base import MethodReviewer, MethodReviewerRegistry

_PKG_DIR = Path(__file__).parent


@MethodReviewerRegistry.register("quasi_experimental")
class QuasiExperimentalReviewer(MethodReviewer):
    """Review quasi-experimental (DiD, RDD, IV) impact measurement artifacts.

    Evaluates identifying assumptions, parallel trends, bandwidth/instrument
    validity, specification robustness, and effect size plausibility.

    Confidence range ``(0.60, 0.85)`` reflects lower causal credibility than
    RCT due to reliance on identifying assumptions rather than randomisation.
    """

    name = "quasi_experimental"
    prompt_name = "quasi_experimental_review"
    description = "Review quasi-experimental (DiD, RDD, IV) impact measurement artifacts."
    confidence_range = (0.60, 0.85)

    def prompt_template_dir(self) -> Path:
        """Return the quasi-experimental templates directory."""
        return _PKG_DIR / "templates"

    def knowledge_content_dir(self) -> Path:
        """Return the quasi-experimental knowledge directory."""
        return _PKG_DIR / "knowledge"
