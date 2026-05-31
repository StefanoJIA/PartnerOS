# Project Reorientation Summary

**Status:** current on 2026-05-30.
**Current execution state:** `READY_FOR_STAGING_HANDOFF`.

## Why The Reorientation Still Matters

PartnerOS remains a Windows-first, local-first operating system for intelliOffice operations. The repository still uses Vue, FastAPI, PostgreSQL, Alembic, and development scripts, but that is the implementation stack. It is not the final-user deployment model.

Final users should not need to install or manage PostgreSQL, pgAdmin, Docker, Alembic, seed scripts, connection strings, or multiple terminals. Product mode must hide those concerns behind the packaged app, local sidecar, database lifecycle, health states, diagnostics, and guided recovery.

## What Changed Since The Original D0/D1 Reorientation

The original reorientation focused on moving from web-first assumptions to a desktop-first product foundation. That work has now been absorbed into later execution:

| Area | Current state |
|---|---|
| D5 Lead Intelligence | Closed as D5 Final |
| D6 Quote MVP | Closed as D6 Final |
| D7 Orders / Production / Shipment / Portal bridge / Resources | Closed through D7.9 |
| D8 Runtime and staging handoff | Local gates ready; waiting for real staging values and strict evidence |
| D9 Operating loop | Planned behind `STAGING_VALIDATED`, evidence review, production coordination, and the human Go / No-Go handoff |

The correct current project state is `READY_FOR_STAGING_HANDOFF`, not D0/D1 kickoff.

## Current Priority

Use the D8 staging handoff package and obtain the private staging values needed for strict evidence:

- real `BACKEND_BASE_URL`
- real `SERVICE_PORTAL_PARTNEROS_TOKEN`
- real `SERVICE_PORTAL_ORIGIN`
- deployed PartnerOS staging commit or release tag
- representative TEST fixture scope

Then run strict staging evidence and review the saved redacted records before production coordination, the human Go / No-Go handoff, or D9 kickoff. If the Go / No-Go decision is committed, use `docs/records/d8_production_go_no_go_YYYYMMDD.md`.

## Active Proof Chain

```powershell
cd backend
python scripts/agent_guide_check.py
python scripts/readme_check.py
python scripts/desktop_transition_roadmap_check.py
python scripts/project_reorientation_summary_check.py
python scripts/deployment_readiness_checklist_check.py
python scripts/testing_guide_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
```

For D7.6+ smoke and local D8 validation, use backend port `8014`.

## Product Rules That Still Hold

- PartnerOS is the internal source of truth; `service.intelli-opus.com` remains the customer-facing portal.
- Customer-facing APIs must use strict field whitelists.
- Manufacturing partners are peer rows; no hard-coded HOSUN, JOOBOO, or future partner preference is allowed.
- Lead Intelligence belongs to the market/customer intelligence domain and must feed the quote/order/partner workflow rather than become a silo.
- AI outputs and D9 operating records remain advisory and human-reviewed.
- No product path may require final users to run pgAdmin, PostgreSQL administration, Docker CLI, Alembic, seed scripts, or raw shell commands.

## Explicit Non-Goals For The Current Handoff

- No `service.intelli-opus.com` deployment from this repository.
- No nginx/cloud upstream edits from this repository.
- No automatic email, webhook, carrier API, customer notification, supplier notification, quote/order/shipment/payment mutation, or automatic ticket creation.
- No internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, cookie, raw response body, or customer file in committed docs or records.

## References

- [Product Vision](product_vision.md)
- [Desktop Transition Roadmap](roadmap_desktop_transition.md)
- [Testing Guide](testing.md)
- [Deployment Readiness Checklist](deployment_readiness_checklist.md)
- [Project Execution Chain Gate](phase3/project_execution_chain_gate.md)
- [Project Execution Acceptance Audit](phase3/project_execution_acceptance_audit.md)
- [D8 Staging Handoff Bundle](phase3/d8_staging_handoff_bundle.md)
