"""Tests for backend abstraction and registry."""

from impact_engine_evaluate.review.backends.base import Backend, BackendRegistry
from impact_engine_evaluate.review.backends.deterministic import DeterministicBackend
from impact_engine_evaluate.review.engine import _parse_dimensions, _parse_overall


class _MockBackend(Backend):
    """In-memory backend for testing."""

    name = "mock"

    def __init__(self, response="mock response", **kwargs):
        self._response = response

    def complete(self, messages, *, model=None, temperature=0.0, max_tokens=4096, response_format=None):
        return self._response


def test_register_and_create():
    BackendRegistry.register("_test_mock")(_MockBackend)
    backend = BackendRegistry.create("_test_mock", response="hello")
    assert backend.name == "mock"
    assert backend.complete([]) == "hello"
    # Cleanup
    del BackendRegistry._backends["_test_mock"]


def test_available_lists_registered():
    BackendRegistry.register("_test_a")(_MockBackend)
    BackendRegistry.register("_test_b")(_MockBackend)
    available = BackendRegistry.available()
    assert "_test_a" in available
    assert "_test_b" in available
    # Cleanup
    del BackendRegistry._backends["_test_a"]
    del BackendRegistry._backends["_test_b"]


def test_create_unknown_raises():
    import pytest

    with pytest.raises(KeyError, match="Unknown backend"):
        BackendRegistry.create("nonexistent_backend_xyz")


def test_backend_complete_contract():
    backend = _MockBackend(response="test output")
    messages = [
        {"role": "system", "content": "You are a reviewer."},
        {"role": "user", "content": "Review this."},
    ]
    result = backend.complete(messages, model="m", temperature=0.5, max_tokens=100)
    assert result == "test output"


# -- Deterministic backend ---------------------------------------------------


def test_deterministic_registered():
    assert "deterministic" in BackendRegistry.available()


def test_deterministic_returns_structured_response():
    backend = DeterministicBackend()
    messages = [
        {
            "role": "system",
            "content": (
                "Evaluate the artifact along these dimensions: internal_validity, external_validity, statistical_power."
            ),
        },
        {
            "role": "user",
            "content": "Review:\n---\nRCT study\n---\nModel type: experiment\nSample size: 500",
        },
    ]
    response = backend.complete(messages)
    dims = _parse_dimensions(response, ["internal_validity", "external_validity", "statistical_power"])
    assert len(dims) == 3
    assert dims[0].name == "internal_validity"
    assert 0.0 <= dims[0].score <= 1.0
    overall = _parse_overall(response, dims)
    assert 0.0 <= overall <= 1.0


def test_deterministic_respects_confidence_map():
    backend = DeterministicBackend()
    messages = [
        {"role": "system", "content": "Evaluate dimensions: confidence."},
        {"role": "user", "content": "Model type: experiment\nSample size: 100"},
    ]
    response = backend.complete(messages)
    dims = _parse_dimensions(response, ["confidence"])
    assert len(dims) == 1
    # Experiment range is 0.85–1.0
    assert 0.85 <= dims[0].score <= 1.0


def test_deterministic_is_deterministic():
    backend = DeterministicBackend()
    messages = [
        {"role": "system", "content": "Evaluate dimensions: confidence."},
        {"role": "user", "content": "Model type: quasi-experiment\nSample size: 200"},
    ]
    r1 = backend.complete(messages)
    r2 = backend.complete(messages)
    assert r1 == r2


def test_deterministic_unknown_model_type():
    backend = DeterministicBackend()
    messages = [
        {"role": "system", "content": "Evaluate dimensions: quality."},
        {"role": "user", "content": "Model type: unknown_type\nSample size: 10"},
    ]
    response = backend.complete(messages)
    dims = _parse_dimensions(response, ["quality"])
    assert len(dims) == 1
    assert 0.0 <= dims[0].score <= 1.0
