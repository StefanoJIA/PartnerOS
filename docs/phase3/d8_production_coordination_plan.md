# D8 Production Coordination Plan

**Status:** planned on 2026-05-30; waiting for `STAGING_VALIDATED`.

## Purpose

This plan defines the narrow production coordination path after D8 strict staging evidence passes. It does not authorize deployment from this repository and does not change `service.intelli-opus.com`.

Use [D8 Production Coordination Runbook](d8_production_coordination_runbook.md) for the human Go / No-Go sequence after this plan is ready.

## Entry Criteria

| Gate | Required evidence |
|---|---|
| Local D8 package | `python scripts/d8_staging_execution_pack_check.py` passes |
| Records hygiene | `python scripts/d8_staging_records_check.py` passes |
| Evidence review | `python scripts/d8_staging_evidence_review_check.py` reports `READY_FOR_PRODUCTION_COORDINATION_REVIEW` |
| Staging evidence | `python scripts/d8_readiness_audit.py` reports `STAGING_VALIDATED` |
| Coordination state | `python scripts/d8_production_coordination_check.py` reports `READY_FOR_PRODUCTION_COORDINATION` |
| Gap register | No open D8 strict staging gap register remains for the latest evidence run |
| Go / No-Go record | Optional redacted decision record uses `docs/records/d8_production_go_no_go_YYYYMMDD.md` |

## Go / No-Go

| Area | Go condition | No-Go condition |
|---|---|---|
| Portal bridge | Customer-safe products, orders, production, shipment, resources, and feedback status read from PartnerOS staging | Token rejection, CORS, manifest, readiness, or subresource checks fail |
| Field safety | No internal cost, margin, pricing breakdown, supplier private note, storage path, backend path, token, or secret appears in bridge payloads | Any forbidden marker appears in evidence |
| Runtime | HTTPS public backend URL and HTTPS service portal origin are confirmed | HTTP staging URL, unsafe token, missing token requirement, or readiness failure |
| Records | Redacted evidence and gap artifacts use canonical `docs/records/d8_*_YYYYMMDD` names | Evidence stores raw response bodies, tokens, backend storage paths, or noncanonical record names |

## Coordination Steps

1. Generate the final operator handoff with `python scripts/d8_staging_operator_handoff.py`.
2. Confirm `python scripts/d8_staging_evidence_review_check.py` reports `READY_FOR_PRODUCTION_COORDINATION_REVIEW`.
3. Confirm `python scripts/d8_readiness_audit.py` returns `STAGING_VALIDATED`.
4. Confirm `python scripts/d8_production_coordination_check.py` reports `READY_FOR_PRODUCTION_COORDINATION`.
5. Share only redacted evidence and the production coordination plan with the portal/cloud operator.
6. The portal/cloud operator coordinates any production routing outside this repository.
7. Re-run strict evidence against the production-like endpoint only after the operator confirms the target and token.
8. Record the final PASS/FAIL evidence under `docs/records` using canonical names.
9. If a Go, No-Go, or Pause decision is committed, use `docs/records/d8_production_go_no_go_YYYYMMDD.md` with only redacted summaries and no routing secrets.
10. After production coordination succeeds, use [D9 Post-Launch Operating Loop](d9_post_launch_operating_loop.md) to monitor operating health, order operations, feedback, market response, and improvement backlog.

## Rollback

Rollback is owned by the portal/cloud operator because PartnerOS must not edit nginx or upstream routing from this repository. The rollback signal is any failed production-like evidence check, customer-visible forbidden-field finding, token rejection regression, CORS mismatch, readiness failure, or unexpected customer portal behavior.

## Boundaries

- No nginx or upstream change from this repository.
- No customer portal deployment from this repository.
- No customer or supplier notification.
- No email, webhook, carrier API, or external send action.
- No automatic order, shipment, delivery, payment, or partner-selection mutation.
- No internal cost, margin, supplier private note, token, backend path, storage key, database URL, or secret in customer-visible payloads or evidence records.
