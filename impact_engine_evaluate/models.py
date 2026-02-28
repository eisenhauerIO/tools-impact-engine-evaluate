"""Shared data models for the EVALUATE pipeline stage."""

from dataclasses import dataclass


@dataclass
class EvaluateResult:
    """Output of the EVALUATE pipeline stage (both strategies).

    This is the shared output regardless of whether the ``"score"`` or
    ``"review"`` strategy was used.
    """

    initiative_id: str
    confidence: float
    cost: float
    return_best: float
    return_median: float
    return_worst: float
    model_type: str
    sample_size: int
