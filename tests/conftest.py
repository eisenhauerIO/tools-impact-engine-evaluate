"""Shared fixtures for evaluate tests."""

import pytest

from impact_engine_evaluate.scorer import ModelType


@pytest.fixture()
def sample_measure_event():
    """Measure result event matching the orchestrator contract."""
    return {
        "initiative_id": "init-001",
        "model_type": ModelType.EXPERIMENT,
        "ci_upper": 15.0,
        "effect_estimate": 10.0,
        "ci_lower": 5.0,
        "cost_to_scale": 100.0,
        "sample_size": 50,
    }


@pytest.fixture()
def all_model_events():
    """One measure result event per ModelType."""
    return [
        {
            "initiative_id": f"init-{mt.name.lower()}",
            "model_type": mt,
            "ci_upper": 15.0,
            "effect_estimate": 10.0,
            "ci_lower": 5.0,
            "cost_to_scale": 100.0,
            "sample_size": 50,
        }
        for mt in ModelType
    ]
