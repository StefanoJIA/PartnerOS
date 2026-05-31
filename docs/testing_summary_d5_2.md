# D5.2 Testing Summary

**Status:** historical baseline from 2026-05-23; superseded for current validation on 2026-05-30.

## Purpose

This file preserves the D5.2 Internal MVP testing baseline for release history. It is not the current D8/D9 validation matrix and must not be used to claim `READY_FOR_STAGING_HANDOFF` or `STAGING_VALIDATED`.

Current validation lives in:

- [Testing Guide](testing.md)
- [Deployment Readiness Checklist](deployment_readiness_checklist.md)
- [Project Execution Chain Gate](phase3/project_execution_chain_gate.md)
- [Project Execution Acceptance Audit](phase3/project_execution_acceptance_audit.md)

## Historical Baseline

At the D5.2 baseline, the project recorded:

- backend pytest passing for the D5.2 scope
- frontend vitest passing for the D5.2 scope
- local read-only scripts passing against the then-current developer backend
- portal read-only consumer checks for the historical D5.2 integration

Representative historical commands were:

```powershell
cd backend
python -m pytest -q
python scripts/config_readiness_check.py
python scripts/portal_consumer_check.py

cd ../frontend
npm run test -- --run
```

These commands remain useful for archaeology, but the current D7.6+/D8 handoff uses backend port `8014` and the D8/D9 gate chain.

## Current Replacement

Use the current matrix instead:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/project_execution_chain_check.py
python scripts/project_execution_status.py
python scripts/d8_staging_execution_pack_check.py
python scripts/testing_summary_d5_2_check.py
```

The expected current local state is `READY_FOR_STAGING_HANDOFF`. Strict staging remains separate and requires real private values plus redacted saved evidence.

## Historical Scope Limits

D5.2 did not validate:

- D7 order, production, shipment, portal bridge, or resource-center workflows
- D8 RBAC, runtime hardening, partner operations, market response, or staging evidence
- D9 operating-loop plans
- production HTTPS, service portal cutover, nginx, or cloud upstream changes
- automatic customer or supplier messaging

## Safety Boundaries

Do not use this historical summary to:

- commit `.env`, `local_data/`, `backend/storage/`, uploads, generated logs, customer files, or real tokens
- expose raw response bodies, tokens, backend paths, internal costs, margins, pricing breakdowns, or supplier private notes
- deploy or modify `service.intelli-opus.com`
- edit nginx or cloud upstreams
- send email, webhooks, carrier API calls, customer notifications, or supplier notifications
- automatically change quote, order, shipment, delivery, payment, inventory, or partner-selection state

## Historical Records

| Stage | Record |
|---|---|
| D5.2.2 | [D5.2.2 Internal MVP](records/d5_2_2_internal_mvp_20260523.md) |
| D5.2.7 | [D5.2.7 Follow-Up Rhythm](records/d5_2_7_follow_up_rhythm_20260523.md) |
| D5.2.8 | [D5.2.8 Browser Manual Verification](records/d5_2_8_browser_manual_verification_20260523.md) |
| D5.2.9 | [D5.2.9 Portal Readonly Integration](records/d5_2_9_portal_readonly_integration_20260523.md) |
| D5.2.10 | [D5.2.10 Portal Consumer Deployment Readiness](records/d5_2_10_portal_consumer_deployment_readiness_20260523.md) |

## Validation

```powershell
cd backend
python scripts/testing_summary_d5_2_check.py
python scripts/project_execution_chain_check.py
```
