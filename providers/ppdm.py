"""PPDM provider wrapper for the unified orchestrator layer."""

from __future__ import annotations

from typing import Any

from ppdm import PPDMClient

from .base import BaseProvider, ProviderError


class PPDMProvider(BaseProvider):
    """Thin provider adapter over :class:`ppdm.PPDMClient`."""

    name = "ppdm"

    def healthcheck(self) -> dict[str, Any]:
        try:
            with PPDMClient.from_env() as client:
                policies = client.list_policies()
                running = client.running_activities()
                failed = client.failed_activities()
                return {
                    "provider": self.name,
                    "ok": True,
                    "policy_count": len(policies),
                    "running_activities": len(running),
                    "failed_activities": len(failed),
                }
        except Exception as exc:  # pragma: no cover - exercised via mocks/tests
            return {"provider": self.name, "ok": False, "error": str(exc)}

    def trigger_backup(self, policy_name: str) -> dict[str, Any]:
        with PPDMClient.from_env() as client:
            policy = client.get_policy_by_name(policy_name)
            if not policy:
                raise ProviderError(f"PPDM policy not found: {policy_name}")
            result = client.trigger_backup(policy["id"])
            return {
                "provider": self.name,
                "action": "trigger_backup",
                "policy": policy_name,
                "result": result,
            }

    def inventory(self) -> list[dict[str, Any]]:
        with PPDMClient.from_env() as client:
            assets = client.list_assets()
            rows: list[dict[str, Any]] = []
            for asset in assets:
                rows.append(
                    {
                        "platform": "PPDM",
                        "asset_name": asset.get("name"),
                        "asset_id": asset.get("id"),
                        "asset_type": asset.get("type") or asset.get("assetType"),
                    }
                )
            return rows
