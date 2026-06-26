---
description: Guided PPDM restore wizard — browse assets, select a recovery copy, choose target, confirm, and trigger. Walks through every step without requiring the operator to know REST API details.
argument-hint: "[--asset <name>] [--type <TYPE>] [--dry-run]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If output is `NO_ENV_FILE` or placeholder values, stop and ask the operator to configure `.env`.

## Step 2 — Asset discovery

Parse `$ARGUMENTS` for `--asset NAME` and `--type TYPE` filters.

List matching assets:

```bash
python -c "
from ppdm.client import PPDMClient
import os, json

args = '$ARGUMENTS'.split()
name_filter = None
type_filter = None
for i, a in enumerate(args):
    if a == '--asset' and i + 1 < len(args): name_filter = args[i + 1]
    if a == '--type'  and i + 1 < len(args): type_filter = args[i + 1]

with PPDMClient.from_env() as p:
    assets = p.list_assets(name=name_filter, asset_type=type_filter)
    print(json.dumps(assets[:20], indent=2))
" 2>&1
```

Present assets as a numbered list:

```
[1] prod-k8s-namespace   KUBERNETES         PROTECTED   last backup: 2026-06-25 02:14
[2] sql-db-01            MICROSOFT_SQL_SERVER  PROTECTED   last backup: 2026-06-25 01:05
[3] web-vm-prod          VMWARE_VIRTUAL_MACHINE  PROTECTED   last backup: 2026-06-24 23:30
```

Ask the operator: **"Which asset do you want to restore? (enter number or name)"**

## Step 3 — Browse available copies

Once the operator selects an asset, list its recovery copies:

```bash
python -c "
from ppdm.client import PPDMClient
import os, json
asset_id = '<ASSET_ID>'
with PPDMClient.from_env() as p:
    copies = p.list_copies(asset_id)
    print(json.dumps(copies[:10], indent=2))
" 2>&1
```

Present copies as a table:

```
[1] 2026-06-25 02:14  FULL    retention: 2026-07-25   copy_id: abc-123
[2] 2026-06-24 02:11  FULL    retention: 2026-07-24   copy_id: def-456
[3] 2026-06-23 02:09  FULL    retention: 2026-07-23   copy_id: ghi-789
```

Ask the operator: **"Which copy do you want to restore from? (enter number, default = latest)"**

Default to the most recent copy if the operator presses Enter or says "latest".

## Step 4 — Choose restore target

Ask the operator:

> Where should this be restored?
> [1] Original location (in-place overwrite)
> [2] New location (specify target details)
> [3] Restore files only (file-level, if supported)

Wait for operator input.

**If option 1 (original location):**
- Warn: "This will overwrite the current state of `<asset name>`. Type CONFIRM to proceed."
- Do not proceed without explicit confirmation.

**If option 2 (new location):**
- For KUBERNETES: ask for target namespace name and target cluster ID
- For VMWARE: ask for target datastore and target host
- For SQL: ask for target instance and database name

**If option 3 (file-level):**
- Ask for target path and list of files/directories to restore (comma-separated)

## Step 5 — Summary and confirmation

Before triggering, display a full restore summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RESTORE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Asset:       <name> (<type>)
  Copy date:   <timestamp>
  Copy ID:     <id>
  Target:      <original / new location details>
  Dry run:     <yes / no>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ask: **"Proceed with restore? (yes / no)"**

Do not trigger without explicit "yes".

## Step 6 — Trigger restore

If `$ARGUMENTS` contains `--dry-run`, skip the actual API call and output: *"Dry run complete — no restore was triggered."*

Otherwise:

```bash
python -c "
from ppdm.client import PPDMClient
import os, json

copy_id  = '<COPY_ID>'
asset_id = '<ASSET_ID>'
target   = <TARGET_DICT>

with PPDMClient.from_env() as p:
    result = p.restore(copy_id=copy_id, asset_id=asset_id, target=target)
    print(json.dumps(result, indent=2))
" 2>&1
```

## Step 7 — Monitor progress

After triggering, capture the activity ID from the result and poll for completion:

```bash
python -c "
from ppdm.client import PPDMClient
import os, json, time

activity_id = '<ACTIVITY_ID>'
terminal    = {'SUCCEEDED', 'FAILED', 'CANCELED', 'SKIPPED'}

with PPDMClient.from_env() as p:
    for _ in range(120):  # max 30 minutes at 15s interval
        act = p.list_activities(activity_id=activity_id)
        state = act[0].get('state', '') if act else ''
        print(f'Status: {state}', flush=True)
        if state.upper() in terminal:
            print(json.dumps(act[0], indent=2))
            break
        time.sleep(15)
" 2>&1
```

Report the final outcome:
- **SUCCEEDED** — *"Restore completed successfully."* + duration + bytes transferred
- **FAILED** — *"Restore failed."* + error message + suggested next step
- **CANCELED** — *"Restore was canceled."*
