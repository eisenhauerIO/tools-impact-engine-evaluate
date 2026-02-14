"""Tests for configuration loading."""

from impact_engine_evaluate.config import (
    BackendConfig,
    KnowledgeConfig,
    PromptConfig,
    ReviewConfig,
    load_config,
)


def test_load_config_defaults():
    config = load_config()
    assert isinstance(config, ReviewConfig)
    assert config.backend.type == "anthropic"
    assert config.backend.temperature == 0.0
    assert config.prompt.name == "study_design_review"
    assert config.knowledge is None


def test_load_config_from_dict():
    config = load_config(
        {
            "backend": {"type": "openai", "model": "gpt-4o", "temperature": 0.5},
            "prompt": {"name": "data_quality_review"},
            "knowledge": {"type": "static", "path": "/tmp/kb", "top_k": 3},
        }
    )
    assert config.backend.type == "openai"
    assert config.backend.model == "gpt-4o"
    assert config.backend.temperature == 0.5
    assert config.prompt.name == "data_quality_review"
    assert config.knowledge is not None
    assert config.knowledge.type == "static"
    assert config.knowledge.top_k == 3


def test_load_config_env_override(monkeypatch):
    monkeypatch.setenv("REVIEW_BACKEND_TYPE", "litellm")
    monkeypatch.setenv("REVIEW_BACKEND_MODEL", "custom-model")
    monkeypatch.setenv("REVIEW_PROMPT_NAME", "data_quality_review")
    config = load_config()
    assert config.backend.type == "litellm"
    assert config.backend.model == "custom-model"
    assert config.prompt.name == "data_quality_review"


def test_load_config_env_overrides_dict(monkeypatch):
    monkeypatch.setenv("REVIEW_BACKEND_TYPE", "openai")
    config = load_config({"backend": {"type": "anthropic"}})
    assert config.backend.type == "openai"


def test_config_dataclass_defaults():
    bc = BackendConfig()
    assert bc.type == "anthropic"
    assert bc.extra == {}

    pc = PromptConfig()
    assert pc.template_dirs == []

    kc = KnowledgeConfig()
    assert kc.type == "static"
    assert kc.top_k == 5
