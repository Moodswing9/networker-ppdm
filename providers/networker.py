"""NetWorker provider wrapper for the unified orchestrator layer."""

from __future__ import annotations

from typing import Any

from networker import NWClient

from .base import BaseProvider


class NetworkerProvider(BaseProvider):
    """Thin provider adapter over :class:`networker.NWClient`."""

    name = "networker"

    def healthcheck(self) -> dict[str, Any]:
        try:
            with NWClient.from_env() as client:
                policies = client.list_policies()
                groups = client.list_protection_groups()
                return {
                    "provider": self.name,
                    "ok": True,
                    "policy_count": len(policies),
                    "group_count": len(groups),
                }
        except Exception as exc:  # pragma: no cover - exercised via mocks/tests
            return {"provider": self.name, "ok": False, "error": str(exc)}

    def trigger_group_backup(self, group_name: str) -> dict[str, Any]:
        with NWClient.from_env() as client:
            result = client.trigger_group_backup(group_name)
            return {
                "provider": self.name,
                "action": "trigger_group_backup",
                "group": group_name,
                "result": result,
            }

    def inventory(self, client_name: str | None = None) -> list[dict[str, Any]]:
        with NWClient.from_env() as client:
            rows: list[dict[str, Any]] = []
            if client_name:
                savesets = client.list_savesets_for_client(client_name)
                latest = client.latest_full_backup(client_name)
                rows.append(
                    {
                        "platform": "NetWorker",
                        "asset_name": client_name,
                        "asset_id": client_name,
                        "asset_type": "CLIENT",
                        "latest_full_backup": latest.get("saveTime") if latest else None,
                        "saveset_count": len(savesets),
                    }
                )
                return rows

            for item in client.list_clients():
                rows.append(
                    {
                        "platform": "NetWorker",
                        "asset_name": item.get("hostname") or item.get("name"),
                        "asset_id": item.get("id") or item.get("hostname") or item.get("name"),
                        "asset_type": "CLIENT",
                    }
                )
            return rows
