"""Tests for method reviewer registry mechanics."""

import pytest

from impact_engine_evaluate.review.methods.base import MethodReviewer, MethodReviewerRegistry
from impact_engine_evaluate.review.models import ArtifactPayload


class _MockMethodReviewer(MethodReviewer):
    """Test-only method reviewer."""

    name = "mock_method"
    prompt_name = "mock_review"
    description = "Mock method for testing."

    def load_artifact(self, manifest, job_dir):
        return ArtifactPayload(
            initiative_id="mock-id",
            artifact_text="mock artifact",
            model_type=manifest.model_type,
        )


def test_register_and_create():
    MethodReviewerRegistry.register("_test_mock_method")(_MockMethodReviewer)
    reviewer = MethodReviewerRegistry.create("_test_mock_method")
    assert reviewer.name == "mock_method"
    assert reviewer.prompt_name == "mock_review"
    # Cleanup
    del MethodReviewerRegistry._methods["_test_mock_method"]


def test_available_lists_registered():
    MethodReviewerRegistry.register("_test_m1")(_MockMethodReviewer)
    MethodReviewerRegistry.register("_test_m2")(_MockMethodReviewer)
    available = MethodReviewerRegistry.available()
    assert "_test_m1" in available
    assert "_test_m2" in available
    # Cleanup
    del MethodReviewerRegistry._methods["_test_m1"]
    del MethodReviewerRegistry._methods["_test_m2"]


def test_create_unknown_raises():
    with pytest.raises(KeyError, match="Unknown method"):
        MethodReviewerRegistry.create("nonexistent_method_xyz")


def test_experiment_auto_registered():
    assert "experiment" in MethodReviewerRegistry.available()


def test_experiment_reviewer_has_template_dir():
    reviewer = MethodReviewerRegistry.create("experiment")
    template_dir = reviewer.prompt_template_dir()
    assert template_dir is not None
    assert template_dir.is_dir()
    assert (template_dir / "experiment_review.yaml").exists()


def test_experiment_reviewer_has_knowledge_dir():
    reviewer = MethodReviewerRegistry.create("experiment")
    knowledge_dir = reviewer.knowledge_content_dir()
    assert knowledge_dir is not None
    assert knowledge_dir.is_dir()
    assert any(knowledge_dir.glob("*.md"))


def test_method_reviewer_default_dirs():
    MethodReviewerRegistry.register("_test_no_dirs")(_MockMethodReviewer)
    reviewer = MethodReviewerRegistry.create("_test_no_dirs")
    assert reviewer.prompt_template_dir() is None
    assert reviewer.knowledge_content_dir() is None
    del MethodReviewerRegistry._methods["_test_no_dirs"]


def test_registered_reviewers_have_confidence_range():
    """Every registered reviewer has a non-default confidence_range."""
    for name in MethodReviewerRegistry.available():
        reviewer = MethodReviewerRegistry.create(name)
        lo, hi = reviewer.confidence_range
        assert lo > 0.0 or hi > 0.0, f"{name} has default (0.0, 0.0) confidence_range"
        assert lo <= hi, f"{name} has inverted confidence_range: ({lo}, {hi})"


def test_confidence_map():
    """confidence_map() returns a dict keyed by method name."""
    cmap = MethodReviewerRegistry.confidence_map()
    assert "experiment" in cmap
    assert cmap["experiment"] == (0.85, 1.0)
