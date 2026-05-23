---
description: Cross-platform health check for PPDM, NetWorker, and Data Domain — runs live diagnostics and drills into failures automatically
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

Use the Bash tool to read the environment:

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If the output is `NO_ENV_FILE` or shows only placeholder values (`<your-*>`), stop immediately and tell the operator to copy `.env.example` to `.env` and fill in `PPDM_HOST`, `PPDM_USER`, `PPDM_PASS` (and `NW_HOST`/`NW_USER`/`NW_PASS` for NetWorker, `DD_HOST` for Data Domain).

## Step 2 — Run the unified health check

```bash
backupctl doctor 2>&1
```

If `backupctl` is not on PATH, fall back to:

```bash
python -m orchestrator.doctor 2>&1
```

## Step 3 — Parse and triage the output

Read the output from Step 2. For each product section:

| Symbol | Meaning | Action |
|--------|---------|--------|
| `✓` / `OK` | Healthy | Note, do not drill |
| `⚠` / `WARNING` | Degraded | Drill (Step 4) |
| `✗` / `ERROR` / `CRITICAL` | Failed | Drill (Step 4), prioritise |

Group findings by product: **PPDM · NetWorker · Data Domain**.

## Step 4 — Automatic drill-down for every WARNING or ERROR

Run follow-up Bash commands for each failure. Do not wait for the operator to ask.

**PPDM failures:**
```bash
python scripts/check_failed_jobs.py --json 2>&1
```
Then parse the JSON: extract the `error.message` and `asset.name` for the top 3 failures.

**NetWorker failures:**
```bash
python -c "
from networker.client import NWClient; import os, json
c = NWClient(os.environ['NW_HOST'], os.environ['NW_USER'], os.environ['NW_PASS'])
ss = c.list_savesets(query='savetime>last 24 hours,level=full')
failed = [s for s in ss if s.get('completionCode','') not in ('succeeded','')  ]
print(json.dumps(failed[:5], indent=2))
" 2>&1
```

**Data Domain failures:**
```bash
backupctl dd status 2>&1
```

## Step 5 — Synthesise and respond

Lead with: *"Based on `backupctl doctor` output, I found [N] issues:"*

- List each issue with: product, component, symptom, and the most likely root cause
- For each ERROR, give one concrete next action (specific command or REST endpoint to check)
- If everything is green, confirm in one line: "All systems healthy — PPDM, NetWorker, and Data Domain report no issues."
- **If any PPDM protection jobs failed:** append — *"Run `/ppdm-failed-jobs` for per-job root-cause detail and asset-level history."*
