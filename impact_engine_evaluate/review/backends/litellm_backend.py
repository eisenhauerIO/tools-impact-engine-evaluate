"""LiteLLM catch-all backend supporting 100+ LLM providers."""

from __future__ import annotations

import logging
from typing import Any

from impact_engine_evaluate.review.backends.base import Backend, BackendRegistry

logger = logging.getLogger(__name__)

try:
    import litellm

    _HAS_LITELLM = True
except ImportError:  # pragma: no cover
    _HAS_LITELLM = False


@BackendRegistry.register("litellm")
class LiteLLMBackend(Backend):
    """Backend powered by LiteLLM's unified completion interface.

    Parameters
    ----------
    model : str
        Model identifier in LiteLLM format
        (e.g. ``"bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0"``).
    max_tokens : int
        Default max tokens for completions.
    """

    name = "litellm"

    def __init__(
        self,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
    ) -> None:
        if not _HAS_LITELLM:
            msg = "The 'litellm' package is required: pip install litellm"
            raise ImportError(msg)
        self._model = model
        self._max_tokens = max_tokens

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Call LiteLLM's unified completion endpoint.

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
            Optional response format hint.

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

        logger.debug("LiteLLM request model=%s messages=%d", kwargs["model"], len(messages))
        response = litellm.completion(**kwargs)
        return response.choices[0].message.content or ""
