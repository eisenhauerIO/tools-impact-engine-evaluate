"""Shared job directory reader: build scorer events from job artifacts."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from impact_engine_evaluate.review.manifest import Manifest

logger = logging.getLogger(__name__)


def load_scorer_event(
    manifest: Manifest,
    job_dir: str | Path,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a scorer event dict from a job directory's ``impact_results.json``.

    Parameters
    ----------
    manifest : Manifest
        Parsed job manifest.
    job_dir : str | Path
        Path to the job directory.
    overrides : dict[str, Any] | None
        Optional overrides (e.g. ``cost_to_scale`` from the orchestrator event).

    Returns
    -------
    dict[str, Any]
        Flat dict with keys ``initiative_id``, ``model_type``, ``ci_upper``,
        ``effect_estimate``, ``ci_lower``, ``cost_to_scale``, and
        ``sample_size``.

    Raises
    ------
    FileNotFoundError
        If ``impact_results.json`` is not found in the job directory.
    """
    job_dir = Path(job_dir)
    results_path = job_dir / "impact_results.json"

    if not results_path.exists():
        msg = f"Impact results not found: {results_path}"
        raise FileNotFoundError(msg)

    with open(results_path, encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)

    event: dict[str, Any] = {
        "initiative_id": manifest.initiative_id or job_dir.name,
        "model_type": manifest.model_type,
        "ci_upper": float(data.get("ci_upper", 0.0)),
        "effect_estimate": float(data.get("effect_estimate", 0.0)),
        "ci_lower": float(data.get("ci_lower", 0.0)),
        "cost_to_scale": float(data.get("cost_to_scale", 0.0)),
        "sample_size": int(data.get("sample_size", 0)),
    }

    if overrides:
        event.update(overrides)

    logger.debug("Loaded scorer event from %s: initiative_id=%s", results_path, event["initiative_id"])

    return event
