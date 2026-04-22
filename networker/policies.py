"""networker/policies.py — Policy, workflow, and action endpoints."""

from __future__ import annotations


class PoliciesMixin:
    """Mixin providing /policies endpoints for NWClient."""

    def list_policies(self) -> list[dict]:
        """Return all NetWorker protection policies."""
        return self._get("/policies").get("policies", [])

    def get_policy(self, policy_name: str) -> dict:
        """Return a single policy by name."""
        return self._get(f"/policies/{policy_name}")

    def list_workflows(self, policy_name: str) -> list[dict]:
        """Return all workflows for a protection policy."""
        return self._get(f"/policies/{policy_name}/workflows").get("workflows", [])

    def list_actions(self, policy_name: str, workflow_name: str) -> list[dict]:
        """Return all actions for a policy workflow."""
        return self._get(
            f"/policies/{policy_name}/workflows/{workflow_name}/actions"
        ).get("actions", [])

    def list_protection_groups(self) -> list[dict]:
        """Return all protection groups (legacy 'groups')."""
        return self._get("/protectiongroups").get("protectionGroups", [])

    def get_protection_group(self, group_name: str) -> dict:
        """Return a single protection group by name."""
        return self._get(f"/protectiongroups/{group_name}")
