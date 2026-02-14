"""Abstract backend protocol and registry for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Backend(ABC):
    """LLM backend that can produce completions.

    Subclasses must set ``name`` and implement ``complete``.
    """

    name: str = ""

    @abstractmethod
    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Return the assistant's text response.

        Parameters
        ----------
        messages : list[dict[str, str]]
            Chat messages (``role`` / ``content`` dicts).
        model : str | None
            Override the default model for this call.
        temperature : float
            Sampling temperature.
        max_tokens : int
            Maximum tokens in the response.
        response_format : dict | None
            Optional structured-output hint (backend-specific).

        Returns
        -------
        str
            The assistant's text completion.
        """


class BackendRegistry:
    """Discover and instantiate registered LLM backends."""

    _backends: dict[str, type[Backend]] = {}

    @classmethod
    def register(cls, name: str):
        """Class decorator that registers a backend under *name*.

        Parameters
        ----------
        name : str
            Lookup key used in configuration files.

        Returns
        -------
        Callable
            The original class, unmodified.
        """

        def decorator(klass: type[Backend]) -> type[Backend]:
            cls._backends[name] = klass
            return klass

        return decorator

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> Backend:
        """Instantiate a registered backend.

        Parameters
        ----------
        name : str
            Registered backend name.
        **kwargs
            Forwarded to the backend constructor.

        Returns
        -------
        Backend

        Raises
        ------
        KeyError
            If *name* is not registered.
        """
        if name not in cls._backends:
            available = ", ".join(sorted(cls._backends)) or "(none)"
            msg = f"Unknown backend {name!r}. Available: {available}"
            raise KeyError(msg)
        return cls._backends[name](**kwargs)

    @classmethod
    def available(cls) -> list[str]:
        """Return sorted list of registered backend names."""
        return sorted(cls._backends)
