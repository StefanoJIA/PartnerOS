# D9.4 Improvement Backlog

**Status:** planned on 2026-05-30; starts only after D8 production coordination and D9 kickoff.

## Purpose

D9.4 converts repeated post-launch operating gaps into scoped implementation briefs for future sprints. It collects signals from D9.1 operating health, D9.2 order operations, and D9.3 market response, then turns only reviewed patterns into backlog candidates.

It is a planning loop, not an automatic ticket creator or product-change workflow.

## Entry Criteria

| Gate | Required evidence |
|---|---|
| D8 staging validation | `python scripts/d8_readiness_audit.py` reports `STAGING_VALIDATED` |
| D8 production coordination | `python scripts/d8_production_coordination_check.py` reports `READY_FOR_PRODUCTION_COORDINATION` |
| D9 kickoff | `python scripts/d9_operating_loop_kickoff_check.py` passes |
| D9.1 health review | `python scripts/d9_1_operating_health_review_check.py` passes |
| D9.2 order operations loop | `python scripts/d9_2_order_operations_loop_check.py` passes |
| D9.3 market response loop | `python scripts/d9_3_market_response_loop_check.py` passes |
| D9 records hygiene | `python scripts/d9_operating_records_check.py` passes |

## Backlog Candidate Fields

| Field | Meaning |
|---|---|
| Source loop | D9.1 health, D9.2 order operations, or D9.3 market response |
| Evidence summary | Redacted description of repeated signal or gap |
| Customer-visible impact | What customers or operators experience, without raw payloads |
| Proposed scope | Smallest implementation brief that could address the pattern |
| Owner | Human owner for triage, not an auto-assignee |
| Priority | Human-reviewed priority |
| Next action | Clarify, design, implement, defer, or close |

## Review Command

```powershell
cd backend
python scripts/d9_4_improvement_backlog_check.py
python scripts/d9_operating_loop_kickoff_check.py
python scripts/d9_operating_records_check.py
```

## Record Template

Use a canonical redacted record name such as `docs/records/d9_improvement_backlog_YYYYMMDD.md`.

```markdown
# D9 Improvement Backlog - YYYY-MM-DD

Loop: Improvement backlog
Evidence source: redacted summary only
Owner: TBD
Status: open

## Candidates

| Source loop | Evidence summary | Customer-visible impact | Proposed scope | Owner | Priority | Next action |
|---|---|---|---|---|---|---|
| D9.1 / D9.2 / D9.3 |  |  |  | TBD | TBD | clarify |

## Safety

- No automatic ticket creation, customer reply, supplier notification, or product change triggered.
- No automatic pricing, product, quote, order, shipment, payment, inventory, or partner-selection mutation triggered.
- No tokens, raw response bodies, customer files, internal cost, margin, supplier private note, backend path, storage key, database URL, or secret included.
```

## Boundaries

- No `.env`, token value, bearer header, cookie, raw header, raw response body, customer file, upload, `local_data`, or `backend/storage` artifact may be committed.
- No automatic ticket creation, email, webhook, carrier API, customer notification, supplier notification, pricing mutation, product mutation, quote mutation, order mutation, shipment mutation, payment action, inventory reservation, partner-selection mutation, nginx edit, cloud upstream edit, or `service.intelli-opus.com` deployment is authorized by D9.4.
- Internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, token, database URL, and secret values remain excluded from D9 records and customer-facing artifacts.
