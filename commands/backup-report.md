---
description: Cross-platform executive backup report — combines PPDM, NetWorker, and Data Domain into a single health summary with job success rates, SLA compliance, capacity status, top failures, and prioritised recommendations
argument-hint: "[--hours <N>] [--json]"
allowed-tools: ["Bash", "Read"]
---

**Do not ask the operator to run commands. Execute every step yourself using the Bash tool.**

## Step 1 — Pre-flight: load credentials

```bash
cat .env 2>/dev/null || cat .env.example 2>/dev/null || echo "NO_ENV_FILE"
```

Note which of `PPDM_HOST`, `NW_HOST`, `DD_HOST` are set. Collect data only from configured products. If none are set, stop and ask the operator to configure `.env`.

Parse `$ARGUMENTS` for `--hours N` (default 24).

## Step 2 — PPDM data

```bash
python -c "
from ppdm.client import PPDMClient
import os, json
with PPDMClient.from_env() as p:
    failed  = p.list_activities(state='FAILED',    page_size=100)
    running = p.list_activities(state='RUNNING',   page_size=50)
    success = p.list_activities(state='SUCCEEDED', page_size=200)
    assets  = p.list_assets(page_size=200)
    print(json.dumps({
        'failed':  failed,
        'running': running,
        'success': success,
        'assets':  assets,
    }, indent=2))
" 2>&1
```

Also fetch SLA compliance:

```bash
python scripts/sla_report.py --json 2>&1
```

## Step 3 — NetWorker data

```bash
python -c "
import requests, os, json, urllib3
urllib3.disable_warnings()
host = os.environ.get('NW_HOST','')
if not host:
    print(json.dumps({'skipped': True}))
else:
    auth = (os.environ['NW_USER'], os.environ['NW_PASS'])
    base = f'https://{host}:9090/nwrestapi/v3/global'
    savesets = requests.get(f'{base}/savesets', auth=auth, verify=False, params={'count':200}).json().get('savesets',[])
    clients  = requests.get(f'{base}/clients',  auth=auth, verify=False).json().get('clients',[])
    print(json.dumps({'savesets': savesets, 'clients': clients}, indent=2))
" 2>&1
```

## Step 4 — Data Domain data

```bash
python -c "
import requests, os, json, urllib3
urllib3.disable_warnings()
host = os.environ.get('DD_HOST','')
if not host:
    print(json.dumps({'skipped': True}))
else:
    auth = (os.environ['DD_USER'], os.environ['DD_PASS'])
    base = f'https://{host}:3009/rest/v1.0'
    fs   = requests.get(f'{base}/filesystems', auth=auth, verify=False).json()
    sus  = requests.get(f'{base}/ddboost/storage-units', auth=auth, verify=False).json()
    print(json.dumps({'filesystem': fs, 'storage_units': sus}, indent=2))
" 2>&1
```

## Step 5 — Compile the executive report

Using all data collected, produce the report in this exact format:

---

# Backup Infrastructure Report

**Generated:** `<datetime>`
**Window:** Last `<N>` hours
**Products:** `<PPDM · NetWorker · Data Domain>` (or "not configured" for missing)

---

## Overall Status: [🟢 HEALTHY / 🟡 WARNING / 🔴 CRITICAL]

> One-sentence executive summary of the most important finding across all products.

---

## PPDM

| Metric | Value |
|--------|-------|
| Total jobs | N |
| Succeeded | N (XX%) |
| Failed | N |
| Running | N |
| SLA compliance | XX% |
| Assets protected | N |

**Top failures** (up to 5):

| Asset | Type | Error |
|-------|------|-------|
| ... | ... | ... |

---

## NetWorker

| Metric | Value |
|--------|-------|
| Total savesets | N |
| Successful | N (XX%) |
| Failed | N |
| Clients reporting | N |

**Failed savesets** (up to 5): `Client | Save Set | Status`

---

## Data Domain

| Metric | Value |
|--------|-------|
| Total capacity | X.X GiB |
| Used | X.X GiB (XX%) |
| Available | X.X GiB |
| Storage units | N |
| DDBoost | enabled / disabled |

Capacity status: 🔴 CRITICAL (>85%) / 🟡 WARNING (>75%) / 🟢 OK

---

## Prioritised Action Items

Ordered by severity across all products:

1. 🔴 **[CRITICAL]** `<what>` — `<exact command to run>`
2. 🟡 **[WARNING]** `<what>` — `<exact command to run>`
3. ...

If no action items: *"All products healthy — no action required."*

---

## Products Skipped

List any products not configured, with the env vars needed to enable them.

---

**Severity thresholds applied:**

| Condition | Severity |
|-----------|----------|
| Any PPDM job FAILED | CRITICAL |
| PPDM SLA < 90% | CRITICAL |
| PPDM SLA 90–95% | WARNING |
| Any NetWorker saveset failed | WARNING |
| DD capacity > 85% | CRITICAL |
| DD capacity > 75% | WARNING |
| All healthy | INFO |

Overall = highest severity across all products.

---

## Step 6 — JSON output

If `$ARGUMENTS` contains `--json`, output raw aggregated data as JSON instead of the formatted report.
