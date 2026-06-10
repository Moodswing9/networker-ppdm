---
description: Multi-agent DR orchestration — four specialist Claude agents triage, diagnose, remediate, and validate a disaster recovery response
argument-hint: "[--incident 'description'] [--json]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If output is `NO_ENV_FILE` or placeholder values, stop and ask the operator to configure `.env`.

## Step 2 — Run the four-agent pipeline

```bash
python scripts/dr_orchestrate.py $ARGUMENTS 2>&1
```

Four Claude Opus 4.7 agents run sequentially — each receives the previous agent's output as context:

1. **Monitor** — collects live PPDM state (failed/running jobs, asset count) and triages severity
2. **Diagnose** — performs root cause analysis, identifies primary cause and up to three contributing factors
3. **Remediate** — generates a prioritised recovery plan with copy-pasteable CLI commands and rollback steps
4. **Validate** — reviews the plan for safety, flags risks, and issues a confidence score with Go / No-Go verdict

## Step 3 — Present the results

Lead with the **Validate** agent's verdict:
- If **Go** with confidence ≥ 7/10: present the Remediate plan as a numbered checklist, offer to execute step 1 via `/ppdm-backup` or `backupctl`
- If **No-Go** or confidence < 7/10: list the specific gaps the Validate agent flagged and ask the operator which to resolve first

Always show the Monitor severity badge (CRITICAL / WARNING / INFO) prominently at the top.

## Step 4 — Escalation path

If severity is CRITICAL and confidence ≥ 7/10, suggest running `/dr-plan` for a full RPO/RTO-aware disaster recovery plan.
