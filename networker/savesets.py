"""networker/savesets.py — Saveset query endpoints."""

from __future__ import annotations


class SavesetsMixin:
    """Mixin providing /savesets endpoints for NWClient."""

    def list_savesets(
        self,
        client_name: str | None = None,
        save_path: str | None = None,
        level: str | None = None,
        extra_query: str | None = None,
    ) -> list[dict]:
        """Return savesets matching the given filters.

        Args:
            client_name:  Filter by client hostname.
            save_path:    Filter by save path / save set name.
            level:        Backup level: "Full", "Incremental", "Differential".
            extra_query:  Additional raw query string appended with comma.

        Returns:
            List of saveset dicts, each including ssid, name, level,
            savetime, and size fields.
        """
        parts: list[str] = []
        if client_name:
            parts.append(f"clientName:{client_name}")
        if save_path:
            parts.append(f"name:{save_path}")
        if level:
            parts.append(f"level:{level}")
        if extra_query:
            parts.append(extra_query)

        params: dict = {}
        if parts:
            params["q"] = ",".join(parts)

        return self._get("/savesets", params).get("savesets", [])

    def get_saveset(self, ssid: str) -> dict:
        """Return a single saveset by SSID."""
        return self._get(f"/savesets/{ssid}")

    def list_savesets_for_client(self, client_name: str) -> list[dict]:
        """Shorthand — return all savesets for a specific client."""
        return self.list_savesets(client_name=client_name)

    def latest_full_backup(self, client_name: str) -> dict | None:
        """Return the most recent Full-level saveset for a client, or None."""
        savesets = self.list_savesets(client_name=client_name, level="Full")
        if not savesets:
            return None
        return max(savesets, key=lambda s: s.get("saveTime", ""))
