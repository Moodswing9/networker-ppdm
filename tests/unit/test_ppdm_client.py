"""Unit tests for PPDMClient auth and base HTTP methods."""

import pytest
import responses

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
