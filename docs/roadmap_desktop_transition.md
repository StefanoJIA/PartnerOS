# Desktop Transition Roadmap

**Status:** current on 2026-05-30 as a product-strategy roadmap.
**Current execution state:** `READY_FOR_STAGING_HANDOFF`.

This roadmap explains the desktop-first product direction and how the earlier D0-D6 transition work maps into the current D7-D9 execution chain. It is not the active staging runbook; use [D8 Staging Handoff Bundle](phase3/d8_staging_handoff_bundle.md) and [D8 Staging Operator Runbook](phase3/d8_staging_operator_runbook.md) for that.

## Product Principle

PartnerOS is the internal source of truth for intelliOffice operations. The final customer/operator product remains Windows-first and desktop-oriented: users should not need to install or manage PostgreSQL, pgAdmin, Docker, Alembic, seed scripts, or multiple terminals to use the packaged product.

Development mode may still use Vue, FastAPI, PostgreSQL, Docker, and manual commands. That is the implementation stack, not the end-user deployment assumption.

## Historical Transition Stages

| Stage | Intent | Current result |
|---|---|---|
| D0 | Reorient docs from web-first to desktop-first | Superseded by current README, product vision, testing guide, and execution gates |
| D1 | Make backend runtime and health checks desktop-ready | Implemented through runtime mode, health, doctor, and database lifecycle checks |
| D2 | Add desktop shell path and frontend health behavior | Implemented enough for development/test coverage; product packaging remains a later productization concern |
| D3 | Add backend sidecar and managed runtime direction | Implemented through sidecar entry, packaging scripts, and runtime docs |
| D4 | Define database lifecycle manager and bootstrap boundaries | Implemented through database lifecycle docs, health fields, and tests |
| D5 | Close lead intelligence, enrichment, manual outreach, and pre-quote handoff | Closed as D5 Final |
| D6 | Close quote MVP through quote-to-order readiness | Closed as D6 Final |

## Current Execution Stages

| Stage | Scope | Current result |
|---|---|---|
| D7 | Orders, confirmations, partners/suppliers, production milestones, shipment plans, portal bridge, resources | Closed through D7.9 |
| D8 | Runtime hardening, service portal staging integration, strict staging evidence, production coordination readiness | Local gates ready; waiting for real staging values and evidence |
| D9 | Post-launch operating loop, health review, order operations, market response, improvement backlog | Planned behind `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, production coordination, and human Go / No-Go handoff; if committed, the record uses `docs/records/d8_production_go_no_go_YYYYMMDD.md` |

Current local proof is `READY_FOR_STAGING_HANDOFF`, not `STAGING_VALIDATED`.

## Active Validation Chain

```powershell
cd backend
python scripts/agent_guide_check.py
python scripts/readme_check.py
python scripts/deployment_readiness_checklist_check.py
python scripts/testing_guide_check.py
python scripts/desktop_transition_roadmap_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
```

For D7.6+ smoke and current D8 local validation, use backend port `8014` and follow [Testing Guide](testing.md).

## Deferred Productization Work

These remain valid product goals, but they are not authorized by the current staging handoff and should not be mixed into D8 evidence work:

- Packaged Windows installer polish and auto-update decisions.
- End-user database provisioning UX beyond the current lifecycle foundation.
- Backup/restore product UX and support diagnostics export.
- Full enterprise RBAC productization beyond current scoped access foundations.
- Cloud sync and multi-site deployment.
- Heavy web scraping, local LLM training, and campaign automation.
- Large Field Visit detail workspace and Constant Contact/Campaign features.

## Safety Boundaries

- No final-user workflow may require pgAdmin, manual PostgreSQL administration, Docker CLI, Alembic, or seed scripts.
- No automatic email, webhook, carrier API, supplier notification, customer notification, order/shipment/payment mutation, nginx edit, cloud upstream edit, or `service.intelli-opus.com` deployment is authorized by this roadmap.
- No internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, cookie, or raw response body may be exposed through customer-facing APIs or committed records.

## References

- [Product Vision](product_vision.md)
- [Architecture Desktop Target](architecture_desktop_target.md)
- [Runtime Modes](runtime_modes.md)
- [Database Lifecycle](database_lifecycle.md)
- [Packaging Strategy](packaging_strategy.md)
- [Migration From Web To Desktop](migration_from_web_to_desktop.md)
- [Project Reorientation Summary](project_reorientation_summary.md)
- [Phase 3 Roadmap](phase3/phase3_roadmap.md)
- [Project Execution Chain Gate](phase3/project_execution_chain_gate.md)
