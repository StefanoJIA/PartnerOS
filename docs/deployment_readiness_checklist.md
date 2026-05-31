# Deployment Readiness Checklist

**Status:** current for D8/D9 on 2026-05-30.
**Current state:** `READY_FOR_STAGING_HANDOFF`.
**Scope:** staging handoff and production-coordination readiness only. This is not a production deploy runbook.

## Current Boundary

PartnerOS local implementation is ready to hand to a staging operator, but production coordination is still blocked until real strict staging evidence exists and has been reviewed.

Use this checklist to keep deployment readiness aligned with the current project gates:

- `READY_FOR_STAGING_HANDOFF` means local docs, checks, and runbooks agree.
- `READY_FOR_STAGING` means local D8 readiness prerequisites are present.
- `STAGING_VALIDATED` requires saved strict staging evidence from the real deployed staging backend.
- `READY_FOR_PRODUCTION_COORDINATION_REVIEW` requires the saved evidence review gate to pass.
- D9 operating-loop work remains gated behind staging validation, evidence review, production coordination, and the human Go / No-Go handoff.

Do not use this repository to deploy or modify `service.intelli-opus.com`, edit nginx/cloud upstreams, or run production release steps.

## Required Private Inputs

The repo must not store these values. Request them through [D8 Staging Access Request](phase3/d8_staging_access_request.md), then preflight them locally before running strict staging evidence.

| Input | Required shape | Storage rule |
|---|---|---|
| `BACKEND_BASE_URL` | HTTPS PartnerOS staging backend origin | Shell/session only |
| `SERVICE_PORTAL_PARTNEROS_TOKEN` | Non-default portal server token | Shell/session only; never paste into docs |
| `SERVICE_PORTAL_ORIGIN` | HTTPS service portal origin, normally `https://service.intelli-opus.com` | Shell/session only |
| Deployed commit or release tag | The staging build being tested | Redacted evidence metadata only |
| TEST fixture scope | Non-production records used for the run | Redacted evidence/gap summaries only |

## Local Handoff Gate

Run these before giving the package to a staging operator:

```powershell
cd backend
python scripts/readme_check.py
python scripts/deployment_readiness_checklist_check.py
python scripts/operator_guide_check.py
python scripts/project_execution_status.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/project_execution_acceptance_audit_check.py
python scripts/d8_staging_execution_pack_check.py
python scripts/d8_staging_handoff_bundle_check.py
python scripts/d8_staging_operator_runbook_check.py
python scripts/d8_staging_access_request_check.py
python scripts/d8_staging_input_preflight_check.py
```

Expected local state before external validation:

- `project_execution_status.py` reports `READY_FOR_STAGING_HANDOFF`.
- `d8_readiness_audit.py` reports `READY_FOR_STAGING`.
- `d8_production_coordination_check.py` reports `WAITING_FOR_STAGING_VALIDATION`.
- If local rehearsal evidence is saved by mistake, `d8_production_coordination_check.py` reports `WAITING_FOR_REAL_STAGING_EVIDENCE` until real strict staging evidence replaces it.
- Input preflight may report `WAITING_FOR_PRIVATE_VALUES` until operations supplies the private staging values; `LOCAL_REHEARSAL_READY` is rehearsal-only and must not produce committed staging evidence.

## Strict Staging Evidence

Run only after private staging inputs are available and input preflight is safe:

```powershell
cd backend
$env:BACKEND_BASE_URL="https://<partneros-staging-backend-origin>"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_staging_input_preflight_check.py
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
python scripts/d8_staging_records_check.py
python scripts/d8_staging_evidence_review_check.py
python scripts/d8_readiness_audit.py
```

Saved evidence must be redacted. It may contain check names, pass/fail status, sanitized URLs, and safety metadata. It must not contain token values, raw response bodies, customer files, upload contents, backend storage paths, `local_data` paths, internal cost or margin details, supplier private notes, or secrets.

## Production Coordination Gate

Production coordination can start only when all of these are true:

- `d8_readiness_audit.py` reports `STAGING_VALIDATED`.
- `d8_staging_evidence_review_check.py` reports `READY_FOR_PRODUCTION_COORDINATION_REVIEW`.
- `d8_production_coordination_check.py` moves out of `WAITING_FOR_STAGING_VALIDATION`.
- The human operator has reviewed the saved evidence and gap records.
- If the Go / No-Go decision is committed, it uses the redacted canonical record `docs/records/d8_production_go_no_go_YYYYMMDD.md`.

Then run:

```powershell
cd backend
python scripts/d8_production_coordination_check.py
python scripts/d8_production_coordination_runbook_check.py
```

This gate prepares a human Go / No-Go and rollback handoff. It does not perform a deployment, edit infrastructure, notify customers, notify suppliers, or mutate order/shipment/payment state.

## D9 Gate

D9 operating-loop execution starts only after `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, production coordination, and the human Go / No-Go handoff are all ready.

```powershell
cd backend
python scripts/d9_operating_execution_pack_check.py
python scripts/d9_operating_loop_kickoff_check.py
python scripts/d9_1_operating_health_review_check.py
python scripts/d9_2_order_operations_loop_check.py
python scripts/d9_3_market_response_loop_check.py
python scripts/d9_4_improvement_backlog_check.py
python scripts/d9_operating_records_check.py
```

## Safety Boundaries

- No `.env`, `local_data`, `backend/storage`, upload, generated log, token, cookie, or raw response body may be committed.
- No carrier API, webhook, email, supplier notification, customer notification, nginx edit, cloud upstream edit, or `service.intelli-opus.com` deployment is authorized here.
- Do not automatically change order status to shipped or delivered.
- Do not expose internal cost, margin, pricing breakdown, supplier private notes, backend file paths, storage keys, or tokens through customer-facing APIs or handoff records.
- Feedback intake remains human-reviewed and does not auto-reply or promise resolution time.

## References

- [README](../README.md)
- [Operator Guide](operator_guide.md)
- [Project Execution Chain Gate](phase3/project_execution_chain_gate.md)
- [Project Execution Acceptance Audit](phase3/project_execution_acceptance_audit.md)
- [D8 Staging Handoff Bundle](phase3/d8_staging_handoff_bundle.md)
- [D8 Staging Operator Runbook](phase3/d8_staging_operator_runbook.md)
- [D8 Production Coordination Runbook](phase3/d8_production_coordination_runbook.md)
- [D9 Operating Execution Pack](phase3/d9_operating_execution_pack.md)
