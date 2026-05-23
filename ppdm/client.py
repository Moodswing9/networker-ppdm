"""
ppdm/client.py — PowerProtect Data Manager REST API client.

Base URL: https://<host>:8443/api/v2

Usage:
    from ppdm import PPDMClient

    with PPDMClient("ppdm.example.com", "admin", "Password1!") as ppdm:
        assets = ppdm.list_assets(asset_type="KUBERNETES")
        failed = ppdm.list_activities(state="FAILED")
"""

from __future__ import annotations

import os
import random
import time
import urllib3

import requests

from .assets import AssetsMixin
from .activities import ActivitiesMixin
from .policies import PoliciesMixin
from .restores import RestoresMixin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_DEFAULT_PORT   = 8443
_API_VERSION    = "v2"
_RETRY_STATUSES  = frozenset({429, 500, 502, 503, 504})
_MAX_RETRIES     = 3
_BACKOFF_BASE    = 1.0   # seconds
_DEFAULT_TIMEOUT = 30    # seconds


class PPDMClient(AssetsMixin, ActivitiesMixin, PoliciesMixin, RestoresMixin):
    """Authenticated session to a PowerProtect Data Manager server.

    Supports use as a context manager (automatically logs out on exit).

    Args:
        host:       Hostname or IP of the PPDM server.
        username:   Admin username (default: "admin").
        password:   Admin password.
        port:       API port (default: 8443).
        verify_ssl: Verify TLS certificate (default: False — self-signed certs common in labs).
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = _DEFAULT_PORT,
        verify_ssl: bool = False,
    ) -> None:
        self.base_url   = f"https://{host}:{port}/api/{_API_VERSION}"
        self._username  = username
        self._password  = password
        self._verify    = verify_ssl
        self._token: str | None = None
        self._session   = requests.Session()
        self._session.verify = verify_ssl

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self) -> None:
        """Authenticate and store the Bearer token."""
        resp = self._session.post(
            f"{self.base_url}/login",
            json={"username": self._username, "password": self._password},
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        self._session.headers.update({"Authorization": f"Bearer {self._token}"})

    def logout(self) -> None:
        """Invalidate the current session token."""
        if self._token:
            try:
                self._session.post(f"{self.base_url}/logout")
            except Exception:
                pass
            finally:
                self._token = None
                self._session.headers.pop("Authorization", None)

    def __enter__(self) -> "PPDMClient":
        self.login()
        return self

    def __exit__(self, *_) -> None:
        self.logout()

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """Send an HTTP request, retrying transient failures with exponential backoff.

        Automatically re-authenticates on a 401 response (once per call).
        """
        kwargs.setdefault("timeout", _DEFAULT_TIMEOUT)
        last_resp: requests.Response | None = None
        last_exc: Exception | None = None
        _auth_retried = False
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = getattr(self._session, method)(url, **kwargs)
                if resp.status_code == 401 and not _auth_retried:
                    _auth_retried = True
                    self.login()
                    continue
                if resp.status_code not in _RETRY_STATUSES:
                    return resp
                last_resp = resp
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
            if attempt < _MAX_RETRIES:
                delay = _BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(delay)
        if last_resp is not None:
            last_resp.raise_for_status()
        raise last_exc  # type: ignore[misc]

    def _get(self, path: str, params: dict | None = None) -> dict:
        """GET with automatic pagination — returns merged content list or raw dict."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        params = dict(params or {})

        # If the caller hasn't set a pageSize, default to 100
        if "pageSize" not in params:
            params["pageSize"] = 100

        all_content: list = []
        page = 0

        while True:
            params["page"] = page
            resp = self._request_with_retry("get", url, params=params)
            resp.raise_for_status()
            data = resp.json()

            # Endpoints that return a list under "content" key
            if isinstance(data, dict) and "content" in data:
                all_content.extend(data["content"])
                total_pages = data.get("page", {}).get("totalPages", 1)
                if page + 1 >= total_pages:
                    data["content"] = all_content
                    return data
                page += 1
            else:
                # Single-object response (e.g. GET /assets/<id>)
                return data

    def _post(self, path: str, body: dict | None = None) -> dict:
        resp = self._request_with_retry(
            "post",
            f"{self.base_url}/{path.lstrip('/')}",
            json=body or {},
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _patch(self, path: str, body: dict) -> dict:
        resp = self._request_with_retry(
            "patch",
            f"{self.base_url}/{path.lstrip('/')}",
            json=body,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _delete(self, path: str) -> None:
        resp = self._request_with_retry(
            "delete",
            f"{self.base_url}/{path.lstrip('/')}",
        )
        resp.raise_for_status()

    # ── Factory from environment variables ───────────────────────────────────

    @classmethod
    def from_env(cls) -> "PPDMClient":
        """Build a PPDMClient from environment variables.

        Required env vars: PPDM_HOST, PPDM_USER, PPDM_PASS
        Optional: PPDM_PORT (default 8443), PPDM_VERIFY_SSL (default false)
        """
        host   = os.environ["PPDM_HOST"]
        user   = os.environ["PPDM_USER"]
        passwd = os.environ["PPDM_PASS"]
        port   = int(os.environ.get("PPDM_PORT", _DEFAULT_PORT))
        verify = os.environ.get("PPDM_VERIFY_SSL", "false").lower() == "true"
        return cls(host, user, passwd, port=port, verify_ssl=verify)
