"""Tests for the deterministic confidence scoring logic."""

from impact_engine_evaluate.score.scorer import ScoreResult, score_confidence

EXPERIMENT_RANGE = (0.85, 1.0)


def test_confidence_within_range():
    """Confidence falls within the given confidence range."""
    result = score_confidence("init-001", EXPERIMENT_RANGE)
    assert EXPERIMENT_RANGE[0] <= result.confidence <= EXPERIMENT_RANGE[1]


def test_determinism():
    """Same initiative_id always produces the same confidence."""
    r1 = score_confidence("init-001", EXPERIMENT_RANGE)
    r2 = score_confidence("init-001", EXPERIMENT_RANGE)
    assert r1 == r2


def test_different_ids_produce_different_confidence():
    """Different initiative_ids produce different scores."""
    r1 = score_confidence("init-001", EXPERIMENT_RANGE)
    r2 = score_confidence("init-999", EXPERIMENT_RANGE)
    assert r1.confidence != r2.confidence


def test_different_ranges_produce_different_confidence():
    """Different confidence ranges produce different scores for the same id."""
    r1 = score_confidence("init-001", (0.85, 1.0))
    r2 = score_confidence("init-001", (0.20, 0.39))
    assert r1.confidence != r2.confidence
    assert 0.85 <= r1.confidence <= 1.0
    assert 0.20 <= r2.confidence <= 0.39


def test_returns_score_result():
    """score_confidence returns a ScoreResult with audit fields."""
    result = score_confidence("init-001", EXPERIMENT_RANGE)
    assert isinstance(result, ScoreResult)
    assert result.initiative_id == "init-001"
    assert result.confidence_range == EXPERIMENT_RANGE
