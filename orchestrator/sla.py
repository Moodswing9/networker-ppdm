"""SLA report — per-policy protection job compliance over a rolling window."""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from ppdm.client import PPDMClient


def run_sla(hours: int = 24) -> list[dict]:
    """Return per-policy SLA rows for protection jobs in the last N hours.

    Each row: Policy, Total, Succeeded, Failed, Canceled, SLA %
    """
    host = os.environ.get("PPDM_HOST", "")
    user = os.environ.get("PPDM_USER", "")
    pw   = os.environ.get("PPDM_PASS", "")
    if not host:
        return [{"error": "PPDM_HOST not set"}]

    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    with PPDMClient(host, user, pw) as ppdm:
        activities = ppdm._get(
            "/activities",
            params={
                "pageSize": 500,
                "filter": (
                    f'classType in ("JOB","JOB_GROUP") '
                    f'and category eq "PROTECT" '
                    f'and startTime gt "{since}"'
                ),
            },
        ).get("content", [])

    stats: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "succeeded": 0, "failed": 0, "canceled": 0}
    )

    for act in activities:
        policy = (
            act.get("policyName")
            or act.get("protectionPolicyName")
            or (act.get("protectionPolicy") or {}).get("name")
            or "unknown"
        )
        state = act.get("state", "").upper()
        s = stats[policy]
        s["total"] += 1
        if state == "SUCCEEDED":
            s["succeeded"] += 1
        elif state == "FAILED":
            s["failed"] += 1
        elif state in ("CANCELED", "CANCELING"):
            s["canceled"] += 1

    rows = []
    for policy, s in sorted(stats.items()):
        total = s["total"]
        sla_pct = round(s["succeeded"] / total * 100, 1) if total else 0.0
        rows.append({
            "Policy":    policy,
            "Total":     total,
            "Succeeded": s["succeeded"],
            "Failed":    s["failed"],
            "Canceled":  s["canceled"],
            "SLA %":     f"{sla_pct:.1f}%",
        })
    return rows
