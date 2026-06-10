"""
Multi-agent DR orchestration pipeline.

Four specialist agents run sequentially:
  1. Monitor   — triages live PPDM state
  2. Diagnose  — root cause analysis
  3. Remediate — prioritised recovery plan with CLI commands
  4. Validate  — safety review + confidence score

Usage:
  python scripts/dr_orchestrate.py [--incident "description"] [--json]
"""

import argparse
import json
import os
import sys
from typing import Any

import anthropic
from ppdm.client import PPDMClient

_MODEL = "claude-opus-4-7"


def _text(msg: anthropic.types.Message) -> str:
    for block in msg.content:
        if block.type == "text":
            return block.text
    return ""


def _collect_state() -> str:
    try:
        with PPDMClient(
            os.environ["PPDM_HOST"],
            os.environ["PPDM_USER"],
            os.environ["PPDM_PASS"],
        ) as ppdm:
            failed  = ppdm.list_activities(state="FAILED",  page_size=20)
            running = ppdm.list_activities(state="RUNNING", page_size=10)
            assets  = ppdm.list_assets(page_size=50)
    except Exception as exc:
        print(f"[dr-orchestrate] PPDM unavailable: {exc}", file=sys.stderr)
        failed, running, assets = [], [], []

    return (
        f"Failed jobs (last 20): {json.dumps(failed[:20], default=str)}\n"
        f"Running jobs: {json.dumps(running[:10], default=str)}\n"
        f"Total protected assets: {len(assets)}"
    )


def run(incident: str | None = None, json_output: bool = False) -> dict[str, Any]:
    client = anthropic.Anthropic()
    state  = _collect_state()

    # ── Agent 1: Monitor ──────────────────────────────────────────────────────
    m1 = client.messages.create(
        model=_MODEL, max_tokens=2048,
        thinking={"type": "adaptive"},
        system=(
            "You are a backup monitoring agent for Dell EMC PPDM and NetWorker. "
            "Analyse the current backup state and produce a concise triage report: "
            "severity (CRITICAL / WARNING / INFO), affected asset count, "
            "top failure categories, and any cascading risk indicators."
        ),
        messages=[{"role": "user", "content": f"{state}\nIncident: {incident or 'General DR assessment'}"}],
    )

    # ── Agent 2: Diagnose ─────────────────────────────────────────────────────
    m2 = client.messages.create(
        model=_MODEL, max_tokens=2048,
        thinking={"type": "adaptive"},
        system=(
            "You are a backup root-cause analysis agent for Dell EMC environments. "
            "Identify the primary root cause and up to three contributing factors. "
            "Be specific: cite error patterns, component names, and likely triggers "
            "(network, storage, credentials, schedule)."
        ),
        messages=[{"role": "user", "content": f"Triage report:\n{_text(m1)}\n\nPerform root cause analysis."}],
    )

    # ── Agent 3: Remediate ────────────────────────────────────────────────────
    m3 = client.messages.create(
        model=_MODEL, max_tokens=4096,
        thinking={"type": "adaptive"},
        system=(
            "You are a backup remediation agent for Dell EMC PPDM and NetWorker. "
            "Generate a step-by-step recovery plan with copy-pasteable CLI commands "
            "(backupctl, REST curl examples). Order by priority: data-at-risk assets first. "
            "Include rollback steps for any destructive action."
        ),
        messages=[{"role": "user", "content": f"Root cause analysis:\n{_text(m2)}\n\nGenerate the remediation plan."}],
    )

    # ── Agent 4: Validate ─────────────────────────────────────────────────────
    m4 = client.messages.create(
        model=_MODEL, max_tokens=1024,
        system=(
            "You are a backup plan validation agent. Review the remediation plan for safety, "
            "completeness, and risk. Flag missing steps, destructive commands without safeguards, "
            "or unverified infrastructure assumptions. "
            "End with: Confidence score X/10 and a one-line Go / No-Go verdict."
        ),
        messages=[{"role": "user", "content": f"Remediation plan:\n{_text(m3)}\n\nValidate this plan."}],
    )

    result = {
        "monitor":   _text(m1),
        "diagnose":  _text(m2),
        "remediate": _text(m3),
        "validate":  _text(m4),
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        div = "─" * 72
        for title, key in [
            ("🔍 MONITOR — Triage Report",        "monitor"),
            ("🧠 DIAGNOSE — Root Cause Analysis",  "diagnose"),
            ("🛠  REMEDIATE — Recovery Plan",       "remediate"),
            ("✅ VALIDATE — Safety Review",         "validate"),
        ]:
            print(f"\n{div}\n{title}\n{div}")
            print(result[key])
        print(f"\n{div}")

    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Multi-agent DR orchestration")
    p.add_argument("--incident", default=None)
    p.add_argument("--json", dest="json_output", action="store_true")
    args = p.parse_args()
    run(incident=args.incident, json_output=args.json_output)


if __name__ == "__main__":
    main()
