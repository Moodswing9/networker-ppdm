"""ppdm/activities.py — Activity (job) monitoring endpoints."""

from __future__ import annotations


# Valid PPDM activity states
STATES = {"RUNNING", "SUCCEEDED", "FAILED", "CANCELED", "CANCELING", "QUEUED"}


class ActivitiesMixin:
    """Mixin providing /activities endpoints for PPDMClient."""

    def list_activities(
        self,
        state: str | None = None,
        asset_type: str | None = None,
        category: str | None = None,
        page_size: int = 100,
    ) -> list[dict]:
        """Return activities, optionally filtered.

        Args:
            state:      "FAILED", "RUNNING", "SUCCEEDED", "CANCELED", etc.
            asset_type: e.g. "KUBERNETES", "VMWARE_VIRTUAL_MACHINE".
            category:   e.g. "PROTECT", "RESTORE", "REPLICATE".
            page_size:  Number of results per page.

        Returns:
            List of activity dicts.
        """
        filters: list[str] = []
        if state:
            filters.append(f'state eq "{state.upper()}"')
        if asset_type:
            filters.append(f'assetType eq "{asset_type}"')
        if category:
            filters.append(f'category eq "{category.upper()}"')

        params: dict = {"pageSize": page_size}
        if filters:
            params["filter"] = " and ".join(filters)

        return self._get("/activities", params).get("content", [])

    def get_activity(self, activity_id: str) -> dict:
        """Return a single activity by ID with full sub-task detail."""
        return self._get(f"/activities/{activity_id}")

    def cancel_activity(self, activity_id: str) -> dict:
        """Request cancellation of a running activity."""
        return self._post(f"/activities/{activity_id}/cancel")

    def failed_activities(self, asset_type: str | None = None) -> list[dict]:
        """Shorthand — return all FAILED activities."""
        return self.list_activities(state="FAILED", asset_type=asset_type)

    def running_activities(self, asset_type: str | None = None) -> list[dict]:
        """Shorthand — return all RUNNING activities."""
        return self.list_activities(state="RUNNING", asset_type=asset_type)
