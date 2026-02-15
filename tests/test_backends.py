"""Tests for backend abstraction and registry."""

from impact_engine_evaluate.review.backends.base import Backend, BackendRegistry


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
