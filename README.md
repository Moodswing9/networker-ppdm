# networker-ppdm

Python REST API clients, automation scripts, and a Claude Code skill for Dell EMC **NetWorker**, **PowerProtect Data Manager (PPDM)**, and **Data Domain** — covering backup/restore operations, Kubernetes protection, DDBoost, database agents, SLA reporting, and automation.

---

## Python Library

Install and import the clients directly in your scripts:

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your host/user/pass
```

### PPDMClient

```python
from ppdm import PPDMClient

with PPDMClient.from_env() as ppdm:
    # List all failed Kubernetes backup jobs
    for job in ppdm.failed_activities(asset_type="KUBERNETES"):
        print(job["name"], job["startTime"])

    # Trigger on-demand backup and get the activity ID
    policy = ppdm.get_policy_by_name("k8s-daily")
    result = ppdm.trigger_backup(policy["id"])

    # Restore a namespace to a new location
    copy = ppdm.latest_copy(asset_id)
    ppdm.restore_kubernetes_to_new_namespace(
        copy["id"], target_namespace="ns-restored", target_cluster_id="..."
    )
```

**Available methods:** `list_assets`, `get_asset`, `list_copies`, `latest_copy`, `list_activities`, `failed_activities`, `running_activities`, `cancel_activity`, `list_policies`, `get_policy_by_name`, `create_policy`, `assign_assets`, `trigger_backup`, `create_protection_rule`, `list_inventory_sources`, `discover_inventory_source`, `list_storage_systems`, `restore`, `restore_kubernetes_to_new_namespace`

### NWClient

```python
from networker import NWClient

with NWClient.from_env() as nw:
    savesets = nw.list_savesets_for_client("web01.example.com")
    latest   = nw.latest_full_backup("web01.example.com")
    nw.trigger_group_backup("Linux-Clients")
```

**Available methods:** `list_clients`, `get_client`, `list_savesets`, `list_savesets_for_client`, `latest_full_backup`, `list_policies`, `list_workflows`, `list_protection_groups`, `trigger_group_backup`, `start_recover`

### DDClient

```python
from datadomain import DDClient

with DDClient.from_env() as dd:
    dd.enable_ddboost()
    dd.create_storage_unit("ppdm-su-01", "ddboost-user", soft_limit_tib=10.0)
    print(dd.filesystem_stats())
```

**Available methods:** `ddboost_status`, `enable_ddboost`, `disable_ddboost`, `list_storage_units`, `create_storage_unit`, `assign_user_to_storage_unit`, `system_info`, `filesystem_stats`, `list_users`, `create_user`

---

## Automation Scripts

Ready-to-run scripts — require `.env` with credentials set.

```bash
# Report all failed backup activities (exit 1 if failures found — CI-friendly)
python scripts/check_failed_jobs.py
python scripts/check_failed_jobs.py --asset-type KUBERNETES
python scripts/check_failed_jobs.py --json

# SLA compliance report
python scripts/sla_report.py
python scripts/sla_report.py --non-compliant-only

