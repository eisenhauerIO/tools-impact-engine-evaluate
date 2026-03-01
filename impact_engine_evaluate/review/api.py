"""Public API: review a job directory."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from impact_engine_evaluate.config import load_config
from impact_engine_evaluate.review.engine import ReviewEngine, load_knowledge, load_prompt_spec
from impact_engine_evaluate.review.knowledge_registry import load_knowledge_base
from impact_engine_evaluate.review.manifest import load_manifest
from impact_engine_evaluate.review.methods import MethodReviewerRegistry
from impact_engine_evaluate.review.models import ReviewResult
from impact_engine_evaluate.review.prompt_registry import load_prompt

logger = logging.getLogger(__name__)

REVIEW_RESULT_FILENAME = "review_result.json"


def compute_review(
    job_dir: str | Path,
    *,
    config: dict | str | None = None,
) -> ReviewResult:
    """Compute a review of a job directory without writing results.

    Suitable for evaluation loops and batch processing where writing back
    to the job directory is unwanted.

    Prompt and knowledge base are resolved in this order:

    1. If ``config.methods[model_type].prompt`` is set, the named prompt is
       loaded from the prompt registry.
    2. Otherwise the reviewer's default ``prompt_template_dir()`` is used.

    The same precedence applies to ``knowledge_base``.

    Parameters
    ----------
    job_dir : str | Path
        Path to the job directory containing ``manifest.json``.
    config : ReviewConfig | dict | str | None
        Backend and method configuration.  A ``ReviewConfig``, a dict, a YAML
        file path, or ``None`` for defaults.

    Returns
    -------
    ReviewResult

    Raises
    ------
    FileNotFoundError
        If the manifest or prompt template is missing.
    KeyError
        If the manifest's ``model_type`` has no registered method reviewer, or
        a configured prompt / knowledge base name is not registered.
    """
    job_dir = Path(job_dir)
    config_dict = load_config(config)

    manifest = load_manifest(job_dir)
    logger.info("Reviewing job_dir=%s model_type=%s", job_dir, manifest.model_type)

    reviewer = MethodReviewerRegistry.create(manifest.model_type)
    artifact = reviewer.load_artifact(manifest, job_dir)

    method = config_dict.get("methods", {}).get(manifest.model_type, {})

    # Prompt: registry name takes precedence over reviewer default directory
    if method.get("prompt", ""):
        spec = load_prompt(method["prompt"])
    else:
        template_dir = reviewer.prompt_template_dir()
        if template_dir is None:
            msg = f"Method {reviewer.name!r} does not provide a prompt template directory"
            raise FileNotFoundError(msg)
        spec = load_prompt_spec(template_dir / f"{reviewer.prompt_name}.yaml")

    # Knowledge base: registry name takes precedence over reviewer default directory
    if method.get("knowledge_base", ""):
        knowledge_context = load_knowledge_base(method["knowledge_base"])
    else:
        knowledge_dir = reviewer.knowledge_content_dir()
        knowledge_context = load_knowledge(knowledge_dir) if knowledge_dir is not None else ""

    engine = ReviewEngine.from_config(config_dict)
    return engine.review(artifact, spec, knowledge_context)


def review(
    job_dir: str | Path,
    *,
    config: dict | str | None = None,
) -> ReviewResult:
    """Review a job directory and write results back.

    Calls :func:`compute_review` then writes ``review_result.json`` to the
    job directory.

    Parameters
    ----------
    job_dir : str | Path
        Path to the job directory containing ``manifest.json``.
    config : ReviewConfig | dict | str | None
        Backend and method configuration.  A ``ReviewConfig``, a dict, a YAML
        file path, or ``None`` for defaults.

    Returns
    -------
    ReviewResult

    Raises
    ------
    FileNotFoundError
        If the manifest or prompt template is missing.
    KeyError
        If the manifest's ``model_type`` has no registered method reviewer, or
        a configured prompt / knowledge base name is not registered.
    """
    job_dir = Path(job_dir)
    result = compute_review(job_dir, config=config)
    result_path = job_dir / REVIEW_RESULT_FILENAME
    result_path.write_text(json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote review result to %s", result_path)
    return result
