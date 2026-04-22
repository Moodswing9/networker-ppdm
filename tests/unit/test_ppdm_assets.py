"""Unit tests for PPDM asset and copy endpoints."""

import responses

from tests.unit.conftest import PPDM_BASE

ASSET_1 = {"id": "ns-001", "name": "prod-namespace", "type": "K8S_NAMESPACE",
            "complianceStatus": "IN_COMPLIANCE", "protectionPolicyName": "k8s-daily"}
ASSET_2 = {"id": "vm-001", "name": "web-server-01", "type": "VMWARE_VIRTUAL_MACHINE",
            "complianceStatus": "NOT_IN_COMPLIANCE", "protectionPolicyName": "vm-policy"}
COPY_1  = {"id": "copy-aaa", "createTime": "2026-04-21T02:00:00Z"}
COPY_2  = {"id": "copy-bbb", "createTime": "2026-04-22T02:00:00Z"}


class TestListAssets:
    @responses.activate
    def test_list_all_assets(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/assets",
            json={"content": [ASSET_1, ASSET_2], "page": {"totalPages": 1}},
            status=200,
        )
        assets = ppdm_client.list_assets()
        assert len(assets) == 2

    @responses.activate
    def test_list_assets_by_type_sends_filter(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/assets",
            json={"content": [ASSET_1], "page": {"totalPages": 1}},
            status=200,
        )
        assets = ppdm_client.list_assets(asset_type="K8S_NAMESPACE")
        assert len(assets) == 1
        # Verify the filter was sent in the request
        req = responses.calls[0].request
        assert 'K8S_NAMESPACE' in req.url

    @responses.activate
    def test_list_assets_by_name(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/assets",
            json={"content": [ASSET_1], "page": {"totalPages": 1}},
            status=200,
        )
        assets = ppdm_client.list_assets(name="prod-namespace")
        assert assets[0]["name"] == "prod-namespace"

    @responses.activate
    def test_get_asset(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/assets/ns-001",
            json=ASSET_1, status=200,
        )
        asset = ppdm_client.get_asset("ns-001")
        assert asset["id"] == "ns-001"


class TestCopies:
    @responses.activate
    def test_list_copies(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/assets/ns-001/copies",
            json={"content": [COPY_1, COPY_2], "page": {"totalPages": 1}},
            status=200,
        )
        copies = ppdm_client.list_copies("ns-001")
        assert len(copies) == 2

    @responses.activate
    def test_latest_copy_returns_newest(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/assets/ns-001/copies",
            json={"content": [COPY_1, COPY_2], "page": {"totalPages": 1}},
            status=200,
        )
        latest = ppdm_client.latest_copy("ns-001")
        assert latest["id"] == "copy-bbb"

    @responses.activate
    def test_latest_copy_returns_none_when_empty(self, ppdm_client):
        responses.add(
            responses.GET, f"{PPDM_BASE}/assets/ns-001/copies",
            json={"content": [], "page": {"totalPages": 1}},
            status=200,
        )
        assert ppdm_client.latest_copy("ns-001") is None
