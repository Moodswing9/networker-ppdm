# Changelog

## [3.4.0] — 2026-11-10
### Changed
- AI features move to the current Claude models: **Claude Opus 5.5** (`claude-opus-5-5`) for `backupctl ask`, `backupctl generate`, `/networker-ask`, `/dr-orchestrate`, `/dr-plan` and the two subagents, and **Claude Haiku 5.5** (`claude-haiku-5-5`) for `/anomaly-report` and the skill validation runner
- Effort is set on every call, because Opus 5.5 always thinks and its default effort (`medium`) differs from before. Calls that already thought adaptively on Opus 4.7 keep `high`, the DR validator (which did not think) uses `low`, and the Haiku calls keep thinking off, so cost and speed stay in line with before while the per-token price drops (Opus $5/$25 → $4/$20, Haiku $1/$5 → $0.10/$0.50 per million tokens)
- `max_tokens` raised where thinking now shares the limit with the answer (Q&A 1024 → 8000, generation and DR agents 2048–4096 → 16000)
- Opus requests opt into server-side refusal fallback (`fallbacks: "default"`); a request that Claude and the fallback both decline raises a clear `ClaudeRefusal` error, and a declined anomaly classification is reported as UNKNOWN
- `anthropic` requirement → `>=2.7` (API version `2026-10-21`)

### Fixed
- The skill validation runner read `content[0].text`, which breaks when a response starts with a thinking block; it now joins the text blocks

### Added
- `orchestrator/claude_models.py`: model IDs and request settings shared by every AI feature
- Unit tests for the shared settings and the DR planner's endpoint and fallback (82 unit tests in total)

## [3.3.3] — 2026-11-10
### Fixed
- `/dr-plan` (`scripts/dr_plan.py`) failed on every run: it requested `thinking: {type: "enabled", budget_tokens: 8000}`, which Claude Opus 4.7 rejects with HTTP 400 ("thinking.type.enabled is not supported for this model"). It now uses adaptive thinking with `output_config.effort: "high"` and `max_tokens` 16000
- `dr_plan_thinking.md` would have been empty even with a working request, because Opus 4.7 omits thinking text unless asked; the request now sets `display: "summarized"`. Docs no longer promise the "full extended thinking chain": current Claude models return a summary of their reasoning, never the raw chain
- `dr_plan.py` writes the sidecar as UTF-8, joins every text block of the plan, and warns when the output hits `max_tokens`
- CLAUDE.md showed `dr_plan.py --incident`, a flag the script does not have; it now shows `--rpo` / `--rto`

### Added
- Unit tests for the `dr_plan` request (adaptive thinking, effort, summarized display, sidecar content); 71 unit tests in total

## [3.3.2] — 2026-10-14
### Fixed
- `backupctl ask` and the skill validation runner (`tests/run_tests.py`) looked for `SKILL.md` in the repo root, which has been empty since the skill moved to `skills/networker-ppdm/` in the plugin packaging. `ask` failed with `FileNotFoundError` unless `--skill` was passed, and the runner exited before running a test. Both now default to `skills/networker-ppdm/SKILL.md`, resolved from the package, so they work from any directory
- `backupctl ask` and `generate` said "openai package required" when the missing package was `anthropic`; the message now names the package that is actually missing
- README test counts: 69 unit tests, 110 skill validation cases

### Added
- Unit tests for the default skill path (CLI, RAG pipeline, chunker, runner)

## [3.3.1] — 2026-10-12
### Fixed
- Claude Code plugin manifest passes `claude plugin validate`: `repository` is a URL, `license` is MIT and the unsupported `components` field is gone; the invalid `commands` map was removed; all 13 commands and both agents load from their default folders
- Install docs: the plugin is now installed from the Moodswing9 marketplace (`claude plugin marketplace add Moodswing9/claude-plugins`, then `claude plugin install networker-ppdm@moodswing9`). The previously documented `npx skills add` installs only the skill, not the slash commands

### Added
- CI validates the plugin manifest on every push and pull request

## [3.3.0] — 2026-07-16
### Added
- `/restore-monitor` — list active and recent PPDM restore sessions, check one by ID, or cancel a running restore (asks for CONFIRM). 13 slash commands in total
- `RestoresMixin`: `list_restores()` and `cancel_restore()`

## [3.2.0] — 2026-07-10
### Added
- `/nw-restore` — guided NetWorker saveset restore wizard: client and saveset browser, original or alternate target (original requires CONFIRM), summary, then recovery via the NetWorker REST API. Supports `--client` and `--dry-run`. 12 slash commands in total

## [3.1.0] — 2026-07-01
### Added
- `/backup-report` — cross-platform executive summary across PPDM, NetWorker and Data Domain: job counts, SLA %, saveset success rate, capacity, overall status and prioritised action items. Skips unconfigured products; supports `--hours` and `--json`. 11 slash commands in total

