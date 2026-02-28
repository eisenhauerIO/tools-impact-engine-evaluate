"""Deterministic confidence scoring for debugging, testing, and illustration."""

import hashlib
from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class EvaluateResult:
    """Confidence-scored initiative with scenario returns."""

    initiative_id: str
    confidence: float
    cost: float
    return_best: float
    return_median: float
    return_worst: float
    model_type: str
    sample_size: int


def _stable_seed(s: str) -> int:
    """Return a deterministic 32-bit seed from a string, stable across processes."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 2**32


def score_initiative(event: dict, confidence_range: tuple[float, float]) -> dict:
    """Score a single initiative using a given confidence range.

    Parameters
    ----------
    event : dict
        Scorer event with keys ``initiative_id``, ``model_type``,
        ``ci_upper``, ``effect_estimate``, ``ci_lower``, ``cost_to_scale``,
        and ``sample_size``.
    confidence_range : tuple[float, float]
        ``(lower, upper)`` bounds for the confidence draw.

    Returns
    -------
    dict
        Serialized ``EvaluateResult`` with confidence drawn deterministically
        from *confidence_range*, seeded by ``initiative_id``.
    """
    seed = _stable_seed(event["initiative_id"])
    rng = np.random.default_rng(seed)
    confidence = rng.uniform(confidence_range[0], confidence_range[1])

    result = EvaluateResult(
        initiative_id=event["initiative_id"],
        confidence=confidence,
        cost=event["cost_to_scale"],
        return_best=event["ci_upper"],
        return_median=event["effect_estimate"],
        return_worst=event["ci_lower"],
        model_type=event["model_type"],
        sample_size=event["sample_size"],
    )
    return asdict(result)
