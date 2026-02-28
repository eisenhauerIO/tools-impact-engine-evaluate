"""Unified configuration for the review subsystem."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BackendConfig:
    """LLM backend configuration.

    Parameters
    ----------
    type : str
        Registered backend name (e.g. ``"anthropic"``, ``"openai"``).
    model : str
        Model identifier.
    temperature : float
        Sampling temperature.
    max_tokens : int
        Maximum tokens per completion.
    extra : dict
        Additional backend-specific kwargs.
    """

    type: str = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.0
    max_tokens: int = 4096
    extra: dict = field(default_factory=dict)


@dataclass
class ReviewConfig:
    """Top-level configuration for the review subsystem.

    Parameters
    ----------
    backend : BackendConfig
        LLM backend settings.
    """

    backend: BackendConfig = field(default_factory=BackendConfig)


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
        type=os.environ.get("REVIEW_BACKEND_TYPE", backend_raw.get("type", "anthropic")),
        model=os.environ.get("REVIEW_BACKEND_MODEL", backend_raw.get("model", "claude-sonnet-4-5-20250929")),
        temperature=float(os.environ.get("REVIEW_BACKEND_TEMPERATURE", backend_raw.get("temperature", 0.0))),
        max_tokens=int(os.environ.get("REVIEW_BACKEND_MAX_TOKENS", backend_raw.get("max_tokens", 4096))),
        extra={k: v for k, v in backend_raw.items() if k not in {"type", "model", "temperature", "max_tokens"}},
    )

    return ReviewConfig(backend=backend)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file using PyYAML."""
    try:
        import yaml

        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        msg = "PyYAML is required to load YAML config files: pip install pyyaml"
        raise ImportError(msg) from None
