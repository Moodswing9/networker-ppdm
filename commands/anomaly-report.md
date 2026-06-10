---
description: Detect anomalous, degrading, and failed backup jobs over a configurable history window using the Claude Batch API
argument-hint: "[--days <N>] [--wait] [--batch-id <ID>]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If output is `NO_ENV_FILE`, stop and ask the operator to configure `.env`.

## Step 2 — Submit batch or retrieve results

```bash
python scripts/anomaly_report.py $ARGUMENTS 2>&1
```

**Behaviour:**
- Without `--wait`: fetches up to 500 activities from PPDM, submits each as a separate Batch API request to Claude Haiku, prints the batch ID, and exits. Cost-efficient — Haiku processes the full window asynchronously.
- With `--wait`: blocks until the batch completes, polling every 30 s (24 h max timeout).
- With `--batch-id <ID>`: resumes a previously submitted batch without re-fetching PPDM data.

Default window: 30 days. Pass `--days` to change.

## Step 3 — Interpret the report

The report classifies every activity into:
- **ANOMALOUS** — failed or completed with errors (risk score 6–10)
- **DEGRADING** — succeeded but shows declining performance trends (risk score 3–7)
- **NORMAL** — completed within expected parameters (risk score 0–3)

Each entry shows a risk score (0–10) and a one-sentence reason.

## Step 4 — Surface actionable insights

Compute and present:
1. **Overall health score**: `(NORMAL / total) × 100`%
2. **Top 3 failure patterns** by frequency across the window
3. **Highest-risk assets**: top 5 ANOMALOUS items sorted by risk score

For any asset with risk score ≥ 8, cross-reference with `/ppdm-failed-jobs` to fetch full error detail immediately — do not wait for the operator to ask.

## Step 5 — Escalation

If more than 15% of jobs are ANOMALOUS or DEGRADING, recommend running `/dr-orchestrate` for a full multi-agent remediation cycle.
