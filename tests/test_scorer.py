"""Tests for the pure scoring logic."""

from impact_engine_evaluate.scorer import score_initiative

EXPERIMENT_RANGE = (0.85, 1.0)


def test_confidence_within_range(sample_scorer_event):
    """Confidence falls within the given confidence range."""
    result = score_initiative(sample_scorer_event, EXPERIMENT_RANGE)
    assert EXPERIMENT_RANGE[0] <= result["confidence"] <= EXPERIMENT_RANGE[1]


def test_return_mapping(sample_scorer_event):
    """Return fields map correctly from event inputs."""
    result = score_initiative(sample_scorer_event, EXPERIMENT_RANGE)
    assert result["return_worst"] == sample_scorer_event["ci_lower"]
    assert result["return_median"] == sample_scorer_event["effect_estimate"]
    assert result["return_best"] == sample_scorer_event["ci_upper"]


def test_determinism(sample_scorer_event):
    """Same initiative_id always produces the same confidence."""
    r1 = score_initiative(sample_scorer_event, EXPERIMENT_RANGE)
    r2 = score_initiative(sample_scorer_event, EXPERIMENT_RANGE)
    assert r1["confidence"] == r2["confidence"]


def test_model_type_is_string(sample_scorer_event):
    """Model type in result is a plain string."""
    result = score_initiative(sample_scorer_event, EXPERIMENT_RANGE)
    assert isinstance(result["model_type"], str)
    assert result["model_type"] == "experiment"


def test_different_ranges_produce_different_confidence(sample_scorer_event):
    """Different confidence ranges produce different scores for the same event."""
    r1 = score_initiative(sample_scorer_event, (0.85, 1.0))
    r2 = score_initiative(sample_scorer_event, (0.20, 0.39))
    assert r1["confidence"] != r2["confidence"]
    assert 0.85 <= r1["confidence"] <= 1.0
    assert 0.20 <= r2["confidence"] <= 0.39
