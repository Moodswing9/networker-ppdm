"""Unit tests for PPDMClient auth and base HTTP methods."""

import pytest
import responses
import requests

from ppdm.client import PPDMClient
from tests.unit.conftest import PPDM_HOST, PPDM_BASE, FAKE_TOKEN


class TestPPDMLogin:
    @responses.activate
    def test_login_stores_token(self):
        responses.add(
            responses.POST,
            f"{PPDM_BASE}/login",
            json={"access_token": FAKE_TOKEN},
            status=200,
        )
        client = PPDMClient(PPDM_HOST, "admin", "pass")
        client.login()
        assert client._token == FAKE_TOKEN
        assert client._session.headers["Authorization"] == f"Bearer {FAKE_TOKEN}"

    @responses.activate
    def test_login_raises_on_401(self):
        responses.add(
            responses.POST,
            f"{PPDM_BASE}/login",
            json={"message": "Unauthorized"},
            status=401,
        )
        client = PPDMClient(PPDM_HOST, "admin", "wrongpass")
        with pytest.raises(Exception):
            client.login()

    @responses.activate
    def test_context_manager_logs_out(self):
        responses.add(
            responses.POST,
            f"{PPDM_BASE}/login",
            json={"access_token": FAKE_TOKEN},
            status=200,
        )
        responses.add(
            responses.POST,
            f"{PPDM_BASE}/logout",
            status=204,
            body=b"",
        )
        with PPDMClient(PPDM_HOST, "admin", "pass") as ppdm:
            assert ppdm._token == FAKE_TOKEN
        assert ppdm._token is None


class TestPPDMPagination:
    @responses.activate
    def test_get_merges_pages(self, ppdm_client):
        # Page 0
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/assets",
            json={
                "content": [{"id": "a1"}],
                "page": {"totalPages": 2},
            },
            status=200,
        )
        # Page 1
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/assets",
            json={
                "content": [{"id": "a2"}],
                "page": {"totalPages": 2},
            },
            status=200,
        )
        result = ppdm_client._get("/assets")
        assert len(result["content"]) == 2
        assert result["content"][0]["id"] == "a1"
        assert result["content"][1]["id"] == "a2"

    @responses.activate
    def test_get_single_object(self, ppdm_client):
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/assets/abc-123",
            json={"id": "abc-123", "name": "my-asset"},
            status=200,
        )
        result = ppdm_client._get("/assets/abc-123")
        assert result["id"] == "abc-123"


class TestPPDMAuth401Retry:
    @responses.activate
    def test_401_triggers_reauth_and_retries(self, ppdm_client):
        """A 401 mid-session causes one re-login then a successful retry."""
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/activities",
            json={"error": "Unauthorized"},
            status=401,
        )
        responses.add(
            responses.POST,
            f"{PPDM_BASE}/login",
            json={"access_token": "new-token"},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/activities",
            json={"content": [{"id": "job-1"}]},
            status=200,
        )
        result = ppdm_client._get("/activities")
        assert len(result["content"]) == 1
        assert result["content"][0]["id"] == "job-1"

    @responses.activate
    def test_second_401_raises(self, ppdm_client):
        """Re-auth is attempted only once; a second 401 propagates as an error."""
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/activities",
            status=401,
        )
        responses.add(
            responses.POST,
            f"{PPDM_BASE}/login",
            json={"access_token": "new-token"},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/activities",
            status=401,
        )
        with pytest.raises(Exception):
            ppdm_client._get("/activities")

    @responses.activate
    def test_reauth_updates_token_header(self, ppdm_client):
        """After re-auth the session carries the new token."""
        responses.add(responses.GET, f"{PPDM_BASE}/activities", status=401)
        responses.add(
            responses.POST,
            f"{PPDM_BASE}/login",
            json={"access_token": "refreshed-token"},
            status=200,
        )
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/activities",
            json={"content": []},
            status=200,
        )
        ppdm_client._get("/activities")
        assert ppdm_client._session.headers.get("Authorization") == "Bearer refreshed-token"


class TestPPDMPaginationEdgeCases:
    @responses.activate
    def test_missing_page_key_defaults_to_single_page(self, ppdm_client):
        """Response without a 'page' key is treated as a one-page result."""
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/assets",
            json={"content": [{"id": "x1"}]},
            status=200,
        )
        result = ppdm_client._get("/assets")
        assert len(result["content"]) == 1

    @responses.activate
    def test_empty_page_object_defaults_to_single_page(self, ppdm_client):
        """page dict present but totalPages absent — treat as 1 page."""
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/assets",
            json={"content": [{"id": "y1"}], "page": {}},
            status=200,
        )
        result = ppdm_client._get("/assets")
        assert len(result["content"]) == 1

    @responses.activate
    def test_total_pages_zero_returns_without_looping(self, ppdm_client):
        """totalPages=0 should not cause an infinite loop."""
        responses.add(
            responses.GET,
            f"{PPDM_BASE}/assets",
            json={"content": [], "page": {"totalPages": 0}},
            status=200,
        )
        result = ppdm_client._get("/assets")
        assert result["content"] == []
