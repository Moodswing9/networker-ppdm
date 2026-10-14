<div align="center">

# 🛡️ NetWorker / PPDM

**Python REST API clients, unified CLI, automation scripts, and a Claude Code skill for Dell EMC NetWorker, PowerProtect Data Manager, and Data Domain**

[![Version](https://img.shields.io/badge/version-3.3.2-6366f1?style=flat-square)](https://github.com/Moodswing9/networker-ppdm/releases)
[![License](https://img.shields.io/badge/license-MIT-22c55e?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/Moodswing9/networker-ppdm/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/Moodswing9/networker-ppdm/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-3b82f6?style=flat-square)](#)
[![Tests](https://img.shields.io/badge/tests-105%20cases-22c55e?style=flat-square)](#tests)
[![Claude Code Plugin](https://img.shields.io/badge/claude%20code-plugin-f59e0b?style=flat-square)](#claude-code-plugin)
[![Claude AI](https://img.shields.io/badge/AI-Claude%20Opus%204.7-f59e0b?style=flat-square)](#ai-features)

</div>

---

## Overview

A complete automation and expert-guidance toolkit for Dell EMC backup infrastructure. Covers backup/restore operations, Kubernetes protection, DDBoost, database agents, SLA reporting, and cloud tier management across **PPDM**, **NetWorker**, and **Data Domain**.

---

## Python Library

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your host / user / pass
```

Both clients implement **automatic retry with exponential backoff** — transient failures (HTTP 429, 500, 502, 503, 504, connection errors) are retried up to 3 times with randomised jitter before raising. Non-retryable responses (4xx) surface immediately.

### PPDMClient

```python
from ppdm import PPDMClient

with PPDMClient.from_env() as ppdm:
    # List all failed Kubernetes backup jobs
    for job in ppdm.failed_activities(asset_type="KUBERNETES"):
        print(job["name"], job["startTime"])

    # Trigger on-demand backup
    policy = ppdm.get_policy_by_name("k8s-daily")
    result = ppdm.trigger_backup(policy["id"])

    # Restore a namespace to a new location
    copy = ppdm.latest_copy(asset_id)
    ppdm.restore_kubernetes_to_new_namespace(
        copy["id"], target_namespace="ns-restored", target_cluster_id="..."
    )
```

**Available methods:** `list_assets` · `get_asset` · `list_copies` · `latest_copy` · `list_activities` · `failed_activities` · `running_activities` · `cancel_activity` · `list_policies` · `get_policy_by_name` · `create_policy` · `assign_assets` · `trigger_backup` · `create_protection_rule` · `list_inventory_sources` · `discover_inventory_source` · `list_storage_systems` · `restore` · `restore_kubernetes_to_new_namespace`

### NWClient

```python
from networker import NWClient

with NWClient.from_env() as nw:
    savesets = nw.list_savesets_for_client("web01.example.com")
    latest   = nw.latest_full_backup("web01.example.com")
    nw.trigger_group_backup("Linux-Clients")
```

**Available methods:** `list_clients` · `get_client` · `list_savesets` · `list_savesets_for_client` · `latest_full_backup` · `list_policies` · `list_workflows` · `list_protection_groups` · `trigger_group_backup` · `start_recover`

### DDClient

```python
from datadomain import DDClient

with DDClient.from_env() as dd:
    dd.enable_ddboost()
    dd.create_storage_unit("ppdm-su-01", "ddboost-user", soft_limit_tib=10.0)
    print(dd.filesystem_stats())
```

**Available methods:** `ddboost_status` · `enable_ddboost` · `disable_ddboost` · `list_storage_units` · `create_storage_unit` · `assign_user_to_storage_unit` · `system_info` · `filesystem_stats` · `list_users` · `create_user`

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

`backupctl` is a single operator-friendly entry point across PPDM, NetWorker, and Data Domain.

```bash
pip install -e .
backupctl doctor
backupctl inventory --format json
backupctl protect ppdm --target k8s-daily
backupctl protect networker --target Linux-Clients
backupctl dd status

# AI commands — require ANTHROPIC_API_KEY
backupctl ask "How do I restore a Kubernetes namespace from a PPDM copy?"
backupctl generate "Python script that lists all PPDM policies older than 30 days"
```

| Command | Description |
|:---|:---|
| `backupctl doctor` | Cross-platform health check for PPDM, NetWorker, and Data Domain |
| `backupctl inventory` | Combined PPDM + NetWorker inventory output |
| `backupctl protect` | Trigger a PPDM policy or NetWorker protection group backup |
| `backupctl dd status` | Inspect Data Domain status and filesystem details |
| `backupctl ask` | Plain-English Q&A over SKILL.md — RAG-powered, answered by Claude Opus 4.7 |
| `backupctl generate` | Generate NetWorker/PPDM automation scripts with Claude Opus 4.7 |

---

## AI Features

Powered by **Claude Opus 4.7** (adaptive thinking) for Q&A and script generation. Embeddings use NVIDIA NIM NemoRetriever for vector search.

### `backupctl ask` — RAG over SKILL.md

Asks NetWorker/PPDM questions in plain English. The pipeline:

1. **Chunks** SKILL.md by H2 heading (`rag/chunker.py`)
2. **Embeds** each chunk with `nvidia/llama-3.2-nemoretriever-300m-embed-v1` (`rag/embedder.py`)
3. **Stores** vectors in an in-memory cosine-similarity index, cached as `.rag_index.json` (`rag/retriever.py`)
4. **Retrieves** the top-K chunks for the user's question, then asks `claude-opus-4-7` (adaptive thinking) to answer using only that context (`rag/pipeline.py`)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export NVIDIA_API_KEY=nvapi-...   # required for embeddings only
backupctl ask "What's the safest way to cancel a stuck PPDM activity?"
backupctl ask "Show me the REST call to list failed Kubernetes jobs" --top-k 8
backupctl ask "..." --rebuild   # force rebuild of vector index
```

### `backupctl generate` — Domain-Aware Script Generation

Generates production-ready Python or bash scripts targeting the NetWorker/PPDM REST APIs. Uses **`claude-opus-4-7`** (adaptive thinking) with a system prompt that constrains output to clean, error-handled, log-aware code (`orchestrator/generate.py`).

```bash
backupctl generate "Bash script that nightly reports DD storage units over 80% full"
backupctl generate "Python script that triggers PPDM backups for all K8s namespaces" -o backup_all_ns.py
```

> **Requirements for AI features:** `pip install anthropic>=0.40` and `ANTHROPIC_API_KEY` set in the environment. `NVIDIA_API_KEY` is still required for the NemoRetriever embedding step in `backupctl ask`.

---

## Claude Code Plugin

Install as a plugin to get the skill, 13 slash commands and 2 agents inline in Claude Code:

From a terminal:

```bash
claude plugin marketplace add Moodswing9/claude-plugins
claude plugin install networker-ppdm@moodswing9
```

This installs the skill, all 13 slash commands and both agents.

Or inside Claude Code: `/plugin marketplace add Moodswing9/claude-plugins`, then `/plugin install networker-ppdm@moodswing9`.

Only need the knowledge skill, without the slash commands? `npx skills add Moodswing9/networker-ppdm -g` installs just the skill.

Once installed, you get:

| Component | What it does |
|:---|:---|
| **`networker-ppdm` skill** | Auto-activates when you ask about NetWorker, PPDM, Data Domain, or backup/restore operations. |
| **`/networker-ask`** | Ask any NetWorker/PPDM question — answered by Claude Opus 4.7 using the domain knowledge base. |

**Health and reporting**

| Command | What it does |
|:---|:---|
| **`/ppdm-doctor`** | Cross-product health check across PPDM, NetWorker and Data Domain, drilling into failures automatically. |
| **`/ppdm-failed-jobs`** | Lists failed PPDM activities with root-cause hints. CI-friendly exit code. |
| **`/ppdm-sla`** | SLA compliance report — surfaces non-compliant assets with their recent job history. |
| **`/networker-report`** | Weekly NetWorker summary — saveset success rates, failed clients, data volume and policy compliance. |
| **`/backup-report`** | Cross-platform executive report combining PPDM, NetWorker and Data Domain, with prioritised action items. |
| **`/anomaly-report`** | Flags anomalous, degrading and failed jobs over a history window using the Claude Batch API. |

**Backup and restore**

| Command | What it does |
|:---|:---|
| **`/ppdm-backup`** | Trigger an on-demand PPDM backup, validating the asset and policy first, optionally polling until completion. |
| **`/ppdm-restore`** | Guided PPDM restore wizard — pick an asset, a recovery copy and a target, confirm, and watch it run. |
| **`/nw-restore`** | Guided NetWorker saveset restore wizard — pick a client, a saveset and a target path, confirm, and trigger. |
| **`/restore-monitor`** | List active and recent PPDM restore sessions, check one by ID, or cancel a running restore. |

**Disaster recovery**

| Command | What it does |
|:---|:---|
| **`/dr-orchestrate`** | Four specialist Claude agents triage, diagnose, remediate and validate a DR response, ending in a Go/No-Go verdict. |
| **`/dr-plan`** | Full DR plan from your live PPDM topology using Claude Opus 4.7 extended thinking, with the reasoning exported for audit. |

**Agents**

| Agent | What it does |
|:---|:---|
| **`backup-engineer`** | Senior-level deep-dive agent for complex multi-product troubleshooting. Use via the Agent tool with `subagent_type: "backup-engineer"`. |
| **`backup-health-monitor`** | Runs a full environment sweep and produces a daily digest with severity-ranked action items. |

The restore wizards ask for explicit confirmation before restoring to the original location, and `/restore-monitor` asks before canceling a restore.

> **Requirements:** [Claude Code](https://claude.com/claude-code) 1.0.33+. Python 3.10+ on the machine running the slash commands (for the underlying scripts).

### Coverage

| Product | Areas |
|:---|:---|
| **PPDM REST API** | Assets · policies · protection rules · activities · restores · SLA compliance · alerts · credentials · RBAC · LDAP/AD · cloud tier · replication · copies · NAS · VMware · Kubernetes · database agents (Oracle / SQL Server / SAP HANA) · vProxy · diagnostics · upgrade |
| **NetWorker REST API + CLI** | Clients · savesets · backup/restore · policy/workflow/actions · clone · storage nodes · devices · volumes · directives · notifications · NDMP · bootstrap/DR · lockbox |
| **Data Domain REST API + CLI** | DDBoost · storage units · VTL · cloud tier · NFS/CIFS · encryption at rest · replication · dedup metrics · filesystem maintenance |
| **CloudBoost** | Appliance registration · AWS S3 / Azure Blob profiles · NetWorker device integration |
| **Kubernetes** | Full 10-step PPDM protection guide — CDI · VolumeSnapshot · RBAC · policy · restore · monitoring |

---

## Tests

Two suites — one for the Python library, one for the Claude Code skill.

### Unit Tests

```bash
pip install -e ".[dev]"
python -m pytest tests/unit/          # 69 tests, fully mocked
```

### Skill Validation Tests

```bash
pip install -r tests/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

python tests/run_tests.py                          # all 110 tests
python tests/run_tests.py --category "Kubernetes"
python tests/run_tests.py --id ppdm_oracle_policy
python tests/run_tests.py --fail-fast
python tests/run_tests.py --verbose
python tests/run_tests.py --output results.json
```

### Test Coverage — 105 cases across 44 categories

| Area | Tests |
|:---|:---:|
| PPDM Core · Policies · Credentials · SLA · Alerts · System · RBAC · LDAP · App Host | 19 |
| PPDM Database (Oracle · SQL Server · SAP HANA) | 5 |
| PPDM Replication · Cloud Tier · Copies · NAS · VMware · Reports · Config · Diagnostics | 18 |
| PPDM Tags · vProxy · DDBoost | 4 |
| Kubernetes | 7 |
| NetWorker Core · Policy · Clone · Directives · Storage · Client · NDMP | 19 |
| DDBoost · Data Domain · VTL · Cloud Tier · Encryption · Users · SNMP · Syslog · NFS · CIFS · Dedup | 20 |
| CloudBoost · Cross-Product · Troubleshooting · Best Practices | 10 |
| **Total** | **105** |

### Sample output

```
networker-ppdm skill test runner
Model  : claude-haiku-4-5-20251001
Tests  : 105

  ✓ [ppdm_auth]         How do I authenticate to the PPDM REST API...
  ✓ [ppdm_list_assets]  Show me the PPDM REST API call to list all assets...
  ✓ [k8s_prerequisites] What are the prerequisites before registering a Kubernetes cluster...

────────────────────────────────────────────────────────────
  Total  : 105  ·  Passed : 104  ·  Failed : 1  ·  Score : 99.0%
────────────────────────────────────────────────────────────
```

### Adding tests

```yaml
# tests/test_cases.yaml
- id: my_new_test
  category: PPDM Core
  prompt: "How do I do X in PPDM?"
  assertions:
    - "keyword1"
    - "endpoint/path"
```

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built by [Moodswing9](https://github.com/Moodswing9) · [Portfolio](https://moodswing9.github.io)

</div>
