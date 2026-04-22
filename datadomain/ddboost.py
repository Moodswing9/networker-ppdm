"""datadomain/ddboost.py — DDBoost management endpoints."""

from __future__ import annotations

_DDBOOST_PATH = "protocols/ddboost"
_SU_PATH      = "protocols/ddboost/storage-units"


class DDBoostMixin:
    """Mixin providing DDBoost endpoints for DDClient."""

    def ddboost_status(self) -> dict:
        """Return DDBoost service status and encryption settings."""
        return self._get(f"/{_DDBOOST_PATH}")

    def enable_ddboost(self) -> dict:
        """Enable the DDBoost service."""
        return self._put(f"/{_DDBOOST_PATH}", {"status": "enabled"})

    def disable_ddboost(self) -> dict:
        """Disable the DDBoost service."""
        return self._put(f"/{_DDBOOST_PATH}", {"status": "disabled"})

    # ── Storage units ─────────────────────────────────────────────────────────

    def list_storage_units(self) -> list[dict]:
        """Return all DDBoost storage units."""
        return self._get(f"/{_SU_PATH}").get("storage_units", [])

    def get_storage_unit(self, name: str) -> dict:
        """Return a single storage unit by name."""
        return self._get(f"/{_SU_PATH}/{name}")

    def create_storage_unit(
        self,
        name: str,
        user: str,
        soft_limit_tib: float | None = None,
        hard_limit_tib: float | None = None,
    ) -> dict:
        """Create a DDBoost storage unit.

        Args:
            name:           Storage unit name.
            user:           DDBoost user to own this unit.
            soft_limit_tib: Soft quota in TiB (None = unlimited).
            hard_limit_tib: Hard quota in TiB (None = unlimited).
        """
        body: dict = {"name": name, "user": user}
        if soft_limit_tib is not None or hard_limit_tib is not None:
            quota: dict = {}
            if soft_limit_tib is not None:
                quota["soft-limit"] = {"value": soft_limit_tib, "unit": "TiB"}
            if hard_limit_tib is not None:
                quota["hard-limit"] = {"value": hard_limit_tib, "unit": "TiB"}
            body["quota"] = quota
        return self._post(f"/{_SU_PATH}", body)

    def delete_storage_unit(self, name: str) -> None:
        """Delete a DDBoost storage unit."""
        self._delete(f"/{_SU_PATH}/{name}")

    def assign_user_to_storage_unit(
        self, unit_name: str, username: str, access: str = "read-write"
    ) -> dict:
        """Assign a DDBoost user to a storage unit.

        Args:
            unit_name: Storage unit name.
            username:  DDBoost username to assign.
            access:    "read-write" (default) or "read-only".
        """
        return self._put(
            f"/{_SU_PATH}/{unit_name}/users",
            {"name": username, "access": access},
        )
