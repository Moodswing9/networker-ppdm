"""
Extended-thinking DR planner.

Feeds PPDM topology into Claude Opus 4.7 with a high thinking budget
and generates a comprehensive DR plan.  The raw thinking chain is
saved to dr_plan_thinking.md for operator audit.

Usage:
  python scripts/dr_plan.py [--rpo <hours>] [--rto <hours>] [--json]
"""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic
from ppdm.client import PPDMClient

_MODEL          = "claude-opus-4-7"
_THINKING_BUDGET = 8000
_MAX_OUTPUT     = 4096


def _topology() -> dict:
    try:
        with PPDMClient(
            os.environ["PPDM_HOST"],
            os.environ["PPDM_USER"],
            os.environ["PPDM_PASS"],
        ) as ppdm:
            assets   = ppdm.list_assets(page_size=100)
            policies = ppdm.list_policies()
            failed   = ppdm.list_activities(state="FAILED", page_size=30)
    except Exception as exc:
        print(f"[dr-plan] PPDM unavailable ({exc}), using empty topology.", file=sys.stderr)
        assets, policies, failed = [], [], []
    return {"assets": assets, "policies": policies, "recent_failures": failed}


def run(rpo_hours: int = 24, rto_hours: int = 4, json_output: bool = False) -> dict:
    client = anthropic.Anthropic()
    topo   = _topology()

    prompt = (
        f"## Backup Topology\n"
        f"- Protected assets: {len(topo['assets'])}\n"
        f"- Protection policies: {len(topo['policies'])}\n"
        f"- Recent failures (last 30): {len(topo['recent_failures'])}\n\n"
        f"Asset sample (first 10):\n{json.dumps(topo['assets'][:10], default=str, indent=2)}\n\n"
        f"Policy sample (first 5):\n{json.dumps(topo['policies'][:5], default=str, indent=2)}\n\n"
        f"Recent failures:\n{json.dumps(topo['recent_failures'][:10], default=str, indent=2)}\n\n"
        f"## Requirements\n"
        f"- RPO: {rpo_hours} hours\n"
        f"- RTO: {rto_hours} hours\n\n"
        f"## Deliverables\n"
        f"1. DR Readiness Assessment (READY / AT RISK / CRITICAL) with justification\n"
        f"2. Asset recovery priority tiers (Tier 1 = restore immediately, Tier 3 = best-effort)\n"
        f"3. Step-by-step recovery runbook with PPDM/NetWorker commands\n"
        f"4. Gap analysis: assets and scenarios NOT covered by current policies\n"
        f"5. Recommended policy changes to meet the stated RPO/RTO targets\n"
    )

    msg = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_OUTPUT + _THINKING_BUDGET,
        thinking={"type": "enabled", "budget_tokens": _THINKING_BUDGET},
        system=(
            "You are a senior disaster recovery architect specialising in Dell EMC "
            "PowerProtect Data Manager and NetWorker. Apply methodical DR planning: "
            "consider data criticality, recovery dependencies, network paths, and "
            "credential availability under failure conditions."
        ),
        messages=[{"role": "user", "content": prompt}],
    )

    plan, thinking = "", ""
    for block in msg.content:
        if block.type == "thinking":
            thinking = block.thinking
        elif block.type == "text":
            plan = block.text

    sidecar = Path("dr_plan_thinking.md")
    sidecar.write_text(f"# DR Plan — Extended Thinking\n\n{thinking}\n")

    result = {
        "rpo_hours": rpo_hours,
        "rto_hours": rto_hours,
        "plan": plan,
        "thinking_saved_to": str(sidecar),
        "topology": {k: len(v) for k, v in topo.items()},
    }

    if json_output:
        meta = {k: v for k, v in result.items() if k != "plan"}
        print(json.dumps(meta, indent=2))
        print("\n" + "─" * 72 + "\n")
        print(plan)
    else:
        print("\n" + "═" * 72)
        print(f"  DISASTER RECOVERY PLAN   RPO: {rpo_hours}h  |  RTO: {rto_hours}h")
        print("═" * 72 + "\n")
        print(plan)
        print(f"\n[Extended thinking saved → {sidecar}]")

    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Extended-thinking DR planner")
    p.add_argument("--rpo",  type=int, default=24)
    p.add_argument("--rto",  type=int, default=4)
    p.add_argument("--json", dest="json_output", action="store_true")
    args = p.parse_args()
    run(rpo_hours=args.rpo, rto_hours=args.rto, json_output=args.json_output)


if __name__ == "__main__":
    main()
