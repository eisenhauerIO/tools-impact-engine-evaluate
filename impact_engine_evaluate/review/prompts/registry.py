"""Prompt template discovery and registration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from impact_engine_evaluate.review.models import PromptSpec

logger = logging.getLogger(__name__)

_BUILTIN_DIR = Path(__file__).parent / "templates"


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, using PyYAML if available, else a minimal parser."""
    try:
        import yaml

        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        return _minimal_yaml_load(path)


def _minimal_yaml_load(path: Path) -> dict[str, Any]:
    """Minimal YAML-subset parser for simple prompt files.

    Handles top-level scalar keys and multiline ``|`` blocks.
    Sufficient for the built-in template format; install PyYAML for
    full YAML support.
    """
    result: dict[str, Any] = {}
    current_key: str | None = None
    block_lines: list[str] = []
    block_indent: int | None = None

    def _flush() -> None:
        if current_key and block_lines:
            result[current_key] = "\n".join(block_lines)

    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")

            # Skip comments and blank lines outside blocks
            if current_key is None and (not line.strip() or line.strip().startswith("#")):
                continue

            # Detect block continuation
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

            # Top-level key: value
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


def _spec_from_dict(data: dict[str, Any]) -> PromptSpec:
    """Convert a loaded YAML dict into a PromptSpec."""
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


class PromptRegistry:
    """Discover, cache, and retrieve prompt templates.

    Parameters
    ----------
    extra_dirs : list[str | Path] | None
        Additional directories to scan for ``.yaml`` prompt files.
    """

    def __init__(self, extra_dirs: list[str | Path] | None = None) -> None:
        self._specs: dict[str, PromptSpec] = {}
        self._scan(_BUILTIN_DIR)
        for d in extra_dirs or []:
            self._scan(Path(d))

    def _scan(self, directory: Path) -> None:
        """Scan *directory* for YAML prompt templates."""
        if not directory.is_dir():
            logger.warning("Prompt directory does not exist: %s", directory)
            return
        for path in sorted(directory.glob("*.yaml")):
            data = _load_yaml(path)
            spec = _spec_from_dict(data)
            self._specs[spec.name] = spec
            logger.debug("Loaded prompt %s v%s from %s", spec.name, spec.version, path)

    def get(self, name: str) -> PromptSpec:
        """Return a prompt spec by name.

        Parameters
        ----------
        name : str
            Registered prompt name.

        Returns
        -------
        PromptSpec

        Raises
        ------
        KeyError
            If *name* is not found.
        """
        if name not in self._specs:
            available = ", ".join(sorted(self._specs)) or "(none)"
            msg = f"Unknown prompt {name!r}. Available: {available}"
            raise KeyError(msg)
        return self._specs[name]

    def available(self) -> list[str]:
        """Return sorted list of registered prompt names."""
        return sorted(self._specs)

    def register(self, spec: PromptSpec) -> None:
        """Register a prompt spec programmatically.

        Parameters
        ----------
        spec : PromptSpec
            The prompt specification to register.
        """
        self._specs[spec.name] = spec
