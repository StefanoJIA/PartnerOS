# Migration From Web Development To Desktop Product

**Status:** current on 2026-05-30.

## Purpose

PartnerOS began as a browser-run Vue + FastAPI + PostgreSQL application. The product target is still a Windows desktop application for internal intelliOffice operations.

This document explains what should be preserved, what should move behind desktop lifecycle management, and what must remain out of scope while the project is in `READY_FOR_STAGING_HANDOFF`.

It is not a staging evidence record, not a production installer runbook, and not permission to deploy or modify `service.intelli-opus.com`.

## Current State

The repository is the authoritative implementation for:

- FastAPI backend routes, services, schemas, and models
- Vue/Vite frontend workflows
- PostgreSQL + pgvector data model and Alembic migrations
- order, production, shipment, portal bridge, resource center, RBAC, operations, and market-response workflows through D8/D9 planning
- Tauri shell and backend sidecar foundation
- database lifecycle health fields and migration checks

The correct project state remains `READY_FOR_STAGING_HANDOFF`. Local desktop and runtime checks do not prove `STAGING_VALIDATED`.

## Preserve

Keep these assets as the desktop product evolves:

- existing business models and Alembic migrations
- FastAPI route contracts except where a desktop boundary requires explicit security or path changes
- Vue operational workflows that are already used by internal operators
- D7 order, production milestone, shipment plan, portal bridge, and resource center boundaries
- D8 RBAC, runtime hardening, partner operations, and market response intelligence
- manual-only safety rules for notifications, supplier/customer contact, carrier APIs, and business status changes
- partner-neutral product and supplier logic

Do not fork a second desktop-only business codebase unless there is a documented architecture decision with a migration and test plan.

## Move Behind Desktop Lifecycle

The following concerns should become product-managed over time:

- launching the backend sidecar
- selecting and probing the backend origin
- database configuration, migration, and health diagnostics
- local logs and redacted diagnostic export
- installer entrypoint, shortcut, signing, and update behavior
- eventual backup/restore UX

Final users should not run separate frontend/backend commands, PostgreSQL, pgAdmin, Docker, Alembic, raw SQL, or seed scripts.

## Do Not Rebuild

Do not rebuild the core business stack just because the delivery shape changes:

- no parallel microservice split for current scale
- no duplicate data model outside Alembic and SQLAlchemy
- no unreviewed SQLite replacement for PostgreSQL + pgvector
- no separate customer portal implementation inside this repository
- no UnionGPT gateway or cloud nginx work from PartnerOS packaging

## Migration Sequence

The practical sequence is:

1. Keep the browser local workflow healthy for development and validation.
2. Keep the Tauri shell and sidecar path aligned with `/health`.
3. Keep the database lifecycle contract current and redacted.
4. Keep the D7.6+/D8 validation default on backend port `8014`.
5. Run strict staging evidence only when real private staging values are supplied.
6. After staging evidence and production coordination, close the desktop packaging decisions in [Packaging Strategy](packaging_strategy.md) and [Open Questions: Desktop & Packaging](open_questions_desktop.md).

Strict staging private values include `BACKEND_BASE_URL`, `SERVICE_PORTAL_PARTNEROS_TOKEN`, and `SERVICE_PORTAL_ORIGIN`; keep them outside the repository.

## Boundaries

The migration path must not:

- call carrier APIs
- send email, webhooks, customer notifications, or supplier notifications
- automatically change order status to shipped or delivered
- create feedback tickets outside the D7.7+ bridge rules
- expose internal cost, margin, pricing breakdowns, supplier private notes, backend paths, storage keys, or tokens
- commit `.env`, `local_data/`, `backend/storage/`, generated logs, uploads, customer files, or real tokens
- deploy or modify `service.intelli-opus.com`
- edit nginx or cloud upstreams

## Validation

Run these checks after changing this migration guide:

```powershell
cd backend
python scripts/web_to_desktop_migration_doc_check.py
python scripts/desktop_target_architecture_check.py
python scripts/desktop_packaging_docs_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
```

## Related Docs

- [Product Vision](product_vision.md)
- [Desktop Target Architecture](architecture_desktop_target.md)
- [Runtime Modes](runtime_modes.md)
- [Database Lifecycle](database_lifecycle.md)
- [Packaging Strategy](packaging_strategy.md)
- [Open Questions: Desktop & Packaging](open_questions_desktop.md)
