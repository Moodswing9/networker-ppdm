"""
networker/client.py — NetWorker REST API client.

Base URL: https://<host>:9090/nwrestapi/v3

Usage:
    from networker import NWClient

    with NWClient("nwserver.example.com", "administrator", "Password1!") as nw:
        clients = nw.list_clients()
        savesets = nw.list_savesets(client_name="myhost.example.com")
"""

from __future__ import annotations

import os
import urllib3

import requests

from .savesets import SavesetsMixin
from .policies import PoliciesMixin as NWPoliciesMixin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_DEFAULT_PORT   = 9090
_API_BASE_PATH  = "nwrestapi/v3"


class NWClient(SavesetsMixin, NWPoliciesMixin):
    """Authenticated session to a NetWorker REST API server.

    Args:
        host:       NetWorker server hostname or IP.
        username:   Admin username.
        password:   Admin password.
        port:       REST API port (default: 9090).
        verify_ssl: Verify TLS certificate (default: False).
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = _DEFAULT_PORT,
        verify_ssl: bool = False,
    ) -> None:
        self.base_url  = f"https://{host}:{port}/{_API_BASE_PATH}"
        self._auth     = (username, password)
        self._verify   = verify_ssl
        self._session  = requests.Session()
        self._session.auth   = self._auth
        self._session.verify = verify_ssl

    def __enter__(self) -> "NWClient":
        return self

    def __exit__(self, *_) -> None:
        self._session.close()

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = self._session.get(
            f"{self.base_url}/global/{path.lstrip('/')}",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, body: dict | None = None) -> dict:
        resp = self._session.post(
            f"{self.base_url}/global/{path.lstrip('/')}",
            json=body or {},
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _put(self, path: str, body: dict) -> dict:
        resp = self._session.put(
            f"{self.base_url}/global/{path.lstrip('/')}",
            json=body,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _delete(self, path: str) -> None:
        resp = self._session.delete(
            f"{self.base_url}/global/{path.lstrip('/')}"
        )
        resp.raise_for_status()

    # ── Clients ───────────────────────────────────────────────────────────────

    def list_clients(self) -> list[dict]:
        """Return all NetWorker client resources."""
        return self._get("/clients").get("clients", [])

    def get_client(self, client_name: str) -> dict | None:
        """Return a single client resource by hostname, or None if not found."""
        for client in self.list_clients():
            if client.get("hostname") == client_name or client.get("name") == client_name:
                return client
        return None

    def get_client_by_id(self, client_id: str) -> dict:
        """Return a single client resource by ID."""
        return self._get(f"/clients/{client_id}")

    # ── Backups ───────────────────────────────────────────────────────────────

    def trigger_group_backup(self, group_name: str) -> dict:
        """Trigger an immediate backup for a protection group.

        Equivalent to: ``savegrp -G <group_name>``
        """
        return self._post(f"/protectiongroups/{group_name}/op/backup")

    # ── Recovers ─────────────────────────────────────────────────────────────

    def start_recover(
        self,
        source_client: str,
        destination_client: str,
        saveset_ids: list[str],
        destination_path: str | None = None,
    ) -> dict:
        """Initiate a file-system recover.

        Args:
            source_client:      Client the data was backed up from.
            destination_client: Client to restore to (can be same as source).
            saveset_ids:        List of saveset SSIDs to recover.
            destination_path:   Restore to this path (None = original location).
        """
        body: dict = {
            "sourceClient":      source_client,
            "destinationClient": destination_client,
            "saveSets":          saveset_ids,
        }
        if destination_path:
            body["destinationPath"] = destination_path
        return self._post("/recovers", body)

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "NWClient":
        """Build an NWClient from environment variables.

        Required: NW_HOST, NW_USER, NW_PASS
        Optional: NW_PORT (default 9090), NW_VERIFY_SSL (default false)
        """
        host   = os.environ["NW_HOST"]
        user   = os.environ["NW_USER"]
        passwd = os.environ["NW_PASS"]
        port   = int(os.environ.get("NW_PORT", _DEFAULT_PORT))
        verify = os.environ.get("NW_VERIFY_SSL", "false").lower() == "true"
        return cls(host, user, passwd, port=port, verify_ssl=verify)
