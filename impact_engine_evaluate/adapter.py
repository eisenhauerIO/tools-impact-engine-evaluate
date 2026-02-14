"""EVALUATE component: confidence scoring for the orchestrator pipeline."""

import logging

from impact_engine_evaluate.scorer import score_initiative

logger = logging.getLogger(__name__)

try:
    from impact_engine_orchestrator.components.base import PipelineComponent
except ImportError:
    from abc import ABC, abstractmethod

    class PipelineComponent(ABC):  # type: ignore[no-redef]
        """Fallback base when orchestrator is not installed."""

        @abstractmethod
        def execute(self, event: dict) -> dict:
            """Process event and return result."""


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
