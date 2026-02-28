"""Deterministic confidence scoring for debugging, testing, and illustration."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass


@dataclass
class ScoreResult:
    """Result of the score strategy.

    Mirrors ``ReviewResult`` for the review strategy. Captures the
    computed confidence together with the inputs that produced it,
    providing an audit trail for the deterministic path.

    Parameters
    ----------
    initiative_id : str
        Initiative identifier used as seed.
    confidence : float
        Deterministic confidence value.
    confidence_range : tuple[float, float]
        ``(lower, upper)`` bounds from the method reviewer.
    """

    initiative_id: str
    confidence: float
    confidence_range: tuple[float, float]


def _stable_seed(s: str) -> int:
    """Return a deterministic 32-bit seed from a string, stable across processes."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 2**32


def score_confidence(initiative_id: str, confidence_range: tuple[float, float]) -> ScoreResult:
    """Draw a reproducible confidence value from *confidence_range*.

    Parameters
    ----------
    initiative_id : str
        Seed string (typically the initiative identifier).
    confidence_range : tuple[float, float]
        ``(lower, upper)`` bounds for the confidence draw.

    Returns
    -------
    ScoreResult
        Result containing the confidence value and audit fields.
    """
    seed = _stable_seed(initiative_id)
    rng = random.Random(seed)
    confidence = rng.uniform(confidence_range[0], confidence_range[1])
    return ScoreResult(
        initiative_id=initiative_id,
        confidence=confidence,
        confidence_range=confidence_range,
    )
