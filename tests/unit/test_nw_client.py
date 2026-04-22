"""Unit tests for NWClient — savesets, clients, policies."""

import responses

from tests.unit.conftest import NW_BASE

CLIENT_1  = {"id": "cl-001", "hostname": "web01.example.com", "name": "web01"}
SAVESET_1 = {"ssid": "1234567890",  "name": "/",      "level": "Full",
             "saveTime": "2026-04-21T22:00:00Z", "sumSize": 104857600}
SAVESET_2 = {"ssid": "1234567891",  "name": "/home",  "level": "Incremental",
             "saveTime": "2026-04-22T22:00:00Z", "sumSize": 10485760}
POLICY_1  = {"name": "GoldPolicy", "comment": "Daily full + weekly clone"}
GROUP_1   = {"name": "Linux-Clients", "comment": "All Linux servers"}


class TestNWClients:
    @responses.activate
    def test_list_clients(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/clients",
            json={"clients": [CLIENT_1]},
            status=200,
        )
        clients = nw_client.list_clients()
        assert len(clients) == 1
        assert clients[0]["hostname"] == "web01.example.com"

    @responses.activate
    def test_get_client_by_hostname(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/clients",
            json={"clients": [CLIENT_1]},
            status=200,
        )
        client = nw_client.get_client("web01.example.com")
        assert client["id"] == "cl-001"

    @responses.activate
    def test_get_client_not_found_returns_none(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/clients",
            json={"clients": []},
            status=200,
        )
        assert nw_client.get_client("nonexistent") is None


class TestNWSavesets:
    @responses.activate
    def test_list_savesets_for_client(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/savesets",
            json={"savesets": [SAVESET_1, SAVESET_2]},
            status=200,
        )
        savesets = nw_client.list_savesets_for_client("web01.example.com")
        assert len(savesets) == 2

    @responses.activate
    def test_list_savesets_sends_client_filter(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/savesets",
            json={"savesets": [SAVESET_1]},
            status=200,
        )
        nw_client.list_savesets(client_name="web01.example.com")
        assert "web01" in responses.calls[0].request.url

    @responses.activate
    def test_list_savesets_level_filter(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/savesets",
            json={"savesets": [SAVESET_1]},
            status=200,
        )
        savesets = nw_client.list_savesets(client_name="web01", level="Full")
        assert savesets[0]["level"] == "Full"

    @responses.activate
    def test_latest_full_backup(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/savesets",
            json={"savesets": [SAVESET_1]},
            status=200,
        )
        latest = nw_client.latest_full_backup("web01.example.com")
        assert latest["ssid"] == "1234567890"

    @responses.activate
    def test_latest_full_backup_none_when_empty(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/savesets",
            json={"savesets": []},
            status=200,
        )
        assert nw_client.latest_full_backup("web01.example.com") is None


class TestNWPolicies:
    @responses.activate
    def test_list_policies(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/policies",
            json={"policies": [POLICY_1]},
            status=200,
        )
        policies = nw_client.list_policies()
        assert policies[0]["name"] == "GoldPolicy"

    @responses.activate
    def test_list_protection_groups(self, nw_client):
        responses.add(
            responses.GET, f"{NW_BASE}/protectiongroups",
            json={"protectionGroups": [GROUP_1]},
            status=200,
        )
        groups = nw_client.list_protection_groups()
        assert groups[0]["name"] == "Linux-Clients"
