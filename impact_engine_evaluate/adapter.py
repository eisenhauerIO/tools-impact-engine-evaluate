"""EVALUATE component: symmetric strategy dispatch for the orchestrator pipeline."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol

from impact_engine_evaluate.job_reader import load_scorer_event
from impact_engine_evaluate.models import EvaluateResult
from impact_engine_evaluate.review.manifest import load_manifest
from impact_engine_evaluate.review.methods import MethodReviewerRegistry
from impact_engine_evaluate.score import ScoreResult, score_confidence

logger = logging.getLogger(__name__)

EVALUATE_RESULT_FILENAME = "evaluate_result.json"
SCORE_RESULT_FILENAME = "score_result.json"


class PipelineComponent(Protocol):
    """Structural interface for pipeline stage components."""

    def execute(self, event: dict) -> dict:
        """Process event and return result."""
        ...


class Evaluate(PipelineComponent):
    """Unified evaluate component with score and review strategies.

    Reads a job directory, dispatches on ``evaluate_strategy`` from the
    manifest, and returns an :class:`EvaluateResult` dict for downstream
    stages.  Both strategies share the same flow — only the confidence
    source and report differ.

    Parameters
    ----------
    config : dict | str | None
        Backend configuration for the review strategy. Passed through to
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
            Keys: ``initiative_id``, ``confidence``, ``confidence_range``,
            ``strategy``, ``report``.

        Raises
        ------
        ValueError
            If ``evaluate_strategy`` is unknown.
        """
        job_dir = Path(event["job_dir"])
        manifest = load_manifest(job_dir)
        strategy = manifest.evaluate_strategy

        reviewer = MethodReviewerRegistry.create(manifest.model_type)

        # Build overrides from the orchestrator event
        overrides: dict[str, Any] = {}
        if "cost_to_scale" in event:
            overrides["cost_to_scale"] = event["cost_to_scale"]

        scorer_event = load_scorer_event(manifest, job_dir, overrides=overrides or None)

        confidence_range = reviewer.confidence_range

        # --- Only this block differs between strategies ---
        if strategy == "score":
            score_result = score_confidence(scorer_event["initiative_id"], confidence_range)
            _write_score_result(job_dir, score_result)
            confidence = score_result.confidence
            report = f"Confidence drawn uniformly between {confidence_range[0]:.2f} and {confidence_range[1]:.2f}"
        elif strategy == "review":
            from impact_engine_evaluate.review.api import review

            review_result = review(job_dir, config=self._config)
            confidence = review_result.overall_score
            report = review_result
            if confidence == 0.0 and not review_result.dimensions:
                logger.warning(
                    "Review returned 0.0 with no dimensions for initiative=%s",
                    scorer_event["initiative_id"],
                )
        else:
            msg = f"Unknown evaluate_strategy: {strategy!r}"
            raise ValueError(msg)

        # --- Everything below is shared ---
        result = EvaluateResult(
            initiative_id=scorer_event["initiative_id"],
            confidence=confidence,
            confidence_range=confidence_range,
            strategy=strategy,
            report=report,
        )

        _write_evaluate_result(job_dir, result)

        logger.info(
            "Evaluated initiative=%s strategy=%s confidence=%.3f",
            result.initiative_id,
            strategy,
            result.confidence,
        )
        return asdict(result)


def _write_score_result(job_dir: Path, result: ScoreResult) -> None:
    """Write score result to the job directory."""
    result_path = job_dir / SCORE_RESULT_FILENAME
    result_path.write_text(json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8")
    logger.debug("Wrote score result to %s", result_path)


def _write_evaluate_result(job_dir: Path, result: EvaluateResult) -> None:
    """Write evaluate result to the job directory."""
    result_path = job_dir / EVALUATE_RESULT_FILENAME
    result_path.write_text(json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8")
    logger.debug("Wrote evaluate result to %s", result_path)
