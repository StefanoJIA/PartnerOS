# D8 Production Coordination Runbook

**Status:** added on 2026-05-30; use only after `STAGING_VALIDATED`.

## Purpose

This runbook defines the human Go / No-Go sequence after strict staging evidence passes. It coordinates what PartnerOS can hand to the portal/cloud operator, what must stay outside this repository, and when D9 operating gates may begin.

It does not deploy, route, notify, mutate orders, or modify `service.intelli-opus.com`.

## State Map

| State | Meaning | Operator action |
|---|---|---|
| `WAITING_FOR_STAGING_VALIDATION` | Strict staging evidence is missing or failed | Do not start production coordination |
| `WAITING_FOR_REAL_STAGING_EVIDENCE` | Latest evidence is local rehearsal output, not real staging evidence | Replace it with strict staging evidence from real staging values |
| `STAGING_VALIDATED` | Latest strict staging evidence is PASS and records hygiene passed | Prepare Go / No-Go materials |
| `BLOCKED_BY_EVIDENCE_REVIEW` | Readiness says staging passed, but evidence review does not report `READY_FOR_PRODUCTION_COORDINATION_REVIEW` | Return to evidence review or gap triage before Go / No-Go |
| `READY_FOR_PRODUCTION_COORDINATION` | `python scripts/d8_production_coordination_check.py` confirms the local coordination gate | Share redacted evidence and plan with the portal/cloud operator |
| `READY_FOR_PRODUCTION_GO_NO_GO` | Portal/cloud operator has reviewed the redacted package and target ownership | Hold the human Go / No-Go review outside PartnerOS automation |
| `PRODUCTION_COORDINATION_PAUSED` | Any safety, evidence, routing, token, CORS, readiness, or forbidden-field concern appears | Pause and return to gap triage |
| `POST_COORDINATION_D9_READY` | Human coordination completes and no rollback signal is open | Run D9 operating execution pack and kickoff checks |

## Entry Checks

```powershell
cd backend
python scripts/d8_staging_execution_pack_check.py
python scripts/d8_staging_records_check.py
python scripts/d8_staging_evidence_review_check.py
python scripts/d8_readiness_audit.py
python scripts/d8_production_coordination_check.py
```

Proceed only when readiness is `STAGING_VALIDATED`, evidence review is `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, and coordination state is `READY_FOR_PRODUCTION_COORDINATION`.

## Go / No-Go Sequence

1. Confirm the latest evidence JSON is the canonical `docs/records/d8_strict_staging_evidence_YYYYMMDD.json`.
2. Confirm no matching latest gap register remains open.
3. Share only the redacted evidence summary, production coordination plan, and rollback signals with the portal/cloud operator.
4. Confirm the portal/cloud operator owns any routing, cloud upstream, token rotation, and `service.intelli-opus.com` deployment work.
5. Record the human decision as Go, No-Go, or Pause in an external operations channel. If the decision is committed, use the canonical redacted record `docs/records/d8_production_go_no_go_YYYYMMDD.md`.
6. If Go completes with no open rollback signal, run the D9 readiness checks:

```powershell
cd backend
python scripts/d9_operating_execution_pack_check.py
python scripts/d9_operating_loop_kickoff_check.py
```

## Rollback Handoff

Rollback is owned by the portal/cloud operator. PartnerOS should provide only these redacted signals:

| Signal | Meaning |
|---|---|
| strict evidence failure | Production-like endpoint no longer matches the safe bridge contract |
| forbidden field finding | Customer-visible payload includes internal cost, margin, supplier private note, backend path, token, or secret |
| auth rejection regression | Missing or invalid portal token is accepted |
| CORS mismatch | `SERVICE_PORTAL_ORIGIN` is not accepted as expected |
| readiness or manifest failure | Public health/readiness contract is missing or unsafe |

## Boundaries

- No `.env`, token values, cookies, raw headers, raw response bodies, screenshots with secrets, customer files, uploads, `local_data`, or `backend/storage`.
- No nginx or cloud upstream change from this repository.
- No `service.intelli-opus.com` deployment from this repository.
- No email, webhook, carrier API, customer or supplier notification, or quote/order/shipment/payment/inventory/partner-selection mutation.
- No internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, database URL, or secret in committed artifacts.
- No token values.
- No raw response bodies.
- No nginx.
- No cloud upstream.
- No email, webhook, carrier API.
- No customer or supplier notification.
- No quote/order/shipment/payment/inventory/partner-selection mutation.
- No internal cost, margin, pricing breakdown.
