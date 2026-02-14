"""Template rendering for prompt specs."""

from __future__ import annotations

from typing import Any

from impact_engine_evaluate.review.models import PromptSpec


def render(spec: PromptSpec, variables: dict[str, Any]) -> list[dict[str, str]]:
    """Render a prompt spec into chat messages.

    Uses Jinja2 if available, otherwise falls back to ``str.format_map``
    with ``{variable}`` syntax.

    Parameters
    ----------
    spec : PromptSpec
        The prompt template to render.
    variables : dict[str, Any]
        Template variables (e.g. ``artifact``, ``model_type``).

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


def _render_template(template: str, variables: dict[str, Any]) -> str:
    """Render a single template string."""
    if not template:
        return ""
    try:
        import jinja2

        env = jinja2.Environment(undefined=jinja2.Undefined)
        return env.from_string(template).render(**variables)
    except ImportError:
        # Fallback: convert Jinja2 {{ var }} to Python {var} for format_map.
        import re

        converted = re.sub(r"\{\{-?\s*", "{", template)
        converted = re.sub(r"\s*-?\}\}", "}", converted)
        # Strip Jinja2 block tags ({% ... %}) — they can't be emulated.
        converted = re.sub(r"\{%.*?%\}", "", converted)
        try:
            return converted.format_map(variables)
        except KeyError:
            return converted
