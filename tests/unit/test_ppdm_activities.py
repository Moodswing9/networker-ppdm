"""Unit tests for PPDM activity (job) endpoints."""

import responses

from tests.unit.conftest import PPDM_BASE

FAILED_JOB  = {"id": "act-001", "state": "FAILED",  "assetType": "KUBERNETES",
               "name": "k8s-backup", "startTime": "2026-04-22T02:00:00Z",
               "result": {"error": {"code": "ERR_001", "message": "No snapshot class"}}}
RUNNING_JOB = {"id": "act-002", "state": "RUNNING", "assetType": "VMWARE_VIRTUAL_MACHINE",
               "name": "vm-backup", "startTime": "2026-04-22T03:00:00Z"}


class TestListActivities:
    @responses.activate
    def test_list_failed_activities(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/activities",
            json={"content": [FAILED_JOB], "page": {"totalPages": 1}},
            status=200,
        )
        failed = ppdm_client.failed_activities()
        assert len(failed) == 1
        assert failed[0]["state"] == "FAILED"

    @responses.activate
    def test_failed_activities_filter_sent(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/activities",
            json={"content": [], "page": {"totalPages": 1}},
            status=200,
        )
        ppdm_client.failed_activities()
        req = responses.calls[0].request
        assert "FAILED" in req.url

    @responses.activate
    def test_list_activities_by_asset_type(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/activities",
            json={"content": [FAILED_JOB], "page": {"totalPages": 1}},
            status=200,
        )
        jobs = ppdm_client.list_activities(state="FAILED", asset_type="KUBERNETES")
        assert jobs[0]["assetType"] == "KUBERNETES"
        req = responses.calls[0].request
        assert "KUBERNETES" in req.url

    @responses.activate
    def test_get_activity(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/activities/act-001",
            json=FAILED_JOB, status=200,
        )
        job = ppdm_client.get_activity("act-001")
        assert job["id"] == "act-001"

    @responses.activate
    def test_cancel_activity(self, ppdm_client):
        responses.add(
            responses.POST, f"{PPDM_BASE}/activities/act-002/cancel",
            json={}, status=200,
        )
        result = ppdm_client.cancel_activity("act-002")
        assert isinstance(result, dict)
