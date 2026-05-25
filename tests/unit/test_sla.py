"""Unit tests for orchestrator.sla.run_sla()."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from orchestrator.sla import run_sla


ACTIVITIES = [
    {"classType": "JOB", "category": "PROTECT", "state": "SUCCEEDED", "policyName": "k8s-daily"},
    {"classType": "JOB", "category": "PROTECT", "state": "SUCCEEDED", "policyName": "k8s-daily"},
    {"classType": "JOB", "category": "PROTECT", "state": "FAILED",    "policyName": "k8s-daily"},
    {"classType": "JOB", "category": "PROTECT", "state": "SUCCEEDED", "policyName": "vm-nightly"},
    {"classType": "JOB", "category": "PROTECT", "state": "CANCELED",  "policyName": "vm-nightly"},
    {"classType": "JOB", "category": "PROTECT", "state": "SUCCEEDED", "policyName": "sql-hourly"},
]


def _make_ppdm_mock(activities: list[dict]) -> MagicMock:
    mock_client = MagicMock()
    mock_client._get.return_value = {"content": activities}
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


@patch.dict("os.environ", {"PPDM_HOST": "ppdm.test", "PPDM_USER": "admin", "PPDM_PASS": "pass"})
@patch("orchestrator.sla.PPDMClient")
def test_sla_row_count(mock_cls):
    mock_cls.return_value = _make_ppdm_mock(ACTIVITIES)
    rows = run_sla(hours=24)
    assert len(rows) == 3


@patch.dict("os.environ", {"PPDM_HOST": "ppdm.test", "PPDM_USER": "admin", "PPDM_PASS": "pass"})
@patch("orchestrator.sla.PPDMClient")
def test_sla_percentages(mock_cls):
    mock_cls.return_value = _make_ppdm_mock(ACTIVITIES)
    rows = run_sla(hours=24)
    by_policy = {r["Policy"]: r for r in rows}

    assert by_policy["k8s-daily"]["Total"] == 3
    assert by_policy["k8s-daily"]["Succeeded"] == 2
    assert by_policy["k8s-daily"]["Failed"] == 1
    assert by_policy["k8s-daily"]["SLA %"] == "66.7%"

    assert by_policy["vm-nightly"]["Canceled"] == 1
    assert by_policy["vm-nightly"]["SLA %"] == "50.0%"

    assert by_policy["sql-hourly"]["SLA %"] == "100.0%"


@patch.dict("os.environ", {"PPDM_HOST": "ppdm.test", "PPDM_USER": "admin", "PPDM_PASS": "pass"})
@patch("orchestrator.sla.PPDMClient")
def test_sla_empty_activities(mock_cls):
    mock_cls.return_value = _make_ppdm_mock([])
    rows = run_sla(hours=24)
    assert rows == []


@patch.dict("os.environ", {"PPDM_HOST": ""})
def test_sla_no_host_returns_error():
    rows = run_sla()
    assert len(rows) == 1
    assert "error" in rows[0]


@patch.dict("os.environ", {"PPDM_HOST": "ppdm.test", "PPDM_USER": "admin", "PPDM_PASS": "pass"})
@patch("orchestrator.sla.PPDMClient")
def test_sla_fallback_policy_name(mock_cls):
    """Activity with no policyName falls back through protectionPolicyName then protectionPolicy.name."""
    acts = [
        {"state": "SUCCEEDED", "protectionPolicy": {"name": "fallback-policy"}},
    ]
    mock_cls.return_value = _make_ppdm_mock(acts)
    rows = run_sla()
    assert rows[0]["Policy"] == "fallback-policy"
