"""
datadomain/client.py — Data Domain REST API client.

Base URL: https://<host>:3009/rest/v1.0

Usage:
    from datadomain import DDClient

    with DDClient("datadomain.example.com", "sysadmin", "Password1!") as dd:
        units = dd.list_storage_units()
        dd.enable_ddboost()
"""

from __future__ import annotations

import os
import urllib3

import requests

from .ddboost import DDBoostMixin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_DEFAULT_PORT  = 3009
_API_BASE_PATH = "rest/v1.0"
_DD_SYSTEM     = "dd-systems/0"  # primary system endpoint prefix


class DDClient(DDBoostMixin):
    """Authenticated session to a Data Domain REST API.

    Args:
        host:       Data Domain hostname or IP.
        username:   Admin username (default: "sysadmin").
        password:   Admin password.
        port:       REST API port (default: 3009).
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
        self._username = username
        self._password = password
        self._verify   = verify_ssl
        self._token: str | None = None
        self._session  = requests.Session()
        self._session.verify = verify_ssl

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self) -> None:
        """Authenticate and store the DD session token."""
        resp = self._session.post(
            f"{self.base_url}/auth",
            json={"username": self._username, "password": self._password},
        )
        resp.raise_for_status()
        self._token = resp.json()["token"]
        self._session.headers.update({"X-DD-AUTH-TOKEN": self._token})

    def logout(self) -> None:
        """Invalidate the session token."""
        if self._token:
            try:
                self._session.delete(f"{self.base_url}/auth")
            except Exception:
                pass
            finally:
                self._token = None
                self._session.headers.pop("X-DD-AUTH-TOKEN", None)

    def __enter__(self) -> "DDClient":
        self.login()
        return self

    def __exit__(self, *_) -> None:
        self.logout()

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = self._session.get(
            f"{self.base_url}/{_DD_SYSTEM}/{path.lstrip('/')}",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, body: dict | None = None) -> dict:
        resp = self._session.post(
            f"{self.base_url}/{_DD_SYSTEM}/{path.lstrip('/')}",
            json=body or {},
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _put(self, path: str, body: dict) -> dict:
        resp = self._session.put(
            f"{self.base_url}/{_DD_SYSTEM}/{path.lstrip('/')}",
            json=body,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _delete(self, path: str) -> None:
        resp = self._session.delete(
            f"{self.base_url}/{_DD_SYSTEM}/{path.lstrip('/')}"
        )
        resp.raise_for_status()

    # ── System ────────────────────────────────────────────────────────────────

    def system_info(self) -> dict:
        """Return Data Domain system info (model, serial, version)."""
        return self._get("/system")

    def filesystem_stats(self) -> dict:
        """Return filesystem usage, dedup ratio, and compression stats."""
        return self._get("/filesystem/stats")

    # ── Users ─────────────────────────────────────────────────────────────────

    def list_users(self) -> list[dict]:
        """Return all local DD users."""
        return self._get("/users").get("user", [])

    def create_user(self, name: str, password: str, role: str = "none") -> dict:
        """Create a local DD user.

        Args:
            name:     Username.
            password: Initial password.
            role:     DD role — "none", "user", "limited-admin", "admin", "security-officer".
        """
        return self._post("/users", {"name": name, "password": password, "role": role})

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "DDClient":
        """Build a DDClient from environment variables.

        Required: DD_HOST, DD_USER, DD_PASS
        Optional: DD_PORT (default 3009), DD_VERIFY_SSL (default false)
        """
        host   = os.environ["DD_HOST"]
        user   = os.environ["DD_USER"]
        passwd = os.environ["DD_PASS"]
        port   = int(os.environ.get("DD_PORT", _DEFAULT_PORT))
        verify = os.environ.get("DD_VERIFY_SSL", "false").lower() == "true"
        return cls(host, user, passwd, port=port, verify_ssl=verify)
