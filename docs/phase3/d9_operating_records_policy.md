# D9 Operating Records Policy

**Status:** planned on 2026-05-30.

## Purpose

D9 records preserve post-launch operating evidence without storing secrets, raw API payloads, customer files, internal cost, supplier private notes, or deployment instructions.

Use [D9 Operating Execution Pack](d9_operating_execution_pack.md) and [D9 Operating Loop Kickoff](d9_operating_loop_kickoff.md) before creating the first D9 operating review record.

Use [D9.1 Operating Health Review](d9_1_operating_health_review.md) for the `d9_operating_health_YYYYMMDD.md` signal set.

Use [D9.2 Order Operations Loop](d9_2_order_operations_loop.md) for the `d9_order_operations_YYYYMMDD.md` signal set.

Use [D9.3 Market Response Loop](d9_3_market_response_loop.md) for the `d9_market_response_YYYYMMDD.md` signal set.

Use [D9.4 Improvement Backlog](d9_4_improvement_backlog.md) for the `d9_improvement_backlog_YYYYMMDD.md` signal set.

Use `docs/records` only for redacted summaries. Do not store `.env`, raw response bodies, screenshots containing tokens, uploads, `local_data`, or files from `backend/storage`.

## Canonical Names

| D9 loop | Path |
|---|---|
| Aggregate operating review | `docs/records/d9_operating_review_YYYYMMDD.md` |
| Operating health | `docs/records/d9_operating_health_YYYYMMDD.md` |
| Order operations | `docs/records/d9_order_operations_YYYYMMDD.md` |
| Market response | `docs/records/d9_market_response_YYYYMMDD.md` |
| Improvement backlog | `docs/records/d9_improvement_backlog_YYYYMMDD.md` |

## Record Gate

Run this before committing any D9 operating records:

```powershell
cd backend
python scripts/d9_operating_records_check.py
```

The check verifies canonical names, requires each committed D9 record to include the Safety section markers below, and scans D9 records for token assignments, internal cost/margin markers, storage paths, local data paths, backend secrets, and raw response body markers.

## Template

`Owner: TBD` is allowed only as a human owner placeholder before production coordination assigns a named operator or team. It is not an auto-assignee, notification target, or permission to create tickets.

```markdown
# D9 Operating Review - YYYY-MM-DD

Loop: Operating health | Order operations | Market response | Improvement backlog
Evidence source: redacted summary only
Owner: TBD
Status: open

## Signals

- Signal:
- Evidence:
- Customer-visible impact:
- Operator action:

## Follow-Up

- Owner:
- Next action:
- Due:

## Safety

- No tokens or raw response bodies included.
- No internal cost, margin, supplier private note, backend path, storage key, database URL, or secret included.
- No automatic customer/supplier notification or business-status mutation triggered.
```
