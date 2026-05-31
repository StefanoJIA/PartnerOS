# D8 Staging Gap Triage

**Status:** added on 2026-05-30; used only when strict staging evidence returns `FAIL`.

## Purpose

This runbook turns a failed D8 strict staging evidence run into a human-owned fix loop. It keeps PartnerOS staging validation moving without storing secrets, changing `service.intelli-opus.com`, or treating failed evidence as production readiness.

## Entry Criteria

- `python scripts/d8_strict_staging_evidence_check.py` returned `FAIL`.
- A redacted evidence file exists at `docs/records/d8_strict_staging_evidence_YYYYMMDD.json`.
- A paired gap register exists at `docs/records/d8_strict_staging_gaps_YYYYMMDD.md`.
- `python scripts/d8_staging_records_check.py` passes before any record is shared or committed.

## Triage Loop

1. Open the latest `d8_strict_staging_gaps_YYYYMMDD.md`.
2. Assign every open row an owner and expected next action.
3. Classify the gap as configuration, token/CORS, runtime readiness, portal bridge contract, field leakage, test data, or unknown.
4. Fix only the PartnerOS-side issue that is in scope for this repository.
5. Do not edit nginx, cloud upstreams, or the customer portal UI from this repository.
6. Rerun strict staging evidence with the same redacted evidence/gap artifact pattern.
7. Close the old row only after the rerun proves the check passed or the gap is superseded by a newer evidence date.

## Required Gap Register Columns

| Column | Meaning |
|---|---|
| Check | Failing evidence check label |
| Detail | Sanitized failure detail, never raw response bodies |
| Recommended action | Safe next fix or investigation step |
| Owner | Human owner or team placeholder |
| Status | `open`, `blocked`, `fixed_pending_rerun`, or `closed` |

`Owner: TBD` is allowed only as a human owner placeholder until the staging operator assigns a named operator or team. It is not an auto-assignee, notification target, or permission to create tickets.

## Close Criteria

- Latest strict staging evidence JSON has `result=PASS`, or a newer failed evidence run contains a narrower remaining gap list.
- `python scripts/d8_staging_records_check.py` passes.
- `python scripts/d8_readiness_audit.py` reports either `STAGING_VALIDATED` or the current `STAGING_GAPS_OPEN` state with the latest gap register.
- `python scripts/d8_production_coordination_check.py` does not report `WAITING_FOR_REAL_STAGING_EVIDENCE`; local rehearsal evidence must be replaced by strict staging evidence from real staging values before coordination.
- No gap record contains token values, `.env` content, raw response bodies, customer files, internal costs, supplier private notes, storage paths, or backend secrets.

## Safety Boundaries

- No automatic customer or supplier notification.
- No email, webhook, carrier API, quote mutation, order mutation, shipment mutation, payment action, inventory reservation, or partner-selection mutation.
- No customer portal deployment, nginx edit, or cloud upstream edit from this repository.
- No internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, or secret in any shared record.
