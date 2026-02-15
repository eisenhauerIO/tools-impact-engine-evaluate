"""Tests for the pure scoring logic."""

from impact_engine_evaluate.scorer import CONFIDENCE_MAP, ModelType, score_initiative


def test_confidence_within_range(sample_measure_event):
    """Confidence falls within the expected range for the model type."""
    result = score_initiative(sample_measure_event)
    lo, hi = CONFIDENCE_MAP[sample_measure_event["model_type"]]
    assert lo <= result["confidence"] <= hi


def test_return_mapping(sample_measure_event):
    """Return fields map correctly from measure result inputs."""
    result = score_initiative(sample_measure_event)
    assert result["return_worst"] == sample_measure_event["ci_lower"]
    assert result["return_median"] == sample_measure_event["effect_estimate"]
    assert result["return_best"] == sample_measure_event["ci_upper"]


def test_determinism(sample_measure_event):
    """Same initiative_id always produces the same confidence."""
    r1 = score_initiative(sample_measure_event)
    r2 = score_initiative(sample_measure_event)
    assert r1["confidence"] == r2["confidence"]


def test_all_model_types_have_confidence_map():
    """Every ModelType has a corresponding CONFIDENCE_MAP entry."""
    for mt in ModelType:
        assert mt in CONFIDENCE_MAP, f"{mt} missing from CONFIDENCE_MAP"


def test_all_model_types_produce_valid_confidence(all_model_events):
    """Confidence is within range for every model type."""
    for event in all_model_events:
        result = score_initiative(event)
        lo, hi = CONFIDENCE_MAP[event["model_type"]]
        assert lo <= result["confidence"] <= hi, f"Failed for {event['model_type']}"
