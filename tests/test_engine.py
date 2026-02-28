"""Tests for ReviewEngine."""

from impact_engine_evaluate.review.backends.base import Backend, BackendRegistry
from impact_engine_evaluate.review.engine import ReviewEngine, _parse_dimensions, _parse_overall, render
from impact_engine_evaluate.review.models import ArtifactPayload, PromptSpec, ReviewDimension

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

SAMPLE_SPEC = PromptSpec(
    name="study_design_review",
    version="1.0",
    description="Review study design quality",
    dimensions=["internal_validity", "external_validity", "statistical_power"],
    system_template="You are a reviewer.\n{% if knowledge_context %}Use: {{ knowledge_context }}{% endif %}",
    user_template="Review: {{ artifact }}\nModel: {{ model_type }}\nSample: {{ sample_size }}",
)


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


# -- Render tests ------------------------------------------------------------


def test_render_basic():
    spec = PromptSpec(
        name="test",
        version="1.0",
        description="Test",
        system_template="You are a {{ role }}.",
        user_template="Review: {{ artifact }}",
    )
    messages = render(spec, {"role": "reviewer", "artifact": "study text"})
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "reviewer" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "study text" in messages[1]["content"]


def test_render_empty_templates():
    spec = PromptSpec(name="empty", version="1.0", description="Empty")
    messages = render(spec, {})
    assert messages == []


def test_render_system_only():
    spec = PromptSpec(
        name="sys",
        version="1.0",
        description="System only",
        system_template="Hello {{ name }}",
    )
    messages = render(spec, {"name": "world"})
    assert len(messages) == 1
    assert messages[0]["role"] == "system"


# -- Engine integration tests ------------------------------------------------


def test_engine_review():
    BackendRegistry.register("_test_engine_mock")(MockBackend)
    try:
        backend = MockBackend(response=SAMPLE_RESPONSE)
        engine = ReviewEngine(backend=backend)

        payload = ArtifactPayload(
            initiative_id="init-test",
            artifact_text="RCT with 500 participants in Kenya",
            model_type="experiment",
            sample_size=500,
        )
        result = engine.review(payload, SAMPLE_SPEC)

        assert result.initiative_id == "init-test"
        assert result.prompt_name == "study_design_review"
        assert result.backend_name == "mock"
        assert len(result.dimensions) == 3
        assert result.overall_score == 0.82
        assert result.raw_response == SAMPLE_RESPONSE
        assert result.timestamp  # non-empty
    finally:
        BackendRegistry._backends.pop("_test_engine_mock", None)


def test_engine_review_with_knowledge():
    backend = MockBackend(response=SAMPLE_RESPONSE)
    engine = ReviewEngine(backend=backend)

    payload = ArtifactPayload(
        initiative_id="init-test-kb",
        artifact_text="RCT data",
        model_type="experiment",
    )
    result = engine.review(payload, SAMPLE_SPEC, knowledge_context="RCT fundamentals...")
    assert result.prompt_name == "study_design_review"
    assert len(result.dimensions) == 3
