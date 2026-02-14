"""ReviewEngine: orchestrates a single artifact review."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from impact_engine_evaluate.config import ReviewConfig, load_config
from impact_engine_evaluate.review.backends import BackendRegistry
from impact_engine_evaluate.review.backends.base import Backend
from impact_engine_evaluate.review.knowledge.base import KnowledgeBase
from impact_engine_evaluate.review.knowledge.static import StaticKnowledgeBase
from impact_engine_evaluate.review.models import ArtifactPayload, ReviewDimension, ReviewResult
from impact_engine_evaluate.review.prompts.registry import PromptRegistry
from impact_engine_evaluate.review.prompts.renderer import render

logger = logging.getLogger(__name__)


class ReviewEngine:
    """Execute an artifact review using a configured backend, prompt, and knowledge base.

    Parameters
    ----------
    backend : Backend
        LLM backend for completions.
    prompt_registry : PromptRegistry
        Registry of available prompt templates.
    knowledge_base : KnowledgeBase | None
        Optional knowledge base for context retrieval.
    default_prompt : str
        Default prompt name when not specified in ``review()``.
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
        prompt_registry: PromptRegistry,
        knowledge_base: KnowledgeBase | None = None,
        default_prompt: str = "study_design_review",
        default_model: str | None = None,
        default_temperature: float = 0.0,
        default_max_tokens: int = 4096,
    ) -> None:
        self._backend = backend
        self._prompt_registry = prompt_registry
        self._knowledge_base = knowledge_base
        self._default_prompt = default_prompt
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

        prompt_registry = PromptRegistry(extra_dirs=config.prompt.template_dirs)

        knowledge_base: KnowledgeBase | None = None
        if config.knowledge and config.knowledge.path:
            if config.knowledge.type == "static":
                knowledge_base = StaticKnowledgeBase(config.knowledge.path)
            else:
                logger.warning("Unsupported knowledge base type: %s", config.knowledge.type)

        return cls(
            backend=backend,
            prompt_registry=prompt_registry,
            knowledge_base=knowledge_base,
            default_prompt=config.prompt.name,
            default_model=config.backend.model,
            default_temperature=config.backend.temperature,
            default_max_tokens=config.backend.max_tokens,
        )

    def review(
        self,
        artifact: ArtifactPayload,
        prompt_name: str | None = None,
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
        prompt_name : str | None
            Prompt template name. Falls back to the engine default.
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
        prompt_name = prompt_name or self._default_prompt
        spec = self._prompt_registry.get(prompt_name)

        # Retrieve knowledge context
        knowledge_context = ""
        if self._knowledge_base:
            chunks = self._knowledge_base.retrieve(artifact.artifact_text)
            if chunks:
                knowledge_context = "\n\n---\n\n".join(c.content for c in chunks)

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
