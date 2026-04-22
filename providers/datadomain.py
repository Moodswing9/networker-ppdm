"""Data Domain provider wrapper for the unified orchestrator layer."""

from __future__ import annotations

from typing import Any

from datadomain import DDClient

from .base import BaseProvider


class DataDomainProvider(BaseProvider):
    """Thin provider adapter over :class:`datadomain.DDClient`."""

    name = "datadomain"

    def healthcheck(self) -> dict[str, Any]:
        try:
            with DDClient.from_env() as client:
                ddboost = client.ddboost_status()
                fs = client.filesystem_stats()
                return {
                    "provider": self.name,
                    "ok": True,
                    "ddboost_status": ddboost,
                    "filesystem": fs,
                }
        except Exception as exc:  # pragma: no cover - exercised via mocks/tests
            return {"provider": self.name, "ok": False, "error": str(exc)}

    def status(self) -> dict[str, Any]:
        with DDClient.from_env() as client:
            return {
                "provider": self.name,
                "ddboost_status": client.ddboost_status(),
                "filesystem": client.filesystem_stats(),
                "system": client.system_info(),
            }
