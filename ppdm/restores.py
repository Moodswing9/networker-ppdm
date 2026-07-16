"""ppdm/restores.py — Restore operation endpoints."""

from __future__ import annotations


class RestoresMixin:
    """Mixin providing /restores endpoints for PPDMClient."""

    def restore(
        self,
        copy_id: str,
        restore_type: str = "TO_ORIGINAL",
        options: dict | None = None,
    ) -> dict:
        """Initiate a restore from a backup copy.

        Args:
            copy_id:       ID of the backup copy to restore from.
                           Obtain via ``list_copies(asset_id)``.
            restore_type:  "TO_ORIGINAL" (default) or "TO_NEW".
            options:       Product-specific restore options dict.
                           For Kubernetes::

                               {
                                   "k8s": {
                                       "targetNamespace": "my-ns-restored",
                                       "targetClusterId": "<inv-source-id>",
                                       "restorePVCs": True,
                                       "restoreNamespaceMetadata": True
                                   }
                               }

                           For VMware::

                               {
                                   "vmware": {
                                       "targetVcenterId": "<vcenter-id>",
                                       "targetDatastoreId": "<ds-id>",
                                       "poweredOn": True
                                   }
                               }

        Returns:
            Dict with ``id`` (restore job ID) and ``state``.
        """
        body: dict = {"copyId": copy_id, "restoreType": restore_type}
        if options:
            body["options"] = options
        return self._post("/restores", body)

    def get_restore(self, restore_id: str) -> dict:
        """Return current state and progress of a restore job."""
        return self._get(f"/restores/{restore_id}")

    def list_restores(self, state: str | None = None, page_size: int = 20) -> list[dict]:
        """List restore sessions, optionally filtered by state.

        Args:
            state:      Optional state filter — "RUNNING", "COMPLETED", "FAILED", "CANCELED".
            page_size:  Max results to return (default 20).
        """
        params: dict = {"pageSize": page_size, "orderby": "startTime DESC"}
        if state:
            params["filter"] = f'state eq "{state}"'
        response = self._get("/restores", params=params)
        if isinstance(response, dict):
            return response.get("content", [])
        return response if isinstance(response, list) else []

    def cancel_restore(self, restore_id: str) -> None:
        """Cancel a running restore session."""
        self._delete(f"/restores/{restore_id}")

    def restore_to_new(
        self,
        copy_id: str,
        options: dict,
    ) -> dict:
        """Shorthand for a TO_NEW restore (new namespace, VM, etc.)."""
        return self.restore(copy_id, restore_type="TO_NEW", options=options)

    def restore_kubernetes_to_new_namespace(
        self,
        copy_id: str,
        target_namespace: str,
        target_cluster_id: str,
        restore_pvcs: bool = True,
    ) -> dict:
        """Restore a Kubernetes namespace backup to a new namespace.

        Args:
            copy_id:             Backup copy ID.
            target_namespace:    Name of the destination namespace.
            target_cluster_id:   Inventory source ID of the target K8s cluster.
            restore_pvcs:        Also restore PersistentVolumeClaims (default: True).
        """
        return self.restore(
            copy_id,
            restore_type="TO_NEW",
            options={
                "k8s": {
                    "targetNamespace": target_namespace,
                    "targetClusterId": target_cluster_id,
                    "restorePVCs": restore_pvcs,
                    "restoreNamespaceMetadata": True,
                }
            },
        )
