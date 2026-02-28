"""Job directory manifest: load, validate, and update."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "manifest.json"


@dataclass
class FileEntry:
    """A single file reference within a manifest.

    Parameters
    ----------
    path : str
        Relative path to the file within the job directory.
    format : str
        File format identifier (e.g. ``"json"``, ``"yaml"``, ``"csv"``).
    """

    path: str
    format: str


@dataclass
class Manifest:
    """Parsed manifest for a job directory.

    Parameters
    ----------
    schema_version : str
        Manifest schema version.
    model_type : str
        Causal inference methodology label.
    created_at : str
        ISO-8601 creation timestamp.
    files : dict[str, FileEntry]
        Mapping of logical names to file entries.
    initiative_id : str
        Initiative identifier. Defaults to the job directory name.
    evaluate_strategy : str
        Evaluation strategy: ``"agentic"`` (LLM review) or
        ``"deterministic"`` (confidence range scoring). Defaults to
        ``"agentic"``.
    """

    schema_version: str
    model_type: str
    created_at: str = ""
    files: dict[str, FileEntry] = field(default_factory=dict)
    initiative_id: str = ""
    evaluate_strategy: str = "agentic"


def load_manifest(job_dir: str | Path) -> Manifest:
    """Load and validate a manifest from a job directory.

    Parameters
    ----------
    job_dir : str | Path
        Path to the job directory containing ``manifest.json``.

    Returns
    -------
    Manifest

    Raises
    ------
    FileNotFoundError
        If ``manifest.json`` does not exist.
    ValueError
        If required fields are missing.
    """
    job_dir = Path(job_dir)
    manifest_path = job_dir / MANIFEST_FILENAME

    if not manifest_path.exists():
        msg = f"Manifest not found: {manifest_path}"
        raise FileNotFoundError(msg)

    with open(manifest_path, encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)

    # Validate required fields
    for key in ("schema_version", "model_type"):
        if key not in data:
            msg = f"Manifest missing required field: {key!r}"
            raise ValueError(msg)

    files: dict[str, FileEntry] = {}
    for name, entry in data.get("files", {}).items():
        files[name] = FileEntry(path=entry["path"], format=entry["format"])

    initiative_id = data.get("initiative_id", "") or job_dir.name

    logger.debug("Loaded manifest from %s: model_type=%s", manifest_path, data["model_type"])

    return Manifest(
        schema_version=data["schema_version"],
        model_type=data["model_type"],
        created_at=data.get("created_at", ""),
        files=files,
        initiative_id=initiative_id,
        evaluate_strategy=data.get("evaluate_strategy", "agentic"),
    )


def update_manifest(job_dir: str | Path, key: str, entry: FileEntry) -> None:
    """Append a file entry to an existing manifest.

    Parameters
    ----------
    job_dir : str | Path
        Path to the job directory.
    key : str
        Logical name for the file entry.
    entry : FileEntry
        The file entry to add.
    """
    job_dir = Path(job_dir)
    manifest_path = job_dir / MANIFEST_FILENAME

    with open(manifest_path, encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)

    data.setdefault("files", {})[key] = {"path": entry.path, "format": entry.format}

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")

    logger.debug("Updated manifest %s: added %s", manifest_path, key)
