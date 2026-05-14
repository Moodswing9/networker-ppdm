---
description: List and diagnose failed PPDM backup activities — fetches job detail automatically for the top failures
argument-hint: "[--asset-type <TYPE>] [--since <TIMESTAMP>]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If output is `NO_ENV_FILE` or placeholder values, stop and ask the operator to configure `.env`.

## Step 2 — Fetch failed activities as JSON

```bash
python scripts/check_failed_jobs.py --json $ARGUMENTS 2>&1
```

The script exits 1 if failures are found (CI-friendly). Capture both stdout and the exit code.

If the script is not available, fall back to the Python client directly:

```bash
python -c "
from ppdm.client import PPDMClient; import os, json
with PPDMClient(os.environ['PPDM_HOST'], os.environ['PPDM_USER'], os.environ['PPDM_PASS']) as p:
    acts = p.list_activities(state='FAILED')
    print(json.dumps(acts, indent=2))
" 2>&1
```

## Step 3 — Automatic detail fetch for top failures

For each of the **top 3 failures** by recency, immediately fetch the full activity detail to get the error message — do not wait for the operator to ask:

```bash
python -c "
from ppdm.client import PPDMClient; import os, json, sys
activity_id = sys.argv[1]
with PPDMClient(os.environ['PPDM_HOST'], os.environ['PPDM_USER'], os.environ['PPDM_PASS']) as p:
    detail = p._session.get(f'{p._base_url}/activities/{activity_id}').json()
    print(json.dumps(detail.get('error', detail), indent=2))
" <ACTIVITY_ID> 2>&1
```

Substitute the actual activity ID from Step 2 output. Run this once per top failure.

## Step 4 — Group and analyse

**If exit code 0 / no failures:** Output "No failed activities in the last 24 h." and stop.

**If failures found:**

1. Group by asset type: Kubernetes · VMware · Database · NAS · Other
2. Within each group, cluster by failure reason (the `error.message` field from Step 3)
3. For the top 3 most common failure reasons, state the next diagnostic step:

| Error pattern | Next step |
|---------------|-----------|
| `vProxy unreachable` | Check vProxy registration: `backupctl doctor` → vProxy section |
| `Lockbox access denied` | Credential rotation needed — check `/api/v2/credentials` |
| `Storage unit full` | Run `backupctl dd status` — check filesystem capacity |
| `Backup window expired` | Policy schedule misalignment — check `/api/v2/protection-policies` |
| `Token expired` / `auth` | Re-auth issue — verify `PPDM_PASS` is current |

4. Format as a table: `Asset | Type | Error | Suggested Action`

Lead with: *"Based on `check_failed_jobs.py` output, I found [N] failures:"*
