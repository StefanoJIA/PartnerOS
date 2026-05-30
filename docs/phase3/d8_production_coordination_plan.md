# D8 Production Coordination Plan

**Status:** planned on 2026-05-30; waiting for `STAGING_VALIDATED`.

## Purpose

This plan defines the narrow production coordination path after D8 strict staging evidence passes. It does not authorize deployment from this repository and does not change `service.intelli-opus.com`.

## Entry Criteria

| Gate | Required evidence |
|---|---|
| Local D8 package | `python scripts/d8_staging_execution_pack_check.py` passes |
| Records hygiene | `python scripts/d8_staging_records_check.py` passes |
| Staging evidence | `python scripts/d8_readiness_audit.py` reports `STAGING_VALIDATED` |
| Gap register | No open D8 strict staging gap register remains for the latest evidence run |

## Go / No-Go

| Area | Go condition | No-Go condition |
|---|---|---|
| Portal bridge | Customer-safe products, orders, production, shipment, resources, and feedback status read from PartnerOS staging | Token rejection, CORS, manifest, readiness, or subresource checks fail |
| Field safety | No internal cost, margin, pricing breakdown, supplier private note, storage path, backend path, token, or secret appears in bridge payloads | Any forbidden marker appears in evidence |
| Runtime | HTTPS public backend URL and HTTPS service portal origin are confirmed | HTTP staging URL, unsafe token, missing token requirement, or readiness failure |
| Records | Redacted evidence and gap artifacts use canonical `docs/records/d8_*_YYYYMMDD` names | Evidence stores raw response bodies, tokens, backend storage paths, or noncanonical record names |

## Coordination Steps

1. Generate the final operator handoff with `python scripts/d8_staging_operator_handoff.py`.
2. Confirm `python scripts/d8_readiness_audit.py` returns `STAGING_VALIDATED`.
3. Share only redacted evidence and the production coordination plan with the portal/cloud operator.
4. The portal/cloud operator coordinates any production routing outside this repository.
5. Re-run strict evidence against the production-like endpoint only after the operator confirms the target and token.
6. Record the final PASS/FAIL evidence under `docs/records` using canonical names.

## Rollback

Rollback is owned by the portal/cloud operator because PartnerOS must not edit nginx or upstream routing from this repository. The rollback signal is any failed production-like evidence check, customer-visible forbidden-field finding, token rejection regression, CORS mismatch, readiness failure, or unexpected customer portal behavior.

## Boundaries

- No nginx or upstream change from this repository.
- No customer portal deployment from this repository.
- No customer or supplier notification.
- No email, webhook, carrier API, or external send action.
- No automatic order, shipment, delivery, payment, or partner-selection mutation.
- No internal cost, margin, supplier private note, token, backend path, storage key, database URL, or secret in customer-visible payloads or evidence records.
