from __future__ import annotations

from orchestrator.doctor import run_doctor
from orchestrator.inventory import run_inventory
from orchestrator.protect import run_protect
from providers.ppdm import PPDMProvider
from providers.networker import NetworkerProvider
from providers.datadomain import DataDomainProvider


class _PPDMStub:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def list_policies(self):
        return [{"id": "p1"}]

    def running_activities(self):
        return [{"id": "r1"}]

    def failed_activities(self):
        return [{"id": "f1"}, {"id": "f2"}]

    def get_policy_by_name(self, name):
        return {"id": "policy-1", "name": name}

    def trigger_backup(self, policy_id):
        return {"activityId": "act-1", "policyId": policy_id}

    def list_assets(self):
        return [{"id": "a1", "name": "asset-1", "type": "KUBERNETES"}]


class _NWStub:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def list_policies(self):
        return [{"name": "gold"}]

    def list_protection_groups(self):
        return [{"name": "Linux-Clients"}]

    def trigger_group_backup(self, group_name):
        return {"status": "queued", "group": group_name}

    def list_clients(self):
        return [{"hostname": "web01.example.com", "id": "c1"}]

    def list_savesets_for_client(self, client_name):
        return [{"ssid": "1"}, {"ssid": "2"}]

    def latest_full_backup(self, client_name):
        return {"saveTime": "2026-04-22T10:00:00Z"}


class _DDStub:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def ddboost_status(self):
        return {"status": "enabled"}

    def filesystem_stats(self):
        return {"preCompUsed": 10}

    def system_info(self):
        return {"model": "DD6900"}


def test_run_doctor(monkeypatch):
    monkeypatch.setattr("providers.ppdm.PPDMClient.from_env", lambda: _PPDMStub())
    monkeypatch.setattr("providers.networker.NWClient.from_env", lambda: _NWStub())
    monkeypatch.setattr("providers.datadomain.DDClient.from_env", lambda: _DDStub())

    results = run_doctor()

    assert len(results) == 3
    assert all(result["ok"] for result in results)
    assert results[0]["provider"] == "ppdm"
    assert results[1]["provider"] == "networker"
    assert results[2]["provider"] == "datadomain"


def test_run_inventory(monkeypatch):
    monkeypatch.setattr("providers.ppdm.PPDMClient.from_env", lambda: _PPDMStub())
    monkeypatch.setattr("providers.networker.NWClient.from_env", lambda: _NWStub())

    rows = run_inventory()

    assert len(rows) == 2
    assert rows[0]["platform"] == "PPDM"
    assert rows[1]["platform"] == "NetWorker"


def test_run_inventory_for_specific_networker_client(monkeypatch):
    monkeypatch.setattr("providers.ppdm.PPDMClient.from_env", lambda: _PPDMStub())
    monkeypatch.setattr("providers.networker.NWClient.from_env", lambda: _NWStub())

    rows = run_inventory(networker_client="web01.example.com")

    assert len(rows) == 2
    assert rows[1]["latest_full_backup"] == "2026-04-22T10:00:00Z"
    assert rows[1]["saveset_count"] == 2


def test_run_protect_ppdm(monkeypatch):
    monkeypatch.setattr("providers.ppdm.PPDMClient.from_env", lambda: _PPDMStub())

    result = run_protect("ppdm", "k8s-daily")

    assert result["provider"] == "ppdm"
    assert result["result"]["activityId"] == "act-1"


def test_run_protect_networker(monkeypatch):
    monkeypatch.setattr("providers.networker.NWClient.from_env", lambda: _NWStub())

    result = run_protect("networker", "Linux-Clients")

    assert result["provider"] == "networker"
    assert result["result"]["group"] == "Linux-Clients"


def test_datadomain_provider_status(monkeypatch):
    monkeypatch.setattr("providers.datadomain.DDClient.from_env", lambda: _DDStub())

    result = DataDomainProvider().status()

    assert result["provider"] == "datadomain"
    assert result["system"]["model"] == "DD6900"


def test_ppdm_provider_healthcheck_error(monkeypatch):
    def _boom():
        raise RuntimeError("ppdm unavailable")

    monkeypatch.setattr("providers.ppdm.PPDMClient.from_env", _boom)

    result = PPDMProvider().healthcheck()

    assert result["ok"] is False
    assert "ppdm unavailable" in result["error"]


def test_networker_provider_healthcheck_error(monkeypatch):
    def _boom():
        raise RuntimeError("networker unavailable")

    monkeypatch.setattr("providers.networker.NWClient.from_env", _boom)

    result = NetworkerProvider().healthcheck()

    assert result["ok"] is False
    assert "networker unavailable" in result["error"]
