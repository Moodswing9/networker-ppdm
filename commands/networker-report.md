---
description: Generate a weekly NetWorker backup summary — saveset success rates, failed clients, data volume, and policy compliance across the last 7 days
argument-hint: "[--days <N>] [--client <name>] [--json]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

If output is `NO_ENV_FILE` or placeholder values, stop and ask the operator to configure `.env` with `NW_HOST`, `NW_USER`, `NW_PASS`.

## Step 2 — Fetch savesets for the reporting window

Parse `$ARGUMENTS` for `--days N` (default 7) and `--client NAME` (optional).

```bash
python -c "
from networker.client import NWClient
import os, json, sys
from datetime import datetime, timedelta, timezone

args = '$ARGUMENTS'.split()
days = 7
client_filter = None
for i, a in enumerate(args):
    if a == '--days' and i + 1 < len(args):
        days = int(args[i + 1])
    if a == '--client' and i + 1 < len(args):
        client_filter = args[i + 1]

nw = NWClient(os.environ['NW_HOST'], os.environ['NW_USER'], os.environ['NW_PASS'])
cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

savesets = nw.list_savesets(client_name=client_filter)
recent = [s for s in savesets if s.get('saveTime', '') >= cutoff]
print(json.dumps({'savesets': recent, 'days': days, 'cutoff': cutoff}, indent=2))
" 2>&1
```

If `NWClient` is unavailable, fall back to a direct REST call:

```bash
python -c "
import requests, os, json, urllib3
urllib3.disable_warnings()
host = os.environ['NW_HOST']
auth = (os.environ['NW_USER'], os.environ['NW_PASS'])
url = f'https://{host}:9090/nwrestapi/v3/global/savesets'
res = requests.get(url, auth=auth, verify=False, params={'count': 500})
print(json.dumps(res.json(), indent=2))
" 2>&1
```

## Step 3 — Fetch client list

```bash
python -c "
import requests, os, json, urllib3
urllib3.disable_warnings()
host = os.environ['NW_HOST']
auth = (os.environ['NW_USER'], os.environ['NW_PASS'])
res = requests.get(f'https://{host}:9090/nwrestapi/v3/global/clients', auth=auth, verify=False)
print(json.dumps(res.json().get('clients', []), indent=2))
" 2>&1
```

## Step 4 — Compile the weekly report

Using data from Steps 2–3, produce a structured report in this format:

---

## NetWorker Weekly Report — Last `<N>` Days

**Generated:** `<current datetime>`  
**Server:** `<NW_HOST>`

### Summary

| Metric | Value |
|--------|-------|
| Total savesets | N |
| Successful | N (XX%) |
| Failed / incomplete | N |
| Total data protected | X.X GB |
| Unique clients backed up | N |
| Clients with failures | N |

### Failed Savesets

List each failed saveset: `Client | Save Set Name | Status | Save Time`

If none, output: *No failed savesets in the reporting window.*

### Top Clients by Data Volume

Top 5 clients by total bytes transferred, descending.

### Policy Compliance

For each client in the client list: was at least one successful saveset completed in the window?
- **Compliant** — at least one successful saveset
- **Non-compliant** — no successful saveset in the window

Output: `Client | Status | Last Successful Backup`

### Recommendations

Based on the data:
1. If failure rate > 10%: flag systemic issue, suggest `backupctl doctor`
2. If any client has zero savesets: flag as uncovered
3. If data volume dropped > 20% week-over-week: flag potential scope reduction

---

## Step 5 — JSON output (if --json flag present)

If `$ARGUMENTS` contains `--json`, output the raw saveset array as JSON instead of the formatted report.
