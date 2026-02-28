"""Tests for configuration loading."""

from impact_engine_evaluate.config import (
    BackendConfig,
    ReviewConfig,
    load_config,
)


def test_load_config_defaults():
    config = load_config()
    assert isinstance(config, ReviewConfig)
    assert config.backend.temperature == 0.0


def test_load_config_from_dict():
    config = load_config(
        {
            "backend": {"model": "gpt-4o", "temperature": 0.5},
        }
    )
    assert config.backend.model == "gpt-4o"
    assert config.backend.temperature == 0.5


def test_load_config_env_override(monkeypatch):
    monkeypatch.setenv("REVIEW_BACKEND_MODEL", "custom-model")
    config = load_config()
    assert config.backend.model == "custom-model"


def test_load_config_env_overrides_dict(monkeypatch):
    monkeypatch.setenv("REVIEW_BACKEND_MODEL", "env-model")
    config = load_config({"backend": {"model": "dict-model"}})
    assert config.backend.model == "env-model"


def test_config_dataclass_defaults():
    bc = BackendConfig()
    assert bc.extra == {}
