"""Tests for the ArtifactReview pipeline component."""

from unittest.mock import MagicMock, patch

from impact_engine_evaluate.review.review_adapter import ArtifactReview

SAMPLE_RESPONSE = """\
DIMENSION: internal_validity
SCORE: 0.85
JUSTIFICATION: Strong design.

DIMENSION: external_validity
SCORE: 0.70
JUSTIFICATION: Limited scope.

DIMENSION: statistical_power
SCORE: 0.90
JUSTIFICATION: Large sample.

OVERALL: 0.82
"""


def _make_mock_backend():
    backend = MagicMock()
    backend.name = "mock"
    backend.complete.return_value = SAMPLE_RESPONSE
    return backend


@patch("impact_engine_evaluate.review.engine.BackendRegistry")
def test_artifact_review_execute(mock_registry_cls):
    mock_registry_cls.create.return_value = _make_mock_backend()

    adapter = ArtifactReview(
        config={
            "backend": {"type": "mock", "model": "mock-model"},
        }
    )
    event = {
        "initiative_id": "init-adapter-test",
        "artifact_text": "RCT with 500 participants",
        "model_type": "experiment",
        "sample_size": 500,
    }
    result = adapter.execute(event)
    assert result["initiative_id"] == "init-adapter-test"
    assert result["overall_score"] == 0.82
    assert len(result["dimensions"]) == 3


@patch("impact_engine_evaluate.review.engine.BackendRegistry")
def test_artifact_review_returns_all_keys(mock_registry_cls):
    mock_registry_cls.create.return_value = _make_mock_backend()

    adapter = ArtifactReview(
        config={
            "backend": {"type": "mock", "model": "mock-model"},
        }
    )
    event = {"initiative_id": "init-keys", "artifact_text": "text"}
    result = adapter.execute(event)

    expected_keys = {
        "initiative_id",
        "prompt_name",
        "prompt_version",
        "backend_name",
        "model",
        "dimensions",
        "overall_score",
        "raw_response",
        "timestamp",
    }
    assert set(result.keys()) == expected_keys
