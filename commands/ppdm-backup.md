---
description: Trigger an on-demand PPDM protection job — validates asset and policy first, then fires and optionally polls to completion
argument-hint: "--asset <NAME> --policy <NAME> [--wait]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If output is `NO_ENV_FILE` or placeholder values, stop and ask the operator to configure `.env`.

## Step 2 — Validate asset and policy before triggering

Before firing any backup, confirm both the asset and policy exist. Run this regardless of whether `$ARGUMENTS` includes them:

```bash
python -c "
from ppdm.client import PPDMClient; import os, json
with PPDMClient(os.environ['PPDM_HOST'], os.environ['PPDM_USER'], os.environ['PPDM_PASS']) as p:
    policies = [pol['name'] for pol in p.list_policies()]
    assets = [a['name'] for a in p.list_assets()]
    print(json.dumps({'policies': policies, 'assets': assets}, indent=2))
" 2>&1
```

- If the asset name from `$ARGUMENTS` matches **exactly one** asset: proceed
- If it matches **zero**: stop and tell the operator — list the 5 closest asset names (fuzzy match by prefix)
- If it matches **more than one**: stop and ask the operator to confirm which one to use
- Apply the same logic to the policy name

## Step 3 — Trigger the on-demand backup

Once asset and policy are confirmed:

```bash
python scripts/ondemand_backup.py $ARGUMENTS 2>&1
```

Capture the activity ID from the output. It will appear as `Activity ID: <uuid>`.

## Step 4 — Poll if `--wait` was passed

If `--wait` is in `$ARGUMENTS`, poll the activity status every 15 seconds until terminal state (`OK`, `FAILED`, `CANCELED`):

```bash
python -c "
from ppdm.client import PPDMClient; import os, json, sys, time
activity_id = sys.argv[1]
terminal = {'OK', 'FAILED', 'CANCELED', 'SKIPPED'}
with PPDMClient(os.environ['PPDM_HOST'], os.environ['PPDM_USER'], os.environ['PPDM_PASS']) as p:
    while True:
        detail = p._session.get(f'{p._base_url}/activities/{activity_id}').json()
        state = detail.get('state', 'UNKNOWN')
        pct = detail.get('percentComplete', 0)
        print(f'State: {state}  Progress: {pct}%', flush=True)
        if state in terminal:
            print(json.dumps(detail, indent=2))
            break
        time.sleep(15)
" <ACTIVITY_ID> 2>&1
```

On completion, summarise: activity ID, final state, duration, bytes transferred (from `statistics` field if present).

## Step 5 — Error handling

If the trigger fails, diagnose immediately using the Bash tool — do not ask the operator to investigate:

| Error pattern | Automatic follow-up |
|---------------|---------------------|
| `policy not found` | Run `backupctl inventory --format json \| python -c "import sys,json; [print(p['name']) for p in json.load(sys.stdin)['ppdm']['policies']]"` and list available policies |
| `asset not assigned` | Check asset protection rules: `p.list_policies()` — find which policy covers this asset type |
| `protection rule conflict` | Fetch asset detail and show current policy assignments |
| `credentials expired` | Run `backupctl doctor` to surface the lockbox refresh guidance |