# Trigger on-demand backup (optionally poll until completion)
python scripts/ondemand_backup.py --asset "prod-namespace" --policy "k8s-daily"
python scripts/ondemand_backup.py --asset "prod-namespace" --policy "k8s-daily" --wait
```


---

## Unified CLI

A new thin orchestration layer, `backupctl`, sits on top of the existing PPDM, NetWorker, and Data Domain clients and gives you one operator-friendly entry point for health checks, inventory, and backup triggers.

```bash
pip install -e .
backupctl doctor
backupctl inventory --format json
backupctl protect ppdm --target k8s-daily
backupctl protect networker --target Linux-Clients
backupctl dd status
```

### Initial commands

- `backupctl doctor` — cross-platform health check for PPDM, NetWorker, and Data Domain
- `backupctl inventory` — combined PPDM + NetWorker inventory output
- `backupctl protect` — trigger a PPDM policy backup or NetWorker protection group backup
- `backupctl dd status` — inspect Data Domain status and filesystem details

## Claude Code Skill

Install the skill globally to get expert NetWorker / PPDM guidance inline in Claude Code:

```bash
npx skills add Moodswing9/networker-ppdm -g
```

Once installed, the skill activates automatically when you ask questions about NetWorker, PPDM, Data Domain, or backup/restore operations.

**Requirements:** [Claude Code](https://claude.ai/code) CLI, `npx` (Node.js)

### What the skill covers

| Product | Areas |
|---|---|
| **PPDM REST API** | Assets, policies, protection rules, activities, restores, SLA compliance, alerts, credentials, users & RBAC, LDAP/AD, reports, system config, cloud tier, replication, copies management, NAS, VMware, Kubernetes, database protection (Oracle / SQL Server / SAP HANA), vProxy, tags, diagnostics, upgrade |
| **NetWorker REST API + CLI** | Clients, savesets, backup/restore, policy/workflow/actions, clone, storage nodes, devices, volumes, directives, notifications, NDMP, bootstrap/DR, lockbox, client properties, server statistics |
| **Data Domain REST API + CLI** | DDBoost, storage units, VTL, cloud tier, NFS/CIFS shares, encryption at rest, user management, SNMP, syslog, replication, dedup/compression metrics, filesystem maintenance |
| **CloudBoost** | Appliance registration, AWS S3 / Azure Blob cloud profiles, NetWorker device integration |
| **Kubernetes** | Full 10-step PPDM protection guide — CDI, VolumeSnapshot, RBAC, policy, restore, monitoring |

---

## Tests

Two test suites — one for the Python library, one for the Claude Code skill.

### Unit Tests (Python library)

```bash
pip install -e ".[dev]"
python -m pytest tests/unit/          # 43 tests, fully mocked — no real servers needed
```

### Skill Validation Tests

The `tests/` directory validates every section of `SKILL.md` by sending prompts to Claude and asserting the responses contain the expected endpoints, commands, and terminology.

### What's tested

| Category | # Tests | Coverage |
|---|---|---|
| PPDM Core | 5 | Auth, assets, activities, restores, Python/PowerShell snippets |
| PPDM Policies | 2 | Create policy, protection rules |
| PPDM Credentials | 1 | CRUD + connectivity test |
| PPDM SLA | 2 | Compliance, custom SLA creation |
| PPDM Alerts | 3 | List/acknowledge, SMTP config, audit logs |
| PPDM System | 1 | Component health, certificates, license |
| PPDM RBAC | 3 | Create user, list roles, session management |
| PPDM LDAP | 2 | Configure provider, test connection, group mappings |
| PPDM App Host | 2 | Register host, agent type reference |
| PPDM Database | 5 | Oracle (policy + PIT restore), SQL Server (policy + restore), SAP HANA |
| PPDM Replication | 2 | 3-stage policy, remote PPDM registration |
| PPDM Cloud Tier | 3 | AWS S3, Azure Blob, data recall |
| PPDM Copies | 3 | Retention lock, legal hold, bulk delete |
| PPDM NAS | 3 | Isilon, NetApp, granular file restore |
| PPDM VMware | 2 | vCenter registration, instant access restore |
| PPDM Reports | 2 | Run report, schedule recurring report |
| PPDM System Config | 4 | DNS/NTP, proxy, 2FA/TOTP, token management |
| PPDM Diagnostics | 2 | Log bundle, upgrade procedure |
| PPDM Tags & vProxy | 2 | Asset tags + protection rules, vProxy deploy/tune |
| PPDM DDBoost | 1 | Register DD with DDBoost via PPDM REST |
| Kubernetes | 7 | Prerequisites, VolumeSnapshotClass, RBAC, register, policy, restore, troubleshoot |
| NetWorker Core | 4 | mminfo, nsradmin, recover CLI, REST API |
| NetWorker Policy | 3 | Hierarchy explanation, create workflow+actions, on-demand run |
| NetWorker Clone | 2 | REST API clone, CLI nsrclone |
| NetWorker Directives | 2 | Create directive, email notification |
| NetWorker Storage | 3 | Storage node, device CRUD, volume management |
| NetWorker Client | 3 | Encryption/parallelism, lockbox, server stats |
| NetWorker NDMP | 2 | NDMP config (NetApp), bootstrap DR procedure |
| DDBoost | 4 | Enable service, create storage unit, NW device, port reference |
| Data Domain | 4 | Auth, filesystem stats, replication, filesystem clean |
| DD VTL | 3 | Create library, access groups, add tapes |
| DD Cloud Tier | 3 | AWS profile, enable on SU, data recall |
| DD Encryption | 2 | Enable + KMIP, key rotation |
| DD Users | 1 | Role table, create/disable user |
| DD SNMP | 1 | SNMPv3 configuration |
| DD Syslog | 1 | Add syslog destination to SIEM |
| DD NFS | 1 | Create NFS export |
| DD CIFS | 1 | Enable CIFS, create share |
| DD Dedup Metrics | 2 | Global stats, per-storage-unit stats |
| CloudBoost | 3 | Register appliance, AWS S3 profile, Azure profile |
| Cross-Product | 2 | NW vs PPDM comparison, port/auth summary |
| Troubleshooting | 3 | PPDM agent, NetWorker backup failure, DD storage full |
| Best Practices | 2 | General, Kubernetes |

**Total: 105 test cases across 44 categories**

### Run the tests

```bash
# Install dependencies
pip install -r tests/requirements.txt

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run all tests
python tests/run_tests.py

