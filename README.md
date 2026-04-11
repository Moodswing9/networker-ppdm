# networker-ppdm

A comprehensive Claude Code skill for Dell EMC **NetWorker** and **PowerProtect Data Manager (PPDM)** — covering backup/restore operations, Kubernetes protection, database agents, REST APIs, CLI commands, troubleshooting, and automation.

## What's covered

| Product | Areas |
|---|---|
| **PPDM REST API** | Assets, policies, protection rules, activities, restores, SLA compliance, alerts, credentials, users & RBAC, LDAP/AD, reports, system config, cloud tier, replication, copies management, NAS, VMware, Kubernetes, database protection (Oracle / SQL Server / SAP HANA), vProxy, tags, diagnostics, upgrade |
| **NetWorker REST API + CLI** | Clients, savesets, backup/restore, policy/workflow/actions, clone, storage nodes, devices, volumes, directives, notifications, NDMP, bootstrap/DR, lockbox, client properties, server statistics |
| **Data Domain REST API + CLI** | DDBoost, storage units, VTL, cloud tier, NFS/CIFS shares, encryption at rest, user management, SNMP, syslog, replication, dedup/compression metrics, filesystem maintenance |
| **CloudBoost** | Appliance registration, AWS S3 / Azure Blob cloud profiles, NetWorker device integration |
| **Kubernetes** | Full 10-step PPDM protection guide — CDI, VolumeSnapshot, RBAC, policy, restore, monitoring |

## Install

```bash
npx skills add Moodswing9/networker-ppdm -g
```

## Usage

Once installed, the skill activates automatically in Claude Code when you ask questions about NetWorker, PPDM, Data Domain, or backup/restore operations.

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- `npx` (Node.js)

---

## Test Suite

The `tests/` directory contains a comprehensive test suite that validates every section of the skill.

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
