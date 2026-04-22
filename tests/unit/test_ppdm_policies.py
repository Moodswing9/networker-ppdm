"""Unit tests for PPDM policy and restore endpoints."""

import responses

from tests.unit.conftest import PPDM_BASE

POLICY = {
    "id": "pol-001",
    "name": "k8s-daily",
    "assetType": "KUBERNETES",
    "type": "ACTIVE",
}


class TestPolicies:
    @responses.activate
    def test_list_policies(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/protection-policies",
            json={"content": [POLICY], "page": {"totalPages": 1}},
            status=200,
        )
        policies = ppdm_client.list_policies()
        assert len(policies) == 1
        assert policies[0]["name"] == "k8s-daily"

    @responses.activate
    def test_get_policy_by_name_found(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/protection-policies",
            json={"content": [POLICY], "page": {"totalPages": 1}},
            status=200,
        )
        p = ppdm_client.get_policy_by_name("k8s-daily")
        assert p["id"] == "pol-001"

    @responses.activate
    def test_get_policy_by_name_not_found(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/protection-policies",
            json={"content": [], "page": {"totalPages": 1}},
            status=200,
        )
        p = ppdm_client.get_policy_by_name("nonexistent")
        assert p is None

    @responses.activate
    def test_trigger_backup_returns_activity_id(self, ppdm_client):
        responses.add(
            responses.POST, f"{PPDM_BASE}/protection-policies/pol-001/protections",
            json={"activityId": "act-999"},
            status=200,
        )
        result = ppdm_client.trigger_backup("pol-001", asset_ids=["ns-001"])
        assert result["activityId"] == "act-999"

    @responses.activate
    def test_assign_assets(self, ppdm_client):
        responses.add(
            responses.POST,
            f"{PPDM_BASE}/protection-policies/pol-001/asset-assignments",
            json={},
            status=200,
        )
        ppdm_client.assign_assets("pol-001", ["ns-001", "ns-002"])
        req = responses.calls[0].request
        import json
        body = json.loads(req.body)
        assert "ns-001" in body["assetIds"]

    @responses.activate
    def test_create_protection_rule(self, ppdm_client):
        rule = {
            "name": "k8s-auto",
            "assetType": "KUBERNETES",
            "policyId": "pol-001",
            "action": "MOVE_TO_POLICY",
            "priority": 1,
            "conditions": [{"assetAttributeName": "type",
                            "operator": "EQUALS",
                            "assetAttributeValue": "K8S_NAMESPACE"}],
        }
        responses.add(
            responses.POST, f"{PPDM_BASE}/protection-rules",
            json={"id": "rule-001", **rule},
            status=201,
        )
        result = ppdm_client.create_protection_rule(rule)
        assert result["id"] == "rule-001"


class TestRestores:
    @responses.activate
    def test_restore_to_original(self, ppdm_client):
        responses.add(
            responses.POST, f"{PPDM_BASE}/restores",
            json={"id": "restore-001", "state": "RUNNING"},
            status=200,
        )
        result = ppdm_client.restore("copy-bbb")
        assert result["id"] == "restore-001"
        import json
        body = json.loads(responses.calls[0].request.body)
        assert body["restoreType"] == "TO_ORIGINAL"
        assert body["copyId"] == "copy-bbb"

    @responses.activate
    def test_restore_k8s_to_new_namespace(self, ppdm_client):
        responses.add(
            responses.POST, f"{PPDM_BASE}/restores",
            json={"id": "restore-002", "state": "RUNNING"},
            status=200,
        )
        result = ppdm_client.restore_kubernetes_to_new_namespace(
            "copy-bbb", "ns-restored", "inv-001"
        )
        assert result["id"] == "restore-002"
        import json
        body = json.loads(responses.calls[0].request.body)
        assert body["restoreType"] == "TO_NEW"
        assert body["options"]["k8s"]["targetNamespace"] == "ns-restored"
