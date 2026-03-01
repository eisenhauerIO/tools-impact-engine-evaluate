"""Tests for configuration loading."""

import pytest

from impact_engine_evaluate.config import (
    BackendConfig,
    load_config,
)


def test_load_config_defaults():
    config = load_config()
    assert isinstance(config, dict)
    assert config["backend"]["temperature"] == 0.0


def test_load_config_from_dict():
    config = load_config(
        {
            "backend": {"model": "gpt-4o", "temperature": 0.5},
        }
    )
    assert config["backend"]["model"] == "gpt-4o"
    assert config["backend"]["temperature"] == 0.5


def test_load_config_env_override(monkeypatch):
    monkeypatch.setenv("REVIEW_BACKEND_MODEL", "custom-model")
    config = load_config()
    assert config["backend"]["model"] == "custom-model"


def test_load_config_env_overrides_dict(monkeypatch):
    monkeypatch.setenv("REVIEW_BACKEND_MODEL", "env-model")
    config = load_config({"backend": {"model": "dict-model"}})
    assert config["backend"]["model"] == "env-model"


def test_config_dataclass_defaults():
    bc = BackendConfig()
    assert bc.extra == {}


class TestBackendConfigValidation:
    """Validation tests for BackendConfig.__post_init__."""

    def test_empty_model_raises(self):
        with pytest.raises(ValueError, match="model must be a non-empty string"):
            BackendConfig(model="")

    def test_negative_temperature_raises(self):
        with pytest.raises(ValueError, match="temperature must be >= 0"):
            BackendConfig(temperature=-0.1)

    def test_zero_temperature_ok(self):
        bc = BackendConfig(temperature=0.0)
        assert bc.temperature == 0.0

    def test_zero_max_tokens_raises(self):
        with pytest.raises(ValueError, match="max_tokens must be > 0"):
            BackendConfig(max_tokens=0)

    def test_negative_max_tokens_raises(self):
        with pytest.raises(ValueError, match="max_tokens must be > 0"):
            BackendConfig(max_tokens=-1)

    def test_valid_config_passes(self):
        bc = BackendConfig(model="gpt-4o", temperature=0.5, max_tokens=1024)
        assert bc.model == "gpt-4o"

    def test_default_config_valid(self):
        bc = BackendConfig()
        assert bc.model == "claude-sonnet-4-5-20250929"
        assert bc.max_tokens == 4096
