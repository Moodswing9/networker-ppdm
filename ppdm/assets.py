"""ppdm/assets.py — Asset management endpoints."""

from __future__ import annotations


class AssetsMixin:
    """Mixin providing /assets endpoints for PPDMClient."""

    def list_assets(
        self,
        asset_type: str | None = None,
        name: str | None = None,
        extra_filter: str | None = None,
        page_size: int = 100,
    ) -> list[dict]:
        """Return all assets, optionally filtered by type or name.

        Args:
            asset_type:    PPDM asset type string, e.g. "KUBERNETES", "VMWARE_VIRTUAL_MACHINE",
                           "ORACLE_DATABASE", "SQL_SERVER_DATABASE", "FILE_SYSTEM".
            name:          Filter by exact asset name.
            extra_filter:  Raw PPDM OData filter string appended with "and".
            page_size:     Number of results per page (default: 100).

        Returns:
            List of asset dicts.
        """
        filters: list[str] = []
        if asset_type:
            filters.append(f'type eq "{asset_type}"')
        if name:
            filters.append(f'name eq "{name}"')
        if extra_filter:
            filters.append(extra_filter)

        params: dict = {"pageSize": page_size}
        if filters:
            params["filter"] = " and ".join(filters)

        return self._get("/assets", params).get("content", [])

    def get_asset(self, asset_id: str) -> dict:
        """Return a single asset by ID."""
        return self._get(f"/assets/{asset_id}")

    def list_copies(self, asset_id: str) -> list[dict]:
        """Return all backup copies available for an asset.

        Useful before initiating a restore — pick the copyId with the desired
        createTime and pass it to PPDMClient.restore().
        """
        return self._get(f"/assets/{asset_id}/copies").get("content", [])

    def latest_copy(self, asset_id: str) -> dict | None:
        """Return the most recent backup copy for an asset, or None."""
        copies = self.list_copies(asset_id)
        if not copies:
            return None
        return max(copies, key=lambda c: c.get("createTime", ""))
