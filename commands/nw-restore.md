---
description: Guided NetWorker saveset restore wizard — browse savesets by client, select a saveset, choose target path, confirm, and trigger nsr_recover. Full recovery flow without leaving Claude Code.
argument-hint: "[--client <name>] [--dry-run]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If `NW_HOST`, `NW_USER`, `NW_PASS` are missing, stop and ask the operator to configure `.env`.

## Step 2 — Client discovery

Parse `$ARGUMENTS` for `--client NAME`.

If `--client` is specified, skip directly to Step 3 with that client name.
Otherwise, list available clients:

```bash
python -c "
import requests, os, json, urllib3
urllib3.disable_warnings()
auth = (os.environ['NW_USER'], os.environ['NW_PASS'])
res  = requests.get(f'https://{os.environ[\"NW_HOST\"]}:9090/nwrestapi/v3/global/clients',
                    auth=auth, verify=False)
clients = res.json().get('clients', [])
for i, c in enumerate(clients[:20], 1):
    print(f'[{i}] {c[\"hostname\"]} (id: {c[\"resourceId\"][\"id\"]})')
" 2>&1
```

Ask: **"Which client do you want to restore from? (enter number or hostname)"**

## Step 3 — Browse savesets for client

```bash
python -c "
import requests, os, json, urllib3
urllib3.disable_warnings()
auth   = (os.environ['NW_USER'], os.environ['NW_PASS'])
client = '<CLIENT_NAME>'
res    = requests.get(
    f'https://{os.environ[\"NW_HOST\"]}:9090/nwrestapi/v3/global/savesets',
    auth=auth, verify=False, params={'q': f'clientName:{client}', 'count': 20}
)
savesets = res.json().get('savesets', [])
for i, s in enumerate(savesets, 1):
    size_mb = round(s.get('size', 0) / 1024 / 1024, 1)
    print(f'[{i}] {s[\"saveTime\"]}  level={s.get(\"level\",\"?\")}  status={s.get(\"status\",\"?\")}  {size_mb} MB  id={s[\"resourceId\"][\"id\"]}')
print(json.dumps(savesets, indent=2))
" 2>&1
```

Present as a numbered table. Ask: **"Which saveset do you want to restore? (enter number, default = most recent)"**

Default to `[1]` (most recent) if the operator presses Enter or says "latest".

## Step 4 — Choose restore target

Ask the operator:

> Where should this be restored?
> [1] Original path (overwrite in place)
> [2] Alternate path (specify destination directory)

**If option 1 (original path):**
- Warn: "This will overwrite files at their original location on `<client>`. Type CONFIRM to proceed."
- Do not proceed without explicit confirmation.

**If option 2 (alternate path):**
- Ask: "Enter the target directory path on the destination host."
- Ask: "Is the destination a different host? (Enter hostname, or press Enter to use original client)"

## Step 5 — Restore summary and confirmation

Before triggering, display:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RESTORE SUMMARY — NetWorker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Client:      <hostname>
  Saveset ID:  <id>
  Save time:   <timestamp>
  Level:       <FULL / INCR>
  Target host: <hostname>
  Target path: <original / alternate path>
  Dry run:     <yes / no>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ask: **"Proceed with restore? (yes / no)"**

Do not trigger without explicit "yes".

## Step 6 — Trigger restore

If `$ARGUMENTS` contains `--dry-run`, output: *"Dry run complete — no restore was triggered."* and stop.

Otherwise, trigger via REST API:

```bash
python -c "
import requests, os, json, urllib3
urllib3.disable_warnings()
auth       = (os.environ['NW_USER'], os.environ['NW_PASS'])
saveset_id = '<SAVESET_ID>'
target_client = '<TARGET_CLIENT>'
target_path   = '<TARGET_PATH>'   # None for original

body = {
    'savesetResourceIds': [saveset_id],
    'destinationClient':  target_client,
}
if target_path and target_path != 'original':
    body['restoreDestinationPath'] = target_path

res = requests.post(
    f'https://{os.environ[\"NW_HOST\"]}:9090/nwrestapi/v3/global/recoveries',
    auth=auth, verify=False, json=body
)
print(json.dumps(res.json(), indent=2))
" 2>&1
```

## Step 7 — Confirm and report

Parse the response for a job or recovery ID. Report:

- **Success**: "Restore job submitted. Recovery ID: `<id>`. Monitor via NetWorker Management Console or `mmrecov` on the server."
- **Failure**: Error message + suggested next step (check NW server logs at `/nsr/logs/messages`)
