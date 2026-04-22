"""Unit tests for DDClient — auth, DDBoost, storage units."""

import pytest
import responses

from datadomain.client import DDClient
from tests.unit.conftest import DD_HOST, DD_BASE, FAKE_DD_TOKEN

DD_AUTH_URL = f"https://{DD_HOST}:3009/rest/v1.0/auth"

SU_1 = {"name": "ppdm-su-01", "user": "ddboost-user", "status": "enabled"}
SU_2 = {"name": "nw-su-01",   "user": "ddboost-user", "status": "enabled"}


class TestDDLogin:
    @responses.activate
    def test_login_stores_token(self):
        responses.add(
            responses.POST, DD_AUTH_URL,
            json={"token": FAKE_DD_TOKEN},
            status=200,
        )
        client = DDClient(DD_HOST, "sysadmin", "pass")
        client.login()
        assert client._token == FAKE_DD_TOKEN
        assert client._session.headers["X-DD-AUTH-TOKEN"] == FAKE_DD_TOKEN

    @responses.activate
    def test_login_raises_on_bad_creds(self):
        responses.add(
            responses.POST, DD_AUTH_URL,
            json={"message": "Unauthorized"},
            status=401,
        )
        client = DDClient(DD_HOST, "sysadmin", "wrong")
        with pytest.raises(Exception):
            client.login()

    @responses.activate
    def test_context_manager_logs_out(self):
        responses.add(
            responses.POST, DD_AUTH_URL,
            json={"token": FAKE_DD_TOKEN},
            status=200,
        )
        responses.add(
            responses.DELETE, DD_AUTH_URL,
            status=200,
            body=b"",
        )
        with DDClient(DD_HOST, "sysadmin", "pass") as dd:
            assert dd._token == FAKE_DD_TOKEN
        assert dd._token is None


class TestDDBoost:
    @responses.activate
    def test_ddboost_status(self, dd_client):
        responses.add(
            responses.GET, f"{DD_BASE}/protocols/ddboost",
            json={"status": "enabled", "encryption": "medium"},
            status=200,
        )
        status = dd_client.ddboost_status()
        assert status["status"] == "enabled"

    @responses.activate
    def test_enable_ddboost(self, dd_client):
        responses.add(
            responses.PUT, f"{DD_BASE}/protocols/ddboost",
            json={"status": "enabled"},
            status=200,
        )
        result = dd_client.enable_ddboost()
        assert result["status"] == "enabled"
        import json
        body = json.loads(responses.calls[0].request.body)
        assert body["status"] == "enabled"


class TestStorageUnits:
    @responses.activate
    def test_list_storage_units(self, dd_client):
        responses.add(
            responses.GET, f"{DD_BASE}/protocols/ddboost/storage-units",
            json={"storage_units": [SU_1, SU_2]},
            status=200,
        )
        units = dd_client.list_storage_units()
        assert len(units) == 2

    @responses.activate
    def test_create_storage_unit(self, dd_client):
        responses.add(
            responses.POST, f"{DD_BASE}/protocols/ddboost/storage-units",
            json={"name": "new-su", "status": "enabled"},
            status=201,
        )
        result = dd_client.create_storage_unit(
            "new-su", "ddboost-user",
            soft_limit_tib=10.0, hard_limit_tib=12.0,
        )
        assert result["name"] == "new-su"
        import json
        body = json.loads(responses.calls[0].request.body)
        assert body["quota"]["soft-limit"]["value"] == 10.0
        assert body["quota"]["hard-limit"]["unit"] == "TiB"

    @responses.activate
    def test_assign_user_to_storage_unit(self, dd_client):
        responses.add(
            responses.PUT,
            f"{DD_BASE}/protocols/ddboost/storage-units/ppdm-su-01/users",
            json={"name": "ddboost-user", "access": "read-write"},
            status=200,
        )
        result = dd_client.assign_user_to_storage_unit("ppdm-su-01", "ddboost-user")
        assert result["access"] == "read-write"
