"""Tests for ReviewEngine."""

from impact_engine_evaluate.review.backends.base import Backend, BackendRegistry
from impact_engine_evaluate.review.backends.deterministic import DeterministicBackend
from impact_engine_evaluate.review.engine import ReviewEngine, _parse_dimensions, _parse_overall
from impact_engine_evaluate.review.models import ArtifactPayload, ReviewDimension
from impact_engine_evaluate.review.prompts.registry import PromptRegistry

# -- Mock backend for engine tests -------------------------------------------


class MockBackend(Backend):
    name = "mock"

    def __init__(self, response="", **kwargs):
        self._response = response

    def complete(self, messages, *, model=None, temperature=0.0, max_tokens=4096, response_format=None):
        return self._response


SAMPLE_RESPONSE = """\
DIMENSION: internal_validity
SCORE: 0.85
JUSTIFICATION: Strong randomized design with proper controls.

DIMENSION: external_validity
SCORE: 0.70
JUSTIFICATION: Limited to one geographic region.

DIMENSION: statistical_power
SCORE: 0.90
JUSTIFICATION: Large sample size (n=500).

OVERALL: 0.82
"""


# -- Parser tests ------------------------------------------------------------


def test_parse_dimensions_structured():
    dims = _parse_dimensions(SAMPLE_RESPONSE, ["internal_validity", "external_validity", "statistical_power"])
    assert len(dims) == 3
    assert dims[0].name == "internal_validity"
    assert dims[0].score == 0.85
    assert "randomized" in dims[0].justification.lower()


def test_parse_dimensions_json_fallback():
    import json

    json_response = json.dumps(
        {
            "dimensions": [
                {"name": "accuracy", "score": 0.9, "justification": "Good"},
                {"name": "completeness", "score": 0.8, "justification": "Mostly complete"},
            ]
        }
    )
    dims = _parse_dimensions(json_response, ["accuracy", "completeness"])
    assert len(dims) == 2
    assert dims[0].name == "accuracy"


def test_parse_dimensions_empty():
    dims = _parse_dimensions("No structured content here.", [])
    assert dims == []


def test_parse_overall_from_text():
    score = _parse_overall(SAMPLE_RESPONSE, [])
    assert score == 0.82


def test_parse_overall_fallback_to_mean():
    dims = [
        ReviewDimension(name="a", score=0.8, justification=""),
        ReviewDimension(name="b", score=0.6, justification=""),
    ]
    score = _parse_overall("no overall here", dims)
    assert abs(score - 0.7) < 1e-6


def test_parse_overall_no_data():
    score = _parse_overall("nothing", [])
    assert score == 0.0


# -- Engine integration tests ------------------------------------------------


def test_engine_review():
    BackendRegistry.register("_test_engine_mock")(MockBackend)
    try:
        backend = MockBackend(response=SAMPLE_RESPONSE)
        registry = PromptRegistry()
        engine = ReviewEngine(
            backend=backend,
            prompt_registry=registry,
            default_prompt="study_design_review",
        )

        payload = ArtifactPayload(
            initiative_id="init-test",
            artifact_text="RCT with 500 participants in Kenya",
            model_type="experiment",
            sample_size=500,
        )
        result = engine.review(payload)

        assert result.initiative_id == "init-test"
        assert result.prompt_name == "study_design_review"
        assert result.backend_name == "mock"
        assert len(result.dimensions) == 3
        assert result.overall_score == 0.82
        assert result.raw_response == SAMPLE_RESPONSE
        assert result.timestamp  # non-empty
    finally:
        BackendRegistry._backends.pop("_test_engine_mock", None)


def test_engine_review_with_prompt_override():
    backend = MockBackend(response=SAMPLE_RESPONSE)
    registry = PromptRegistry()
    engine = ReviewEngine(
        backend=backend,
        prompt_registry=registry,
        default_prompt="study_design_review",
    )

    payload = ArtifactPayload(
        initiative_id="init-test-2",
        artifact_text="Data quality artifact",
    )
    result = engine.review(payload, prompt_name="data_quality_review")
    assert result.prompt_name == "data_quality_review"


# -- Deterministic backend through engine ------------------------------------


def test_engine_deterministic_backend():
    backend = DeterministicBackend()
    registry = PromptRegistry()
    engine = ReviewEngine(
        backend=backend,
        prompt_registry=registry,
        default_prompt="study_design_review",
    )

    payload = ArtifactPayload(
        initiative_id="init-det",
        artifact_text="RCT with 500 participants",
        model_type="experiment",
        sample_size=500,
    )
    result = engine.review(payload)

    assert result.initiative_id == "init-det"
    assert result.backend_name == "deterministic"
    assert result.prompt_name == "study_design_review"
    assert len(result.dimensions) == 3
    for dim in result.dimensions:
        assert 0.85 <= dim.score <= 1.0, f"{dim.name} score out of experiment range"
    assert 0.85 <= result.overall_score <= 1.0


def test_engine_deterministic_is_reproducible():
    backend = DeterministicBackend()
    registry = PromptRegistry()
    engine = ReviewEngine(
        backend=backend,
        prompt_registry=registry,
        default_prompt="study_design_review",
    )

    payload = ArtifactPayload(
        initiative_id="init-repro",
        artifact_text="Observational cohort study, n=200",
        model_type="observational",
        sample_size=200,
    )
    r1 = engine.review(payload)
    r2 = engine.review(payload)
    assert r1.overall_score == r2.overall_score
    assert [d.score for d in r1.dimensions] == [d.score for d in r2.dimensions]


def test_engine_deterministic_via_from_config():
    engine = ReviewEngine.from_config({"backend": {"type": "deterministic", "model": "deterministic"}})
    payload = ArtifactPayload(
        initiative_id="init-cfg",
        artifact_text="Synthetic control study",
        model_type="synthetic_control",
        sample_size=300,
    )
    result = engine.review(payload)
    assert result.backend_name == "deterministic"
    assert len(result.dimensions) >= 1
    assert 0.0 <= result.overall_score <= 1.0
