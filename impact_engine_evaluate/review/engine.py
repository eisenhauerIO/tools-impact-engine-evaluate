"""ReviewEngine: orchestrates a single artifact review."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from impact_engine_evaluate.config import ReviewConfig, load_config
from impact_engine_evaluate.review.backends import BackendRegistry
from impact_engine_evaluate.review.backends.base import Backend
from impact_engine_evaluate.review.models import ArtifactPayload, PromptSpec, ReviewDimension, ReviewResult

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

    Uses Jinja2 if available, otherwise falls back to ``str.format_map``.

    Parameters
    ----------
    spec : PromptSpec
        The prompt template to render.
    variables : dict[str, Any]
        Template variables.

    Returns
    -------
    list[dict[str, str]]
        Chat messages suitable for ``Backend.complete``.
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
    """Execute an artifact review using a configured backend.

    Parameters
    ----------
    backend : Backend
        LLM backend for completions.
    default_model : str | None
        Default model override for the backend.
    default_temperature : float
        Default temperature for completions.
    default_max_tokens : int
        Default max tokens for completions.
    """

    def __init__(
        self,
        backend: Backend,
        *,
        default_model: str | None = None,
        default_temperature: float = 0.0,
        default_max_tokens: int = 4096,
    ) -> None:
        self._backend = backend
        self._default_model = default_model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens

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

        backend = BackendRegistry.create(
            config.backend.type,
            model=config.backend.model,
            **config.backend.extra,
        )

        return cls(
            backend=backend,
            default_model=config.backend.model,
            default_temperature=config.backend.temperature,
            default_max_tokens=config.backend.max_tokens,
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

        # Render and call backend
        messages = render(spec, variables)
        used_model = model or self._default_model or ""
        raw_response = self._backend.complete(
            messages,
            model=model or self._default_model,
            temperature=temperature if temperature is not None else self._default_temperature,
            max_tokens=max_tokens or self._default_max_tokens,
        )

        # Parse response
        dimensions = _parse_dimensions(raw_response, spec.dimensions)
        overall = _parse_overall(raw_response, dimensions)

        result = ReviewResult(
            initiative_id=artifact.initiative_id,
            prompt_name=spec.name,
            prompt_version=spec.version,
            backend_name=self._backend.name,
            model=used_model,
            dimensions=dimensions,
            overall_score=overall,
            raw_response=raw_response,
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
# Response parsing
# ---------------------------------------------------------------------------


def _parse_dimensions(response: str, expected: list[str]) -> list[ReviewDimension]:
    """Parse DIMENSION/SCORE/JUSTIFICATION blocks from a response.

    Also attempts JSON parsing as a fallback.

    Parameters
    ----------
    response : str
        Raw LLM response text.
    expected : list[str]
        Expected dimension names (for fallback ordering).

    Returns
    -------
    list[ReviewDimension]
    """
    dimensions: list[ReviewDimension] = []

    # Try structured text parsing first
    pattern = re.compile(
        r"DIMENSION:\s*(?P<name>\S+)\s*\n"
        r"SCORE:\s*(?P<score>[\d.]+)\s*\n"
        r"JUSTIFICATION:\s*(?P<justification>.+?)(?=\nDIMENSION:|\nOVERALL:|\Z)",
        re.DOTALL,
    )
    for match in pattern.finditer(response):
        try:
            score = float(match.group("score"))
        except ValueError:
            score = 0.0
        dimensions.append(
            ReviewDimension(
                name=match.group("name").strip(),
                score=max(0.0, min(1.0, score)),
                justification=match.group("justification").strip(),
            )
        )

    if dimensions:
        return dimensions

    # Fallback: try JSON
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "dimensions" in data:
            for d in data["dimensions"]:
                dimensions.append(
                    ReviewDimension(
                        name=d.get("name", "unknown"),
                        score=max(0.0, min(1.0, float(d.get("score", 0.0)))),
                        justification=d.get("justification", ""),
                    )
                )
    except (json.JSONDecodeError, TypeError, KeyError):
        pass

    return dimensions


def _parse_overall(response: str, dimensions: list[ReviewDimension]) -> float:
    """Extract the overall score from the response, or compute from dimensions.

    Parameters
    ----------
    response : str
        Raw LLM response text.
    dimensions : list[ReviewDimension]
        Parsed dimensions for fallback averaging.

    Returns
    -------
    float
    """
    match = re.search(r"OVERALL:\s*([\d.]+)", response)
    if match:
        try:
            return max(0.0, min(1.0, float(match.group(1))))
        except ValueError:
            pass

    if dimensions:
        return sum(d.score for d in dimensions) / len(dimensions)

    return 0.0


# ---------------------------------------------------------------------------
# Internal YAML loading
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, using PyYAML if available, else a minimal parser."""
    try:
        import yaml

        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        return _minimal_yaml_load(path)


def _minimal_yaml_load(path: Path) -> dict[str, Any]:
    """Minimal YAML-subset parser for prompt template files.

    Handles top-level scalar keys, lists, and multiline ``|`` blocks.
    Install PyYAML for full YAML support.
    """
    result: dict[str, Any] = {}
    current_key: str | None = None
    block_lines: list[str] = []
    block_indent: int | None = None
    key = ""

    def _flush() -> None:
        if current_key and block_lines:
            result[current_key] = "\n".join(block_lines)

    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")

            if current_key is None and (not line.strip() or line.strip().startswith("#")):
                continue

            if current_key is not None:
                stripped = line.lstrip()
                indent = len(line) - len(stripped)
                if block_indent is None:
                    if stripped:
                        block_indent = indent
                    else:
                        block_lines.append("")
                        continue

                if indent >= block_indent and stripped:
                    block_lines.append(line[block_indent:])
                    continue
                elif not stripped:
                    block_lines.append("")
                    continue
                else:
                    _flush()
                    current_key = None
                    block_lines = []
                    block_indent = None

            if ":" in line and not line[0].isspace():
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if value == "|":
                    current_key = key
                    block_lines = []
                    block_indent = None
                elif value.startswith("["):
                    items = value.strip("[]").split(",")
                    result[key] = [i.strip().strip("\"'") for i in items if i.strip()]
                elif value.startswith("-"):
                    result[key] = [value.lstrip("- ").strip("\"'")]
                else:
                    result[key] = value.strip("\"'")

            elif line.strip().startswith("- ") and isinstance(result.get(key), list):
                result[key].append(line.strip().lstrip("- ").strip("\"'"))

    _flush()
    return result


def _render_template(template: str, variables: dict[str, Any]) -> str:
    """Render a single template string with Jinja2 or fallback."""
    if not template:
        return ""
    try:
        import jinja2

        env = jinja2.Environment(undefined=jinja2.Undefined)
        return env.from_string(template).render(**variables)
    except ImportError:
        converted = re.sub(r"\{\{-?\s*", "{", template)
        converted = re.sub(r"\s*-?\}\}", "}", converted)
        converted = re.sub(r"\{%.*?%\}", "", converted)
        try:
            return converted.format_map(variables)
        except KeyError:
            return converted
