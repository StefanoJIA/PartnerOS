# Packaging Strategy

**Status:** current on 2026-05-30.

## Purpose

PartnerOS is still implemented as a Vue + FastAPI + PostgreSQL application, but the target delivery shape remains a Windows desktop application that internal users launch from one app icon. This strategy keeps desktop packaging aligned with the current `READY_FOR_STAGING_HANDOFF` state while avoiding premature production installer commitments.

This document is not a production release runbook, not staging evidence, and not permission to deploy or modify `service.intelli-opus.com`.

## Current Packaging Facts

- Frontend desktop shell work is under `frontend/src-tauri`.
- The desktop shell target is Tauri 2 unless a later architecture decision records a reason to switch.
- The backend sidecar path uses PyInstaller around `sidecar_entry.py` to create an `intellioffice-backend` executable.
- The Tauri app launches the sidecar through the shell plugin and probes `/health`.
- The sidecar default health origin is `http://127.0.0.1:17888/health`.
- Browser-based local development and D7.6+/D8 validation still use port `8014`.
- PostgreSQL + pgvector remains the authoritative store; see [Database Lifecycle](database_lifecycle.md).

## Desktop Delivery Shape

The intended desktop package should eventually provide:

- one Windows installer or signed package
- one intelliOffice launch icon
- a managed backend sidecar
- a managed database lifecycle path
- a local health/diagnostic surface
- redacted logs and diagnostic export for support
- clear upgrade and rollback behavior

Final users should not need separate frontend/backend commands or manual seed scripts.

Do not require final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL.

## Installer Boundary

Installer implementation is not complete in the current D8 handoff. The next packaging decisions remain:

- MSI, NSIS, WiX, or another Windows installer format
- signing certificate and publisher identity
- update channel and rollback policy
- embedded PostgreSQL versus service-managed PostgreSQL versus another approved lifecycle path
- backup/restore UX
- desktop data directory and retention policy
- enterprise IT deployment requirements

These are tracked in [Open Questions: Desktop & Packaging](open_questions_desktop.md). They must be closed through explicit decisions before claiming production desktop release readiness.

## Database Packaging Boundary

Do not replace the PostgreSQL + pgvector architecture with SQLite or an unreviewed dual-path database strategy inside packaging work. Any long-term SQLite, PostgreSQL-lite, or dual-database SKU must go through an explicit architecture decision and database lifecycle update.

The packaging layer may orchestrate database startup, migration, backup, restore, and diagnostics in the future. It must not hide migration failures, silently create unsafe default credentials, or ask final users to operate database tools.

## Safety Boundaries

Packaging work must not:

- commit `.env`, `local_data/`, `backend/storage/`, generated logs, uploads, tokens, or customer files
- call staging unless running an explicit evidence script with private values
- deploy or modify `service.intelli-opus.com`
- edit nginx or cloud upstreams
- send email, webhooks, carrier API calls, customer notifications, or supplier notifications
- automatically change order status to shipped or delivered
- create feedback tickets or mutate business records as part of packaging

## Validation

Use these local checks after changing packaging or desktop decision docs:

```powershell
cd backend
python scripts/desktop_packaging_docs_check.py
python scripts/desktop_target_architecture_check.py
python scripts/database_lifecycle_doc_check.py
python scripts/project_execution_chain_check.py
```

These checks support `READY_FOR_STAGING_HANDOFF`; they do not prove `STAGING_VALIDATED`.

## Related Docs

- [Desktop Target Architecture](architecture_desktop_target.md)
- [Runtime Modes](runtime_modes.md)
- [Database Lifecycle](database_lifecycle.md)
- [Open Questions: Desktop & Packaging](open_questions_desktop.md)
- [D8 Staging Operator Runbook](phase3/d8_staging_operator_runbook.md)
