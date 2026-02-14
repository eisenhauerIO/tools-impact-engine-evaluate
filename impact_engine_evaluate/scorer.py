"""Pure evaluation logic: confidence scoring by model type."""

import hashlib
import random
from dataclasses import dataclass
from enum import Enum


class ModelType(Enum):
    """Causal inference methodology used for measurement."""

    EXPERIMENT = "experiment"
    QUASI_EXPERIMENT = "quasi-experiment"
    TIME_SERIES = "time-series"
    OBSERVATIONAL = "observational"
    INTERRUPTED_TIME_SERIES = "interrupted_time_series"
    SYNTHETIC_CONTROL = "synthetic_control"
    NEAREST_NEIGHBOUR_MATCHING = "nearest_neighbour_matching"
    SUBCLASSIFICATION = "subclassification"
    METRICS_APPROXIMATION = "metrics_approximation"


@dataclass
class EvaluateResult:
    """Confidence-scored initiative with scenario returns."""

    initiative_id: str
    confidence: float
    cost: float
    return_best: float
    return_median: float
    return_worst: float
    model_type: ModelType
    sample_size: int


CONFIDENCE_MAP: dict[ModelType, tuple[float, float]] = {
    ModelType.EXPERIMENT: (0.85, 1.0),
    ModelType.QUASI_EXPERIMENT: (0.60, 0.84),
    ModelType.TIME_SERIES: (0.40, 0.59),
    ModelType.OBSERVATIONAL: (0.20, 0.39),
    ModelType.INTERRUPTED_TIME_SERIES: (0.40, 0.59),
    ModelType.SYNTHETIC_CONTROL: (0.60, 0.84),
    ModelType.NEAREST_NEIGHBOUR_MATCHING: (0.60, 0.84),
    ModelType.SUBCLASSIFICATION: (0.60, 0.84),
    ModelType.METRICS_APPROXIMATION: (0.20, 0.39),
}


def _stable_seed(s: str) -> int:
    """Return a deterministic 32-bit seed from a string, stable across processes."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % 2**32


def score_initiative(event: dict) -> dict:
    """Score a single initiative based on its model type.

    Parameters
    ----------
    event : dict
        Measure result with keys ``initiative_id``, ``model_type``,
        ``ci_upper``, ``effect_estimate``, ``ci_lower``, ``cost_to_scale``,
        and ``sample_size``.

    Returns
    -------
    dict
        Serialized ``EvaluateResult`` with confidence drawn deterministically
        from the range defined by ``CONFIDENCE_MAP[model_type]``.
    """
    from dataclasses import asdict

    model_type = event["model_type"]
    conf_range = CONFIDENCE_MAP[model_type]
    seed = _stable_seed(event["initiative_id"])
    rng = random.Random(seed)
    confidence = rng.uniform(conf_range[0], conf_range[1])

    result = EvaluateResult(
        initiative_id=event["initiative_id"],
        confidence=confidence,
        cost=event["cost_to_scale"],
        return_best=event["ci_upper"],
        return_median=event["effect_estimate"],
        return_worst=event["ci_lower"],
        model_type=model_type,
        sample_size=event["sample_size"],
    )
    return asdict(result)
