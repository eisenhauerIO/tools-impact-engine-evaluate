"""Unified configuration for the review subsystem."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class BackendConfig:
    """LLM backend configuration.

    Parameters
    ----------
    model : str
        Model identifier passed to ``litellm.completion()``.
    temperature : float
        Sampling temperature.
    max_tokens : int
        Maximum tokens per completion.
    extra : dict
        Additional kwargs forwarded to ``litellm.completion()``.
    """

    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.0
    max_tokens: int = 4096
    extra: dict = field(default_factory=dict)


@dataclass
class MethodConfig:
    """Per-method prompt and knowledge base selection.

    Parameters
    ----------
    prompt : str
        Name of a registered prompt spec.  Empty string uses the reviewer's
        default ``prompt_template_dir()``.
    knowledge_base : str
        Name of a registered knowledge base.  Empty string uses the reviewer's
        default ``knowledge_content_dir()``.
    """

    prompt: str = ""
    knowledge_base: str = ""


@dataclass
class ReviewConfig:
    """Top-level configuration for the review subsystem.

    Parameters
    ----------
    backend : BackendConfig
        LLM backend settings.
    methods : dict[str, MethodConfig]
        Per-method prompt and knowledge base overrides, keyed by ``model_type``.
    """

    backend: BackendConfig = field(default_factory=BackendConfig)
    methods: dict[str, MethodConfig] = field(default_factory=dict)


def load_config(source: str | Path | dict[str, Any] | None = None) -> ReviewConfig:
    """Load a ReviewConfig from a YAML file, dict, or environment variables.

    Parameters
    ----------
    source : str | Path | dict | None
        A path to a YAML file, a raw dict, or ``None`` to use only
        environment variable overrides on defaults.

    Returns
    -------
    ReviewConfig
    """
    raw: dict[str, Any] = {}

    if isinstance(source, dict):
        raw = source
    elif source is not None:
        path = Path(source)
        if path.is_file():
            raw = _load_yaml(path)

    backend_raw = raw.get("backend", {})

    backend = BackendConfig(
        model=os.environ.get("REVIEW_BACKEND_MODEL", backend_raw.get("model", "claude-sonnet-4-5-20250929")),
        temperature=float(os.environ.get("REVIEW_BACKEND_TEMPERATURE", backend_raw.get("temperature", 0.0))),
        max_tokens=int(os.environ.get("REVIEW_BACKEND_MAX_TOKENS", backend_raw.get("max_tokens", 4096))),
        extra={k: v for k, v in backend_raw.items() if k not in {"model", "temperature", "max_tokens"}},
    )

    methods_raw = raw.get("methods", {})
    methods = {
        name: MethodConfig(
            prompt=cfg.get("prompt", ""),
            knowledge_base=cfg.get("knowledge_base", ""),
        )
        for name, cfg in methods_raw.items()
    }

    return ReviewConfig(backend=backend, methods=methods)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file using PyYAML."""
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
