# D7.5 Production Milestone Foundation

**Status:** Implemented · **Date:** 2026-05-24 · **Migration:** `0013_prod_milestones`

## Goal

基于 partner split 建立生产里程碑跟踪，但不创建 shipment、不承诺交期。

## Scope

- `order_production_milestones` (customer order scoped)
- milestone templates
- ensure milestones
- list milestones
- update milestone status
- production summary
- order timeline production events

## Not in Scope

- shipment tracking
- shipment booking
- supplier auto notification
- customer auto notification
- payment
- invoice

## Milestone Templates

- lifting system / HOSUN
- education furniture / JOOBOO
- generic project supply
- fallback

## Safety

- milestones are internal planning/tracking records
- no automatic notification
- no shipment creation
- no lead time guarantee
- ready_to_ship does not mean shipment created

## Acceptance Criteria

- milestones can be generated
- milestones can be updated
- timeline updates
- safety flags correct
- tests pass

## Smoke

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/d7_5_production_milestone_check.py
```
