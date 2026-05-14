---
description: Generate SLA compliance report — surfaces non-compliant assets and auto-fetches their recent job history
argument-hint: "[--non-compliant-only] [--policy <NAME>]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If output is `NO_ENV_FILE` or placeholder values, stop and ask the operator to configure `.env`.

## Step 2 — Run the SLA report

```bash
python scripts/sla_report.py $ARGUMENTS 2>&1
```

If the script fails to import (package not installed), fall back to:

```bash
python -m orchestrator.sla $ARGUMENTS 2>&1
```

## Step 3 — For each non-compliant asset, fetch recent job history

For every asset listed as non-compliant, immediately fetch its last 3 activities — do not ask the operator first:

```bash
python -c "
from ppdm.client import PPDMClient; import os, json, sys
asset_name = sys.argv[1]
with PPDMClient(os.environ['PPDM_HOST'], os.environ['PPDM_USER'], os.environ['PPDM_PASS']) as p:
    acts = p.list_activities(filter=f'asset.name eq \"{asset_name}\"', page_size=3)
    for a in acts:
        print(json.dumps({'id': a['id'], 'state': a['state'], 'startTime': a.get('startTime'), 'error': a.get('error')}, indent=2))
" <ASSET_NAME> 2>&1
```

Run this for the top 5 non-compliant assets at most (avoid flooding output).

## Step 4 — Synthesise and respond

**Always lead with the overall compliance percentage prominently.**

Structure the response as:

```
Compliance: NN% (M of N assets compliant)

Non-compliant assets (sorted by hours over SLA):
| Asset | Policy | Last Success | Hours Over SLA | Pattern |
|-------|--------|-------------|----------------|---------|
| ...   | ...    | ...         | ...            | ...     |

Root cause clusters:
- [N] assets: <shared failure reason> → recommended action
```

For the **top non-compliant policy**, state clearly whether the issue is:
- **Schedule misalignment** — SLA window too narrow for job duration
- **Asset registration** — asset exists but is not protected by any matching rule
- **Actual backup failure** — jobs ran but failed (cite the error from Step 3)

If `--non-compliant-only` was passed, skip the compliant section entirely and lead directly with action items.
