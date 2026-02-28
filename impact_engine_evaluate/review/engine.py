"""ReviewEngine: orchestrates a single artifact review."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jinja2
import litellm
import yaml

from impact_engine_evaluate.config import ReviewConfig, load_config
from impact_engine_evaluate.review.models import (
    ArtifactPayload,
    PromptSpec,
    ReviewDimension,
    ReviewResponse,
    ReviewResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt loading and rendering utilities
# ---------------------------------------------------------------------------


def load_prompt_spec(path: Path) -> PromptSpec:
    """Load a PromptSpec from a YAML file.

    Parameters
    ----------
    path : Path
        Path to a YAML prompt template file.

    Returns
    -------
    PromptSpec

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    """
    if not path.exists():
        msg = f"Prompt template not found: {path}"
        raise FileNotFoundError(msg)

    data = _load_yaml(path)
    dims = data.get("dimensions", [])
    if isinstance(dims, str):
        dims = [d.strip() for d in dims.split(",")]
    return PromptSpec(
        name=data.get("name", "unknown"),
        version=str(data.get("version", "0.0")),
        description=data.get("description", ""),
        dimensions=dims,
        system_template=data.get("system", ""),
        user_template=data.get("user", ""),
    )


def render(spec: PromptSpec, variables: dict[str, Any]) -> list[dict[str, str]]:
    """Render a prompt spec into chat messages.

    Parameters
    ----------
    spec : PromptSpec
        The prompt template to render.
    variables : dict[str, Any]
        Template variables.

    Returns
    -------
    list[dict[str, str]]
        Chat messages suitable for LLM completion.
    """
    system_text = _render_template(spec.system_template, variables)
    user_text = _render_template(spec.user_template, variables)

    messages: list[dict[str, str]] = []
    if system_text:
        messages.append({"role": "system", "content": system_text})
    if user_text:
        messages.append({"role": "user", "content": user_text})
    return messages


def load_knowledge(directory: Path) -> str:
    """Concatenate all ``.md`` and ``.txt`` files in a directory.

    Parameters
    ----------
    directory : Path
        Directory containing knowledge files.

    Returns
    -------
    str
        Combined content separated by section dividers.
    """
    if not directory.is_dir():
        return ""

    parts: list[str] = []
    for ext in ("*.md", "*.txt"):
        for filepath in sorted(directory.glob(ext)):
            content = filepath.read_text(encoding="utf-8")
            parts.append(content)
            logger.debug("Loaded knowledge file: %s (%d chars)", filepath, len(content))

    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# ReviewEngine
# ---------------------------------------------------------------------------


class ReviewEngine:
    """Execute an artifact review via LiteLLM.

    Parameters
    ----------
    default_model : str
        Default model identifier for completions.
    default_temperature : float
        Default temperature for completions.
    default_max_tokens : int
        Default max tokens for completions.
    litellm_extra : dict[str, Any] | None
        Additional kwargs forwarded to ``litellm.completion()``.
    """

    def __init__(
        self,
        *,
        default_model: str = "claude-sonnet-4-5-20250929",
        default_temperature: float = 0.0,
        default_max_tokens: int = 4096,
        litellm_extra: dict[str, Any] | None = None,
    ) -> None:
        self._default_model = default_model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._litellm_extra = litellm_extra or {}

    @classmethod
    def from_config(cls, config: ReviewConfig | dict | str | None = None) -> ReviewEngine:
        """Construct a ReviewEngine from a config object or raw source.

        Parameters
        ----------
        config : ReviewConfig | dict | str | None
            A ``ReviewConfig``, a dict, a YAML file path, or ``None``
            for defaults.

        Returns
        -------
        ReviewEngine
        """
        if not isinstance(config, ReviewConfig):
            config = load_config(config)

        return cls(
            default_model=config.backend.model,
            default_temperature=config.backend.temperature,
            default_max_tokens=config.backend.max_tokens,
            litellm_extra=config.backend.extra,
        )

    def review(
        self,
        artifact: ArtifactPayload,
        spec: PromptSpec,
        knowledge_context: str = "",
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ReviewResult:
        """Execute a review of the given artifact.

        Parameters
        ----------
        artifact : ArtifactPayload
            The artifact to review.
        spec : PromptSpec
            Prompt template specification.
        knowledge_context : str
            Pre-loaded domain knowledge text.
        model : str | None
            Model override for this call.
        temperature : float | None
            Temperature override for this call.
        max_tokens : int | None
            Max tokens override for this call.

        Returns
        -------
        ReviewResult
        """
        # Build template variables
        variables: dict[str, Any] = {
            "artifact": artifact.artifact_text,
            "model_type": artifact.model_type,
            "sample_size": artifact.sample_size,
            "knowledge_context": knowledge_context,
            **artifact.metadata,
        }

        # Render and call LiteLLM
        messages = render(spec, variables)
        used_model = model or self._default_model

        kwargs: dict[str, Any] = {
            "model": used_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self._default_temperature,
            "max_tokens": max_tokens or self._default_max_tokens,
            "response_format": ReviewResponse,
            **self._litellm_extra,
        }
        logger.debug("litellm request model=%s messages=%d", kwargs["model"], len(messages))
        response = litellm.completion(**kwargs)
        parsed: ReviewResponse = response.choices[0].message.parsed

        # Convert structured response to dataclass models
        dimensions = [
            ReviewDimension(name=d.name, score=d.score, justification=d.justification) for d in parsed.dimensions
        ]
        overall = parsed.overall

        result = ReviewResult(
            initiative_id=artifact.initiative_id,
            prompt_name=spec.name,
            prompt_version=spec.version,
            backend_name="litellm",
            model=used_model,
            dimensions=dimensions,
            overall_score=overall,
            raw_response=parsed.model_dump_json(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            "Reviewed initiative=%s prompt=%s overall=%.3f",
            result.initiative_id,
            result.prompt_name,
            result.overall_score,
        )
        return result


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file."""
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _render_template(template: str, variables: dict[str, Any]) -> str:
    """Render a Jinja2 template string."""
    if not template:
        return ""
    env = jinja2.Environment(undefined=jinja2.Undefined)
    return env.from_string(template).render(**variables)
