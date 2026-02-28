"""Shared data models for the EVALUATE pipeline stage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from impact_engine_evaluate.review.models import ReviewResult


@dataclass
class EvaluateResult:
    """Output of the EVALUATE pipeline stage (both strategies).

    Parameters
    ----------
    initiative_id : str
        Initiative identifier.
    confidence : float
        Confidence score between 0.0 and 1.0.
    confidence_range : tuple[float, float]
        ``(lower, upper)`` bounds from the method reviewer.
    strategy : str
        Strategy that produced this result (``"score"`` or ``"review"``).
    report : str | ReviewResult
        Descriptive string for the score strategy; full
        :class:`~impact_engine_evaluate.review.models.ReviewResult` for
        the review strategy.
    """

    initiative_id: str
    confidence: float
    confidence_range: tuple[float, float]
    strategy: str
    report: str | ReviewResult = ""
