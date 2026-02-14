"""Anthropic (Claude) LLM backend."""

from __future__ import annotations

import logging
from typing import Any

from impact_engine_evaluate.review.backends.base import Backend, BackendRegistry

logger = logging.getLogger(__name__)

try:
    import anthropic

    _HAS_ANTHROPIC = True
except ImportError:  # pragma: no cover
    _HAS_ANTHROPIC = False


@BackendRegistry.register("anthropic")
class AnthropicBackend(Backend):
    """Backend powered by the Anthropic Messages API.

    Parameters
    ----------
    model : str
        Default model identifier (e.g. ``"claude-sonnet-4-5-20250929"``).
    api_key : str | None
        Anthropic API key.  Falls back to ``ANTHROPIC_API_KEY`` env var.
    max_tokens : int
        Default max tokens for completions.
    """

    name = "anthropic"

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        api_key: str | None = None,
        max_tokens: int = 4096,
    ) -> None:
        if not _HAS_ANTHROPIC:
            msg = "The 'anthropic' package is required: pip install anthropic"
            raise ImportError(msg)
        self._model = model
        self._max_tokens = max_tokens
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Call the Anthropic Messages API.

        Parameters
        ----------
        messages : list[dict[str, str]]
            Chat messages with ``role`` and ``content`` keys.
        model : str | None
            Override the default model.
        temperature : float
            Sampling temperature.
        max_tokens : int
            Maximum tokens in the response.
        response_format : dict | None
            Ignored for Anthropic (reserved for future structured output).

        Returns
        -------
        str
        """
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        chat_messages = [m for m in messages if m["role"] != "system"]

        kwargs: dict[str, Any] = {
            "model": model or self._model,
            "max_tokens": max_tokens or self._max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }
        if system_parts:
            kwargs["system"] = "\n\n".join(system_parts)

        logger.debug("Anthropic request model=%s messages=%d", kwargs["model"], len(chat_messages))
        response = self._client.messages.create(**kwargs)
        return response.content[0].text
