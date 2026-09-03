"""Provider contract. Flask and translation logic are provider-agnostic."""

from abc import ABC, abstractmethod
from typing import Any


class AIProviderError(RuntimeError):
    """A friendly, expected failure while contacting an AI provider."""


class AIProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        """Return a decoded, schema-constrained provider response."""
