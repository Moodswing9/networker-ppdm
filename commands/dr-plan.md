---
description: Generate a comprehensive Disaster Recovery plan using Claude Opus 4.7 extended thinking — surfaces full reasoning chain for operator audit
argument-hint: "[--rpo <hours>] [--rto <hours>] [--json]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If output is `NO_ENV_FILE`, stop and ask the operator to configure `.env`.

## Step 2 — Generate the DR plan

```bash
python scripts/dr_plan.py $ARGUMENTS 2>&1
```

This feeds live PPDM topology (assets, policies, recent failures) into Claude Opus 4.7 with `budget_tokens=8000` of extended thinking. Default: `--rpo 24 --rto 4`. Pass overrides as needed.

The thinking chain is automatically saved to `dr_plan_thinking.md`.

## Step 3 — Present the plan in five sections

Structure the output clearly with headers:

1. **DR Readiness Assessment** — READY / AT RISK / CRITICAL badge + justification
2. **Asset Recovery Tiers** — Tier 1 (restore immediately) through Tier 3 (best-effort), with asset names
3. **Recovery Runbook** — numbered steps with exact CLI commands
4. **Gap Analysis** — assets and failure scenarios not covered by current policies
5. **Policy Recommendations** — specific changes needed to meet stated RPO/RTO

## Step 4 — Offer the thinking transcript

Inform the operator:

> `dr_plan_thinking.md` contains Claude's full extended thinking chain. Run `cat dr_plan_thinking.md` to audit the decision logic before executing the runbook.

If the operator asks to see the thinking, run:

```bash
cat dr_plan_thinking.md 2>&1
```

## Step 5 — Next steps

If the Gap Analysis reveals unprotected Tier 1 assets, offer to create a protection policy via `/ppdm-backup` or generate a policy script via `backupctl generate`.
