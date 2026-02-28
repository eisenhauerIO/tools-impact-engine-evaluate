"""EVALUATE component: unified strategy dispatch for the orchestrator pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Protocol

from impact_engine_evaluate.job_reader import load_scorer_event
from impact_engine_evaluate.review.manifest import load_manifest
from impact_engine_evaluate.review.methods import MethodReviewerRegistry
from impact_engine_evaluate.review.methods.base import MethodReviewer
from impact_engine_evaluate.scorer import score_initiative

logger = logging.getLogger(__name__)


class PipelineComponent(Protocol):
    """Structural interface for pipeline stage components."""

    def execute(self, event: dict) -> dict:
        """Process event and return result."""
        ...


class Evaluate(PipelineComponent):
    """Unified evaluate component with deterministic and agentic strategies.

    Reads a job directory, dispatches on ``evaluate_strategy`` from the
    manifest, and returns a common 8-key output dict for downstream ALLOCATE.

    Parameters
    ----------
    config : dict | str | None
        Backend configuration for the agentic strategy. Passed through to
        ``review()``.
    """

    def __init__(self, *, config: dict | str | None = None) -> None:
        self._config = config

    def execute(self, event: dict) -> dict:
        """Evaluate an initiative from its job directory.

        Parameters
        ----------
        event : dict
            Must contain ``"job_dir"``. May contain ``"cost_to_scale"``
            as an override.

        Returns
        -------
        dict
            Eight-key output: ``initiative_id``, ``confidence``, ``cost``,
            ``return_best``, ``return_median``, ``return_worst``,
            ``model_type``, ``sample_size``.

        Raises
        ------
        ValueError
            If ``evaluate_strategy`` is unknown.
        """
        job_dir = event["job_dir"]
        manifest = load_manifest(job_dir)
        strategy = manifest.evaluate_strategy

        reviewer = MethodReviewerRegistry.create(manifest.model_type)

        # Build overrides from the orchestrator event
        overrides: dict[str, Any] = {}
        if "cost_to_scale" in event:
            overrides["cost_to_scale"] = event["cost_to_scale"]

        scorer_event = load_scorer_event(manifest, job_dir, overrides=overrides or None)

        if strategy == "deterministic":
            result = self._deterministic(reviewer, scorer_event)
        elif strategy == "agentic":
            result = self._agentic(scorer_event, job_dir)
        else:
            msg = f"Unknown evaluate_strategy: {strategy!r}"
            raise ValueError(msg)

        logger.info(
            "Evaluated initiative=%s strategy=%s confidence=%.3f",
            result["initiative_id"],
            strategy,
            result["confidence"],
        )
        return result

    def _deterministic(self, reviewer: MethodReviewer, scorer_event: dict) -> dict:
        """Run the deterministic scoring path."""
        return score_initiative(scorer_event, reviewer.confidence_range)

    def _agentic(self, scorer_event: dict, job_dir: str | Path) -> dict:
        """Run the agentic LLM review path."""
        from impact_engine_evaluate.review.api import review

        review_result = review(job_dir, config=self._config)

        confidence = review_result.overall_score
        if confidence == 0.0 and not review_result.dimensions:
            logger.warning(
                "Agentic review returned 0.0 with no dimensions for initiative=%s",
                scorer_event["initiative_id"],
            )

        return {
            "initiative_id": scorer_event["initiative_id"],
            "confidence": confidence,
            "cost": scorer_event["cost_to_scale"],
            "return_best": scorer_event["ci_upper"],
            "return_median": scorer_event["effect_estimate"],
            "return_worst": scorer_event["ci_lower"],
            "model_type": scorer_event["model_type"],
            "sample_size": scorer_event["sample_size"],
        }
