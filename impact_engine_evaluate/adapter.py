"""EVALUATE component: confidence scoring for the orchestrator pipeline."""

import logging

from impact_engine_evaluate.scorer import score_initiative

logger = logging.getLogger(__name__)

from typing import Protocol


class PipelineComponent(Protocol):
    """Structural interface for pipeline stage components."""

    def execute(self, event: dict) -> dict: ...


class Evaluate(PipelineComponent):
    """Deterministic confidence scorer based on model type."""

    def execute(self, event: dict) -> dict:
        """Return a validated EvaluateResult dict.

        Parameters
        ----------
        event : dict
            Measure result with keys ``initiative_id``, ``model_type``,
            ``ci_upper``, ``effect_estimate``, ``ci_lower``,
            ``cost_to_scale``, and ``sample_size``.

        Returns
        -------
        dict
            Serialized ``EvaluateResult``.
        """
        result = score_initiative(event)
        logger.info(
            "Evaluated initiative=%s confidence=%.3f",
            result["initiative_id"],
            result["confidence"],
        )
        return result
