# D8 Staging Handoff Bundle

**Status:** added on 2026-05-30; use when `project_execution_status.py` reports `READY_FOR_STAGING_HANDOFF`.

## Purpose

This bundle is the exact local package to hand to the staging operator before real strict staging evidence is run. It keeps the handoff small, redacted, and executable without moving secrets, customer files, or cloud deployment instructions into PartnerOS.

## Include

| Artifact | Purpose |
|---|---|
| [Operator Guide](../operator_guide.md) | Operator-facing guide for D8/D9 handoff gates and manual-only safety boundaries |
| [Deployment Readiness Checklist](../deployment_readiness_checklist.md) | Current D8/D9 staging handoff and production-coordination readiness checklist |
| [Testing Guide](../testing.md) | Current D7.6+/D8 local validation and strict staging evidence matrix |
| [Project Execution Chain Gate](project_execution_chain_gate.md) | Explains the aggregate local gate and `READY_FOR_STAGING_HANDOFF` state |
| [D8 Staging Operator Handoff](d8_staging_operator_handoff.md) | Explains how to generate the dated operator handoff |
| [D8 Local Staging Rehearsal](d8_local_staging_rehearsal.md) | Optional local command-order rehearsal; not staging proof |
| [D8 Staging Operator Runbook](d8_staging_operator_runbook.md) | Gives the operator sequence from handoff to evidence review |
| [D8 Staging Input Preflight](d8_staging_input_preflight.md) | Checks private staging values locally before strict evidence |
| [D8 Staging Access Request](d8_staging_access_request.md) | Lists the private staging values required from operations |
| [D8 Staging Operator Response Intake](d8_staging_operator_response_intake.md) | Defines what redacted operator response data the repo may accept |
| [D8 Strict Staging / Cloud Validation](d8_strict_staging_cloud_validation.md) | Defines the evidence command and pass criteria |
| [D8 Staging Gap Triage](d8_staging_gap_triage.md) | Defines the owner/status/rerun loop if evidence fails |
| [D8 Staging Records Policy](d8_staging_records_policy.md) | Defines canonical record names and redaction rules |
| [D8 Staging Evidence Review](d8_staging_evidence_review.md) | Defines how to interpret saved PASS/FAIL evidence before production coordination |
| [D8 Production Coordination Plan](d8_production_coordination_plan.md) | Defines the path after `STAGING_VALIDATED` |
| [D8 Production Coordination Runbook](d8_production_coordination_runbook.md) | Defines the human Go / No-Go and rollback handoff after staging validation |

## Committed Records

| Record | Use |
|---|---|
| [D8 Staging Operator Handoff Record](../records/d8_staging_operator_handoff_20260531.md) | Current redacted operator handoff generated from local gates |
| [D8 Staging Access Request Record](../records/d8_staging_access_request_20260531.md) | Current redacted request for private staging values |

## Preflight Commands

```powershell
cd backend
python scripts/readme_check.py
python scripts/deployment_readiness_checklist_check.py
python scripts/testing_guide_check.py
python scripts/project_execution_status.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/operator_guide_check.py
python scripts/d8_staging_execution_pack_check.py
python scripts/d8_staging_operator_runbook_check.py
python scripts/d8_local_staging_rehearsal_check.py
python scripts/d8_staging_input_preflight_check.py
python scripts/d8_staging_access_request_check.py
python scripts/d8_staging_operator_response_intake_check.py
python scripts/d8_staging_gap_triage_check.py
python scripts/d8_staging_records_check.py
python scripts/d8_staging_evidence_review_check.py
python scripts/d8_production_coordination_runbook_check.py
```

## Generated Handoff

```powershell
cd backend
python scripts/d8_staging_operator_handoff.py --output ../docs/records/d8_staging_operator_handoff_YYYYMMDD.md
python scripts/d8_staging_records_check.py
```

The generated handoff may be shared only after records check passes and the content contains no token values, raw response bodies, customer files, backend storage paths, or `local_data` references.

When private staging values are available, run [D8 Staging Input Preflight](d8_staging_input_preflight.md) before the strict evidence command. `WAITING_FOR_PRIVATE_VALUES` is acceptable before credentials arrive; `INPUTS_UNSAFE` must be fixed before evidence.

When operations replies, use [D8 Staging Operator Response Intake](d8_staging_operator_response_intake.md) to accept only redacted confirmation fields and canonical evidence artifact names.

[D8 Local Staging Rehearsal](d8_local_staging_rehearsal.md) is optional for command-order practice against local `127.0.0.1:8014`. It is not staging proof and must not be committed as `STAGING_VALIDATED` evidence.

## Strict Evidence Command

```powershell
cd backend
$env:BACKEND_BASE_URL="https://partneros-staging.example.com"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
python scripts/d8_staging_records_check.py
python scripts/d8_staging_evidence_review_check.py
python scripts/d8_readiness_audit.py
```

## Exclude

- `.env`, token values, cookies, raw headers, raw response bodies, screenshots with secrets, customer files, uploads, `local_data`, and `backend/storage`.
- nginx, cloud upstream, or `service.intelli-opus.com` deployment instructions.
- Carrier API calls, email/webhook actions, customer/supplier notification steps, or automatic quote/order/shipment/payment/inventory/partner-selection mutations.
- Internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, or secret.
