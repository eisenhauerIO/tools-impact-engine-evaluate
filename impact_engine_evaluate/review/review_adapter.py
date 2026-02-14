"""Pipeline component adapter for agentic artifact review."""

from __future__ import annotations

import logging
from dataclasses import asdict

from impact_engine_evaluate.config import ReviewConfig, load_config
from impact_engine_evaluate.review.engine import ReviewEngine
from impact_engine_evaluate.review.models import ArtifactPayload

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


class ArtifactReview(PipelineComponent):
    """Pipeline component that performs an agentic artifact review.

    Parameters
    ----------
    config : ReviewConfig | dict | str | None
        Review configuration. Accepts a ``ReviewConfig``, a dict,
        a YAML file path, or ``None`` for defaults.
    """

    def __init__(self, config: ReviewConfig | dict | str | None = None) -> None:
        if not isinstance(config, ReviewConfig):
            config = load_config(config)
        self._engine = ReviewEngine.from_config(config)

    def execute(self, event: dict) -> dict:
        """Review an artifact from a pipeline event.

        Parameters
        ----------
        event : dict
            Pipeline event with ``initiative_id``, ``artifact_text``,
            and optional ``model_type``, ``sample_size`` keys.

        Returns
        -------
        dict
            Serialized ``ReviewResult``.
        """
        payload = ArtifactPayload.from_event(event)
        result = self._engine.review(payload)
        logger.info(
            "ArtifactReview initiative=%s overall=%.3f",
            result.initiative_id,
            result.overall_score,
        )
        return asdict(result)
