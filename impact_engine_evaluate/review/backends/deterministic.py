"""Deterministic rule-based backend using CONFIDENCE_MAP scoring."""

from __future__ import annotations

import hashlib
import logging
import random
import re
from typing import Any

from impact_engine_evaluate.review.backends.base import Backend, BackendRegistry
from impact_engine_evaluate.scorer import CONFIDENCE_MAP, ModelType

logger = logging.getLogger(__name__)

# Lookup from model_type string values to ModelType enum members.
_MODEL_TYPE_LOOKUP: dict[str, ModelType] = {mt.value: mt for mt in ModelType}


@BackendRegistry.register("deterministic")
class DeterministicBackend(Backend):
    """Backend that scores artifacts using the deterministic CONFIDENCE_MAP rules.

    No LLM call is made.  The score is derived from the model type and a
    seeded RNG, exactly like the original ``score_initiative`` logic.

    Parameters
    ----------
    model : str
        Ignored — accepted for config symmetry with LLM backends.
    """

    name = "deterministic"

    def __init__(self, model: str = "deterministic", **kwargs: Any) -> None:
        self._model = model

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Produce a structured review response from deterministic rules.

        Extracts ``model_type``, ``sample_size``, and dimension names from
        the rendered prompt messages, then scores each dimension using the
        ``CONFIDENCE_MAP`` range and a seeded RNG.

        Parameters
        ----------
        messages : list[dict[str, str]]
            Rendered chat messages.
        model : str | None
            Ignored.
        temperature : float
            Ignored.
        max_tokens : int
            Ignored.
        response_format : dict | None
            Ignored.

        Returns
        -------
        str
            Structured text in ``DIMENSION/SCORE/JUSTIFICATION/OVERALL`` format.
        """
        full_text = "\n".join(m["content"] for m in messages)
        model_type_str = _extract_field(full_text, "Model type")
        sample_size_str = _extract_field(full_text, "Sample size")
        dimensions = _extract_dimensions(full_text)

        model_type = _MODEL_TYPE_LOOKUP.get(model_type_str)
        conf_range = CONFIDENCE_MAP.get(model_type) if model_type else None

        # Seed from the full message content for deterministic reproducibility.
        seed = int(hashlib.md5(full_text.encode()).hexdigest(), 16) % 2**32
        rng = random.Random(seed)

        if conf_range is None:
            lo, hi = 0.0, 1.0
            justification_base = "No CONFIDENCE_MAP entry; defaulting to full range."
        else:
            lo, hi = conf_range
            justification_base = f"Deterministic score for {model_type_str} (range {lo:.2f}\u2013{hi:.2f})"
            if sample_size_str:
                justification_base += f", sample size {sample_size_str}"

        lines: list[str] = []
        scores: list[float] = []
        for dim in dimensions:
            score = rng.uniform(lo, hi)
            scores.append(score)
            lines.append(f"DIMENSION: {dim}")
            lines.append(f"SCORE: {score:.4f}")
            lines.append(f"JUSTIFICATION: {justification_base}.")
            lines.append("")

        overall = sum(scores) / len(scores) if scores else rng.uniform(lo, hi)
        lines.append(f"OVERALL: {overall:.4f}")

        return "\n".join(lines)


def _extract_field(text: str, label: str) -> str:
    """Extract a ``Label: value`` field from rendered message text."""
    match = re.search(rf"{re.escape(label)}:\s*(.+)", text)
    return match.group(1).strip() if match else ""


def _extract_dimensions(text: str) -> list[str]:
    """Extract dimension names from the system message.

    Looks for patterns like ``"these dimensions: a, b, c"`` or
    ``"dimensions: a, b, and c"``.
    """
    match = re.search(r"dimensions?:\s*(.+?)(?:\.\s|\n\n)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return ["confidence"]
    raw = match.group(1)
    # Split on commas and newlines, then clean up "and" prefixes
    parts = re.split(r"[,\n]+", raw)
    dims = []
    for p in parts:
        p = p.strip().rstrip(".")
        p = re.sub(r"^and\s+", "", p)
        if p:
            dims.append(p)
    return dims or ["confidence"]
