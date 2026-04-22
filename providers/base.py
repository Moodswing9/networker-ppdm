"""Base abstractions for orchestration providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProviderError(RuntimeError):
    """Raised when a provider cannot complete a requested operation."""


class BaseProvider(ABC):
    """Abstract provider interface for backup platforms."""

    name: str

    @abstractmethod
    def healthcheck(self) -> dict[str, Any]:
        """Return a JSON-serializable health result."""
        raise NotImplementedError
