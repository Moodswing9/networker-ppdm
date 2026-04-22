"""ppdm/policies.py — Protection policy and protection rule endpoints."""

from __future__ import annotations


class PoliciesMixin:
    """Mixin providing /protection-policies and /protection-rules endpoints."""

    # ── Policies ──────────────────────────────────────────────────────────────

    def list_policies(self, asset_type: str | None = None) -> list[dict]:
        """Return all protection policies, optionally filtered by asset type."""
        params: dict = {}
        if asset_type:
            params["filter"] = f'assetType eq "{asset_type}"'
        return self._get("/protection-policies", params).get("content", [])

    def get_policy(self, policy_id: str) -> dict:
        """Return a single protection policy by ID."""
        return self._get(f"/protection-policies/{policy_id}")

    def get_policy_by_name(self, name: str) -> dict | None:
        """Return the first policy matching name, or None."""
        policies = self.list_policies()
        for p in policies:
            if p.get("name") == name:
                return p
        return None

    def create_policy(self, body: dict) -> dict:
        """Create a protection policy.

        Minimal body example for a Kubernetes daily policy::

            {
                "name": "k8s-daily",
                "assetType": "KUBERNETES",
                "type": "ACTIVE",
                "dataConsistency": "CRASH_CONSISTENT",
                "stages": [{
                    "type": "PROTECTION",
                    "retention": {"unit": "DAY", "interval": 30,
                                  "storageSystemRetentionLock": False},
                    "target": {"storageSystemId": "<dd-id>",
                               "dataTargetWithDdBoost": True},
                    "operations": [{
                        "type": "AUTO_FULL",
                        "schedule": {"frequency": "DAILY", "startTime": "02:00",
                                     "duration": 10, "durationUnit": "HOURS"}
                    }]
                }]
            }
        """
        return self._post("/protection-policies", body)

    def assign_assets(self, policy_id: str, asset_ids: list[str]) -> dict:
        """Assign one or more assets to a policy by ID."""
        return self._post(
            f"/protection-policies/{policy_id}/asset-assignments",
            {"assetIds": asset_ids},
        )

    def trigger_backup(
        self,
        policy_id: str,
        asset_ids: list[str] | None = None,
    ) -> dict:
        """Trigger an on-demand backup for a policy.

        Args:
            policy_id:  ID of the protection policy.
            asset_ids:  Subset of assets to back up. If None, backs up all
                        assigned assets.

        Returns:
            Dict containing ``activityId`` for monitoring progress.
        """
        body: dict = {"stages": [{"type": "PROTECTION"}]}
        if asset_ids:
            body["assetIds"] = asset_ids
        return self._post(f"/protection-policies/{policy_id}/protections", body)

    def delete_policy(self, policy_id: str) -> None:
        """Delete a protection policy (must have no active asset assignments)."""
        self._delete(f"/protection-policies/{policy_id}")

    # ── Protection Rules ──────────────────────────────────────────────────────

    def list_protection_rules(self) -> list[dict]:
        """Return all protection rules."""
        return self._get("/protection-rules").get("content", [])

    def create_protection_rule(self, body: dict) -> dict:
        """Create a protection rule for auto-assignment.

        Example body to auto-assign all K8S namespaces::

            {
                "name": "k8s-auto-assign",
                "assetType": "KUBERNETES",
                "policyId": "<policy-id>",
                "action": "MOVE_TO_POLICY",
                "priority": 1,
                "conditions": [{
                    "assetAttributeName": "type",
                    "operator": "EQUALS",
                    "assetAttributeValue": "K8S_NAMESPACE"
                }]
            }
        """
        return self._post("/protection-rules", body)

    def delete_protection_rule(self, rule_id: str) -> None:
        """Delete a protection rule by ID."""
        self._delete(f"/protection-rules/{rule_id}")

    # ── Inventory sources (vCenter, K8s clusters, app hosts) ─────────────────

    def list_inventory_sources(self, source_type: str | None = None) -> list[dict]:
        """Return all registered inventory sources."""
        params: dict = {}
        if source_type:
            params["filter"] = f'type eq "{source_type}"'
        return self._get("/inventory-sources", params).get("content", [])

    def discover_inventory_source(self, source_id: str) -> dict:
        """Trigger asset discovery on an inventory source (vCenter, K8s cluster)."""
        return self._post(f"/inventory-sources/{source_id}/discover")

    # ── Storage systems ───────────────────────────────────────────────────────

    def list_storage_systems(self) -> list[dict]:
        """Return all connected storage systems (Data Domain, cloud targets)."""
        return self._get("/storage-systems").get("content", [])

    def get_storage_system(self, system_id: str) -> dict:
        """Return capacity and detail for a single storage system."""
        return self._get(f"/storage-systems/{system_id}")
