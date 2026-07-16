---
description: Monitor active and recent PPDM restore sessions — list all sessions, check status by ID, or cancel a running restore.
argument-hint: "[--session-id <id>] [--cancel] [--state RUNNING|COMPLETED|FAILED]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If output is `NO_ENV_FILE` or placeholder values, stop and ask the operator to configure `.env`.

## Step 2 — Parse arguments

Parse `$ARGUMENTS` for:
- `--session-id <id>` — get status of a specific session
- `--cancel` — cancel the session specified by `--session-id`
- `--state <STATE>` — filter list by state (RUNNING, COMPLETED, FAILED, CANCELED)

## Step 3a — If `--session-id` provided (with or without `--cancel`)

```bash
python -c "
from ppdm.client import PPDMClient
import json

session_id = '<SESSION_ID>'

with PPDMClient.from_env() as p:
    session = p.get_restore(session_id)
    print(json.dumps(session, indent=2))
" 2>&1
```

Display a formatted status card:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RESTORE SESSION: <id>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  State:    <state>
  Asset:    <assetName> (<assetType>)
  Started:  <startTime>
  Progress: <percentComplete>%
  Bytes:    <bytesRestored> GiB restored
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If `--cancel` is also present and state is RUNNING:
- Warn: "This will cancel restore session `<id>`. Type CONFIRM to proceed."
- Only if operator confirms:

```bash
python -c "
from ppdm.client import PPDMClient
import json

session_id = '<SESSION_ID>'

with PPDMClient.from_env() as p:
    result = p.cancel_restore(session_id)
    print('Restore session cancelled.' if result is None else json.dumps(result))
" 2>&1
```

If state is not RUNNING, inform the operator: "Session is already in terminal state `<state>` — cannot cancel."

## Step 3b — If no `--session-id`, list recent sessions

```bash
python -c "
from ppdm.client import PPDMClient
import json

state_filter = '<STATE_FILTER_OR_EMPTY>'

with PPDMClient.from_env() as p:
    sessions = p.list_restores(state=state_filter if state_filter else None)
    print(json.dumps(sessions[:20], indent=2))
" 2>&1
```

Present as a table:

```
#   Session ID          State       Asset                   Started              Progress
1   abc-123-def         RUNNING     prod-k8s-ns             2026-07-16 14:02     45%
2   ghi-456-jkl         COMPLETED   sql-db-01               2026-07-16 10:30     100%
3   mno-789-pqr         FAILED      web-vm-prod             2026-07-15 23:14     12%
```

If no sessions found, say: "No restore sessions found" (with the applied filter, if any).

If any session is RUNNING, offer: "Run `/restore-monitor --session-id <id>` to track a specific session, or add `--cancel` to stop it."

If any session is FAILED, suggest: "Run `/ppdm-doctor` or check the PPDM UI for error details on the failed session."
