"""Public API: review a job directory."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from impact_engine_evaluate.review.engine import ReviewEngine, load_knowledge, load_prompt_spec
from impact_engine_evaluate.review.manifest import load_manifest
from impact_engine_evaluate.review.methods import MethodReviewerRegistry
from impact_engine_evaluate.review.models import ReviewResult

logger = logging.getLogger(__name__)

REVIEW_RESULT_FILENAME = "review_result.json"


def review(job_dir: str | Path, *, config: dict | str | None = None) -> ReviewResult:
    """Review a job directory and write results back.

    Parameters
    ----------
    job_dir : str | Path
        Path to the job directory containing ``manifest.json``.
    config : dict | str | None
        Backend configuration. A dict, a YAML file path, or ``None``
        for defaults.

    Returns
    -------
    ReviewResult

    Raises
    ------
    FileNotFoundError
        If the manifest or prompt template is missing.
    KeyError
        If the manifest's ``model_type`` has no registered method reviewer.
    """
    job_dir = Path(job_dir)

    # 1. Read manifest
    manifest = load_manifest(job_dir)
    logger.info("Reviewing job_dir=%s model_type=%s", job_dir, manifest.model_type)

    # 2. Select method reviewer
    reviewer = MethodReviewerRegistry.create(manifest.model_type)

    # 3. Load artifact
    artifact = reviewer.load_artifact(manifest, job_dir)

    # 4. Load method-specific prompt and knowledge
    template_dir = reviewer.prompt_template_dir()
    if template_dir is None:
        msg = f"Method {reviewer.name!r} does not provide a prompt template directory"
        raise FileNotFoundError(msg)

    spec = load_prompt_spec(template_dir / f"{reviewer.prompt_name}.yaml")

    knowledge_context = ""
    knowledge_dir = reviewer.knowledge_content_dir()
    if knowledge_dir is not None:
        knowledge_context = load_knowledge(knowledge_dir)

    # 5. Run review
    engine = ReviewEngine.from_config(config)
    result = engine.review(artifact, spec, knowledge_context)

    # 6. Write result to job directory
    result_path = job_dir / REVIEW_RESULT_FILENAME
    result_path.write_text(json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote review result to %s", result_path)

    return result
