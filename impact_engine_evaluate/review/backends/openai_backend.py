"""OpenAI / Azure OpenAI LLM backend."""

from __future__ import annotations

import logging
from typing import Any

from impact_engine_evaluate.review.backends.base import Backend, BackendRegistry

logger = logging.getLogger(__name__)

try:
    import openai

    _HAS_OPENAI = True
except ImportError:  # pragma: no cover
    _HAS_OPENAI = False


@BackendRegistry.register("openai")
class OpenAIBackend(Backend):
    """Backend powered by the OpenAI Chat Completions API.

    Parameters
    ----------
    model : str
        Default model identifier (e.g. ``"gpt-4o"``).
    api_key : str | None
        OpenAI API key.  Falls back to ``OPENAI_API_KEY`` env var.
    base_url : str | None
        Custom base URL (for Azure OpenAI or compatible APIs).
    max_tokens : int
        Default max tokens for completions.
    """

    name = "openai"

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
        max_tokens: int = 4096,
    ) -> None:
        if not _HAS_OPENAI:
            msg = "The 'openai' package is required: pip install openai"
            raise ImportError(msg)
        self._model = model
        self._max_tokens = max_tokens
        kwargs: dict[str, Any] = {}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        self._client = openai.OpenAI(**kwargs)

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Call the OpenAI Chat Completions API.

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
            Optional response format (e.g. ``{"type": "json_object"}``).

        Returns
        -------
        str
        """
        kwargs: dict[str, Any] = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        logger.debug("OpenAI request model=%s messages=%d", kwargs["model"], len(messages))
        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
