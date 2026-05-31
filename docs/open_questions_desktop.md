# Open Questions: Desktop & Packaging

**Status:** current on 2026-05-30.

## Purpose

This document tracks decisions that remain open for the Windows desktop delivery path. It exists so the current D8 handoff can stay honest: local planning is `READY_FOR_STAGING_HANDOFF`, while production desktop packaging is not yet complete.

Open questions here do not block D8 staging evidence. They do block any claim that final-user desktop release packaging is production-ready.

## Decision Register

| Area | Open question | Current default | Close before |
|---|---|---|---|
| Shell | Does Tauri 2 cover sidecar lifecycle, single-instance behavior, installer hooks, and updater needs? | Continue with Tauri 2 | production desktop release |
| Fallback shell | What evidence would justify Electron instead of Tauri? | No fallback unless a recorded blocker appears | installer implementation |
| Installer | Should Windows use MSI, NSIS, WiX, or another packaging format? | undecided | production desktop release |
| Signing | What publisher identity and certificate process will be used? | undecided | any external installer distribution |
| Updates | Which update channel, rollback rule, and delta package policy will be used? | undecided | production desktop release |
| Database runtime | Should PostgreSQL be bundled, service-managed, or installed through an enterprise IT flow? | PostgreSQL + pgvector remains authoritative; packaging path undecided | installer implementation |
| Backup/restore | What local backup, restore, and diagnostic export UX is required? | not implemented | production desktop release |
| Data directory | Where should app data, database files, logs, and diagnostics live on Windows? | undecided | installer implementation |
| Multi-user | Is the default SKU single Windows user, shared workstation, or LAN-accessible deployment? | single-user local-first until decided otherwise | enterprise packaging |
| Local AI | Is any local model bundled, optional, or excluded? | excluded from current packaging scope | AI packaging work |
| Licensing | Which redistribution obligations apply to Tauri/WebView2, PyInstaller, PostgreSQL, pgvector, and bundled runtime assets? | legal review required | external installer distribution |
| Cloud sync | When does `future_cloud` become a real multi-device mode? | not part of D8 staging handoff | future cloud plan |

## Current Non-Decisions

- Do not introduce SQLite, PostgreSQL-lite, or a dual database path without an explicit architecture decision.
- Do not require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL.
- Do not treat local desktop packaging checks as `STAGING_VALIDATED`.
- If local rehearsal output is saved where strict evidence is expected, production coordination remains at `WAITING_FOR_REAL_STAGING_EVIDENCE` until real staging evidence replaces it.
- Do not deploy or modify `service.intelli-opus.com` from packaging work.
- Do not use installer work to trigger email, webhooks, carrier APIs, notifications, feedback creation, or business-record mutation.

## How To Close A Question

Each decision should produce:

- a short written decision in this document or a linked architecture decision record
- affected files and implementation owner
- validation command
- rollback or fallback note
- security and redaction review if credentials, logs, storage, or customer files are involved

## Validation

```powershell
cd backend
python scripts/desktop_packaging_docs_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/d8_staging_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
```

## Related Docs

- [Packaging Strategy](packaging_strategy.md)
- [Desktop Target Architecture](architecture_desktop_target.md)
- [Database Lifecycle](database_lifecycle.md)
- [Runtime Modes](runtime_modes.md)
