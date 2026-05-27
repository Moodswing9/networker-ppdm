# CLAUDE.md — networker-ppdm

## What This Is

A Python package providing REST API clients, a unified `backupctl` CLI, automation scripts, a RAG pipeline, and a Claude Code plugin for Dell EMC **NetWorker**, **PowerProtect Data Manager (PPDM)**, and **Data Domain**.

Installed as an editable package (`pip install -e .`). The Claude Code plugin registers 4 slash commands and a domain-expert skill.

## Commands

```bash
# Install
pip install -e .
pip install -r requirements.txt

# Unified CLI (Typer + Rich)
backupctl doctor      # health check across PPDM + NetWorker + Data Domain
backupctl inventory   # list all assets and protection status
backupctl protect     # trigger on-demand protection
backupctl sla         # per-policy SLA % over a rolling window (--hours, --format)

# Or via python -m
python -m orchestrator.cli doctor

# Standalone scripts
python scripts/check_failed_jobs.py
python scripts/ondemand_backup.py
python scripts/sla_report.py

# RAG pipeline (Q&A over SKILL.md)
python -m rag.pipeline "How do I protect a Kubernetes namespace in PPDM?"

# Tests
pytest tests/ -v
```

## Package Structure

```
networker-ppdm/
├── networker/               # NetWorker REST API client
│   ├── client.py            # NWClient base — auth, session, token management
│   ├── policies.py          # Protection policies mixin
│   └── savesets.py          # Saveset query mixin
├── ppdm/                    # PPDM REST API client
│   ├── client.py            # PPDMClient — mixin composition, context manager
│   ├── activities.py        # ActivitiesMixin — jobs, OData filters
│   ├── assets.py            # AssetsMixin — list/filter assets by type
│   ├── policies.py          # PoliciesMixin — protection rules
│   └── restores.py          # RestoresMixin — restore operations
├── orchestrator/            # Unified CLI
│   ├── cli.py               # Typer app — command definitions
│   ├── doctor.py            # Health check logic
│   ├── inventory.py         # Asset inventory
│   ├── protect.py           # On-demand protection
│   └── generate.py          # AI script generator (Claude Opus 4.7)
├── rag/                     # RAG pipeline
│   ├── pipeline.py          # RagPipeline — build index, retrieve, answer
│   ├── chunker.py           # Load + chunk SKILL.md into passages
│   ├── embedder.py          # NVIDIA NIM NemoRetriever embeddings (nvidia/llama-3.2-nemoretriever-300m-embed-v1)
│   └── retriever.py         # VectorStore — in-memory cosine similarity
├── providers/
│   └── datadomain.py        # Data Domain provider (REST)
├── scripts/                 # Standalone automation scripts
├── agents/
│   └── backup-engineer.md   # Agent prompt for autonomous backup ops
├── commands/                # Claude Code slash commands
│   ├── ppdm-backup.md       # /ppdm-backup
│   ├── ppdm-doctor.md       # /ppdm-doctor
│   ├── ppdm-failed-jobs.md  # /ppdm-failed-jobs
│   └── ppdm-sla.md          # /ppdm-sla
├── skills/
│   └── networker-ppdm/
│       └── SKILL.md         # Domain-expert skill definition
├── .claude-plugin/
│   └── plugin.json          # Claude Code plugin manifest
└── tests/                   # pytest suite
```

## API Clients

### PPDMClient

Context-manager-safe. Base URL: `https://<host>:8443/api/v2`.

```python
from ppdm import PPDMClient

with PPDMClient("ppdm.example.com", "admin", "Password1!") as ppdm:
    assets  = ppdm.list_assets(asset_type="KUBERNETES")
    failed  = ppdm.list_activities(state="FAILED")
    restores = ppdm.list_restores()
```

Mixins: `AssetsMixin`, `ActivitiesMixin`, `PoliciesMixin`, `RestoresMixin` — composed into `PPDMClient`.

Activity filters use OData syntax: `state eq "FAILED" and classType eq "JOB"`.

### NWClient (NetWorker)

NetWorker REST API v2 (`https://<host>:9090/nwrestapi/v3`). Similar mixin pattern.

## RAG Pipeline

Chunks `skills/networker-ppdm/SKILL.md` into passages → embeds with NVIDIA NIM (`nvidia/llama-3.2-nemoretriever-300m-embed-v1`) → stores in in-memory `VectorStore` → retrieves top-K on query → answers with **Claude Opus 4.7** (adaptive thinking).

Cache saved to `.rag_index.json` — auto-invalidated when `SKILL.md` is modified (mtime check).

```bash
NVIDIA_API_KEY=nvapi-...
python -m rag.pipeline "What CLI command lists failed NetWorker savesets?"
```

## Claude Code Plugin

Install globally:
```bash
npx skills add Moodswing9/networker-ppdm -g
```

Slash commands:
| Command | What it does |
|---|---|
| `/ppdm-backup` | Trigger on-demand PPDM protection job |
| `/ppdm-doctor` | Run health check and surface critical issues |
| `/ppdm-failed-jobs` | List and summarise failed jobs in the last 24 h |
| `/ppdm-sla` | Generate SLA compliance report |

## Key Constraints

- `PPDMClient` must be used as a context manager or `.close()` called explicitly — the requests session holds an auth token
- PPDM API returns paginated results; `list_*` methods handle `?pageSize=100` but do not auto-paginate beyond that
- NetWorker REST API is on port 9090, not 8443 — don't mix them up
- RAG index is in-memory and rebuilt on each process start unless `.rag_index.json` cache exists
- `pip install -e .` required for `backupctl` CLI entry point to resolve
- Tests mock HTTP — run `pytest tests/ -v`, no live PPDM needed

## Environment Variables

| Variable | Required for |
|---|---|
| `PPDM_HOST` | scripts, orchestrator commands |
| `PPDM_USER` / `PPDM_PASS` | scripts, orchestrator commands |
| `NW_HOST` / `NW_USER` / `NW_PASS` | NetWorker client |
| `NVIDIA_API_KEY` | RAG embedder (NIM NemoRetriever — embeddings only) |
| `ANTHROPIC_API_KEY` | RAG LLM (Claude Opus 4.7) + script generator |
