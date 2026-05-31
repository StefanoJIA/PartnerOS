# D8 Staging Operator Runbook

**Status:** added on 2026-05-30; use after `READY_FOR_STAGING_HANDOFF`.

## Purpose

This runbook gives the staging operator the exact execution order for moving from local handoff readiness to reviewed strict staging evidence. It is a local, redacted operator checklist; it does not replace the real staging evidence command and does not produce `STAGING_VALIDATED` by itself.

## State Map

| State | Meaning | Operator action |
|---|---|---|
| `READY_FOR_STAGING_HANDOFF` | Local planning, docs, and checks agree | Request private staging values and generate a dated handoff |
| `WAITING_FOR_PRIVATE_VALUES` | Required staging values are unavailable or placeholders | Obtain values privately; do not commit them |
| `INPUTS_UNSAFE` | Provided staging inputs are non-HTTPS, placeholder, known-default, too short, or otherwise unsafe | Fix values before strict evidence |
| `WAITING_FOR_STAGING_EVIDENCE` | Inputs may be ready but no saved strict evidence exists | Run strict evidence and save redacted artifacts |
| `STAGING_GAPS_OPEN` | Strict evidence failed and a gap register exists | Triage owners, close gaps, rerun evidence |
| `STAGING_VALIDATED` | Latest strict evidence is PASS | Proceed to production coordination review |

## Operator Sequence

1. Confirm the local handoff state.

```powershell
cd backend
python scripts/project_execution_status.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/d8_staging_execution_pack_check.py
```

2. Confirm private values are present and safe on the operator machine.

```powershell
cd backend
$env:BACKEND_BASE_URL="https://partneros-staging.example.com"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<portal-server-token>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
python scripts/d8_staging_input_preflight_check.py
```

3. Run strict staging evidence and produce only canonical redacted artifacts.

```powershell
cd backend
python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md
python scripts/d8_staging_records_check.py
python scripts/d8_staging_evidence_review_check.py
python scripts/d8_readiness_audit.py
```

4. Review the next state.

```powershell
cd backend
python scripts/d8_production_coordination_check.py
python scripts/project_execution_status.py
```

## Evidence Acceptance

| Artifact | Acceptance rule |
|---|---|
| `docs/records/d8_strict_staging_evidence_YYYYMMDD.json` | Redacted JSON exists, records check passes, and evidence review reads the latest result |
| `docs/records/d8_strict_staging_gaps_YYYYMMDD.md` | Required when evidence result is FAIL; contains owner/status/rerun fields only |
| Console summaries | `project_execution_status.py` still reports the next manual action; no raw bodies or secrets are printed |

## Boundaries

- No `.env`, token values, cookies, raw headers, raw response bodies, screenshots with secrets, customer files, uploads, `local_data`, or `backend/storage`.
- No nginx, cloud upstream, or `service.intelli-opus.com` deployment from this repository.
- No email, webhook, carrier API, automatic customer or supplier notification, or quote/order/shipment/payment/inventory/partner-selection mutation.
- No internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, database URL, or secret in committed artifacts.
- No token values.
- No raw response bodies.
- No `service.intelli-opus.com` deployment.
- No automatic customer or supplier notification.
- No quote/order/shipment/payment/inventory/partner-selection mutation.