## [3.0.0] — 2026-06-26
### Added
- `/ppdm-restore` — guided PPDM restore wizard: asset discovery, copy browser, target selection and configuration (Kubernetes, VMware, SQL), summary, CONFIRM for in-place restores, and live monitoring. Supports `--asset`, `--type` and `--dry-run`. 10 slash commands in total

## [2.9.0] — 2026-06-18
### Added
- `backup-health-monitor` agent — full environment sweep (PPDM failed jobs and SLA, NetWorker failures, Data Domain capacity, anomaly pass) producing a daily digest with severity-ranked action items. 2 agents in total

## [2.8.0] — 2026-06-18
### Added
- `/networker-report` — weekly NetWorker summary: saveset success rates, failed savesets, top clients by volume, policy compliance and recommendations. Supports `--days`, `--client` and `--json`. 9 slash commands in total

## [2.7.0] — 2026-06-18
### Added
- `/dr-orchestrate` — four Claude Opus 4.7 agents (monitor, diagnose, remediate, validate) produce a DR response with a confidence score and Go/No-Go verdict
- `/dr-plan` — DR plan from live PPDM topology using extended thinking; the reasoning chain is exported to `dr_plan_thinking.md` for audit
- `/anomaly-report` — classifies up to 500 activities as NORMAL, ANOMALOUS or DEGRADING via the Claude Batch API, with risk scores and `--batch-id` resume

## [2.6.0] — 2026-05-25
### Added
- `backupctl sla` command — per-policy SLA % over a configurable rolling window (`--hours`, `--format json|table`)
- 5 unit tests for `orchestrator.sla` covering counts, percentages, fallback policy name resolution, empty result, and missing host

## [2.5.0] — 2026-05-23
### Added
- GitHub Actions CI — pytest on Python 3.11 and 3.12, triggers on push/PR to main
- `TestPPDMAuth401Retry` — 3 tests covering 401 → re-auth → retry flow
- `TestPPDMPaginationEdgeCases` — 3 tests covering missing page key, empty page object, zero total pages

### Changed
- RAG cache invalidation now mtime-based: rebuilds index automatically when `SKILL.md` is newer than `.rag_index.json`
- `pyproject.toml` version aligned to portfolio badge

## [2.4.0] — 2026-05-12
### Added
- Automatic retry with exponential backoff in `PPDMClient` and `NWClient`: retries HTTP 429, 500, 502, 503, 504 and transient connection errors up to 3 times (1 s → 2 s → 4 s plus jitter); other 4xx responses fail immediately

## [2.3.0] — 2026-04-26
### Changed
- Packaged as a Claude Code plugin: `networker-ppdm` skill, `/ppdm-doctor`, `/ppdm-failed-jobs`, `/ppdm-sla`, `/ppdm-backup` and the `backup-engineer` agent
- **Breaking:** `SKILL.md` moved to `skills/networker-ppdm/SKILL.md`; install with `/plugin install Moodswing9/networker-ppdm` instead of `npx skills add`

## [2.2.0] — 2026-04-23
### Added
- `backupctl ask` — plain-English Q&A grounded in `SKILL.md` via a RAG pipeline (NemoRetriever embeddings, Nemotron-70B answers, local index cached in `.rag_index.json`)
- `backupctl generate` — script generation with Qwen2.5-Coder-32B via NVIDIA NIM
- `rag/` modules and `orchestrator/generate.py`; requires `NVIDIA_API_KEY` and `openai>=1.0`

## [2.1.0] — 2026-04-22
### Added
- Providers layer (`providers/`): `PPDMProvider`, `NetworkerProvider`, `DataDomainProvider` with a common `healthcheck()` contract and `ProviderError`
- `backupctl` CLI (Typer + Rich): `doctor`, `inventory`, `protect`, `dd status`, with JSON output
- 9 orchestrator and provider unit tests (51 in total)

## [2.0.0] — 2026-04-22
### Added
- Python REST clients with context-manager login/logout and `from_env()`: `PPDMClient` (mixin-based, automatic pagination), `NWClient`, `DDClient`
- Automation scripts: `check_failed_jobs.py` (exits 1 on failures), `sla_report.py`, `ondemand_backup.py` (optional `--wait`)
- 43 mocked unit tests across the three clients

## [1.0.2] — 2026-04-11
### Fixed
- Skill test runner: `SKILL.md` sent with prompt caching to stay under the tokens-per-minute limit; longer retry delay, an extra attempt and request pacing; token usage summary in results

## [1.0.1] — 2026-04-11
### Fixed
- Skill test runner: UTF-8 output on Windows; `MAX_TOKENS` 1024 → 2048 to stop truncated answers failing assertions

## [1.0.0] — 2026-04-11
### Added
- `networker-ppdm` Claude Code skill: domain knowledge for PPDM (REST API, RBAC, LDAP, database, VMware, Kubernetes and NAS protection, replication, cloud tier), NetWorker (CLI, REST API, policies, cloning, NDMP, disaster recovery), Data Domain (DDBoost, REST API, VTL, cloud tier, encryption) and CloudBoost
- Skill validation suite: 105 test cases across 44 categories
