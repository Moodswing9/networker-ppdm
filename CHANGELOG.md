# Changelog

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

## [2.0.0] — 2026-04-01
### Added
- Claude Code plugin (`plugin.json`) with 4 slash commands: `/ppdm-backup`, `/ppdm-doctor`, `/ppdm-failed-jobs`, `/ppdm-sla`
- `backup-engineer.md` autonomous agent for hands-free backup operations
- `skills/networker-ppdm/SKILL.md` — domain knowledge base (NetWorker, PPDM, Data Domain, DDBoost, VTL, cloud tier)

## [1.0.0] — 2026-03-01
### Added
- `PPDMClient` with mixin composition (`ActivitiesMixin`, `AssetsMixin`, `PoliciesMixin`, `RestoresMixin`)
- `NWClient` for NetWorker REST API v2 (savesets, policies, protection groups)
- `DDClient` for Data Domain REST (DDBoost, storage units)
- `backupctl` unified CLI: `doctor`, `inventory`, `protect`
- `backupctl ask` — plain-English Q&A via NVIDIA NIM RAG pipeline (NemoRetriever embeddings + Nemotron 70B)
- `backupctl generate` — automation script generation via Qwen2.5-Coder-32B
- pytest suite: 59 unit tests, all HTTP-mocked via `responses` library