# Run a specific category
python tests/run_tests.py --category "Kubernetes"
python tests/run_tests.py --category "PPDM Database"
python tests/run_tests.py --category "DD VTL"

# Run a single test by ID
python tests/run_tests.py --id k8s_policy
python tests/run_tests.py --id dd_ddboost_enable
python tests/run_tests.py --id ppdm_oracle_policy

# Stop on first failure
python tests/run_tests.py --fail-fast

# Show full Claude responses
python tests/run_tests.py --verbose

# Save results to JSON
python tests/run_tests.py --output results.json
```

### Sample output

```
networker-ppdm skill test runner
Model  : claude-haiku-4-5-20251001
Skill  : SKILL.md
Tests  : tests/test_cases.yaml
Running: 105 test(s)

PPDM Core
  ✓ [ppdm_auth] How do I authenticate to the PPDM REST API...
  ✓ [ppdm_list_assets] Show me the PPDM REST API call to list all assets...
  ✓ [ppdm_list_activities] How do I retrieve all failed backup activities...

Kubernetes
  ✓ [k8s_prerequisites] What are the prerequisites before registering a Kubernetes...
  ✗ [k8s_policy] How do I create a Kubernetes protection policy...
      Missing assertions: ['CRASH_CONSISTENT']

────────────────────────────────────────────────────────────
RESULTS
────────────────────────────────────────────────────────────
  Total  : 105
  Passed : 104
  Failed : 1
  Score  : 99.0%
  Time   : 127.4s
```

### How it works

1. Loads `SKILL.md` as the Claude system prompt
2. For each test case, sends the prompt to `claude-haiku-4-5-20251001` (fast + cost-effective)
3. Validates the response contains all required **assertions** (case-insensitive substring match)
4. Checks no **negative assertions** appear (e.g. "I don't know")
5. Reports per-test and per-category pass/fail with colour output

### Adding tests

Edit `tests/test_cases.yaml` and add an entry:

```yaml
- id: my_new_test
  category: PPDM Core
  section: PPDM REST API
  prompt: "How do I do X in PPDM?"
  assertions:
    - "keyword1"
    - "endpoint/path"
    - "relevant-term"
```

## License

MIT
