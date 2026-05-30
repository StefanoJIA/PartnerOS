# D9 Operating Loop Kickoff

**Status:** planned on 2026-05-30; starts only after D8 production coordination completes.

## Purpose

This kickoff checklist turns the D9 post-launch operating loop into the first concrete review session after D8 staging evidence and production coordination are complete. It keeps the first production-era review focused, redacted, and human-owned.

It does not authorize service portal deployment, nginx edits, notifications, external sends, carrier calls, or business-record mutations.

## Entry Criteria

| Gate | Required evidence |
|---|---|
| D8 staging validation | `python scripts/d8_readiness_audit.py` reports `STAGING_VALIDATED` |
| Production coordination | `python scripts/d8_production_coordination_check.py` reports `READY_FOR_PRODUCTION_COORDINATION` |
| Evidence review | `python scripts/d8_staging_evidence_review_check.py` reports `READY_FOR_PRODUCTION_COORDINATION_REVIEW` |
| Records hygiene | `python scripts/d8_staging_records_check.py` and `python scripts/d9_operating_records_check.py` pass |

## Kickoff Agenda

| Track | Review prompt | Output |
|---|---|---|
| [D9.1 Operating Health Review](d9_1_operating_health_review.md) | Are readiness, CORS, token rejection, and customer-safe portal reads healthy after coordination? | Redacted health summary |
| [D9.2 Order Operations Loop](d9_2_order_operations_loop.md) | Which confirmed orders need production, shipment, resource, or feedback follow-up? | Owner/action list |
| [D9.3 Market Response Loop](d9_3_market_response_loop.md) | Which feedback, quote outcomes, product gaps, or demand signals should feed advisory review? | Advisory notes |
| [D9.4 Improvement Backlog](d9_4_improvement_backlog.md) | Which repeated gaps deserve scoped implementation briefs? | Backlog candidate list |

## Kickoff Command

```powershell
cd backend
python scripts/d9_operating_loop_kickoff_check.py
python scripts/d9_1_operating_health_review_check.py
python scripts/d9_2_order_operations_loop_check.py
python scripts/d9_3_market_response_loop_check.py
python scripts/d9_4_improvement_backlog_check.py
python scripts/d9_post_launch_plan_check.py
python scripts/d9_operating_records_check.py
```

## Record Template

Use a canonical redacted D9 record name such as `docs/records/d9_operating_review_YYYYMMDD.md`.

```markdown
# D9 Operating Review - YYYY-MM-DD

## D9.1 Operating Health Review
- Evidence:
- Owner:
- Next action:

## D9.2 Order Operations Loop
- Evidence:
- Owner:
- Next action:

## D9.3 Market Response Loop
- Evidence:
- Owner:
- Next action:

## D9.4 Improvement Backlog
- Evidence:
- Owner:
- Next action:
```

## Boundaries

- No `.env`, token value, bearer header, cookie, raw header, raw response body, customer file, upload, `local_data`, or `backend/storage` artifact may be committed.
- No email, webhook, carrier API, customer notification, supplier notification, order mutation, shipment mutation, payment action, inventory reservation, partner-selection mutation, nginx edit, cloud upstream edit, or `service.intelli-opus.com` deployment is authorized by kickoff.
- Internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, database URL, and secret values remain excluded from D9 records and customer-facing artifacts.
