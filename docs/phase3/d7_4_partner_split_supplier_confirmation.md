# D7.4 Partner Split & Supplier Confirmation

**Status:** Implemented · **Date:** 2026-05-24 · **Migration:** `0012_partner_supplier`

## Goal

将 customer order 按 partner 拆分，并手动记录 supplier confirmation，但不启动 production / shipment。

## Scope

- `order_partner_splits`
- `supplier_confirmations`
- ensure partner splits
- add supplier confirmation
- void supplier confirmation
- partner split summary
- order timeline supplier events

## Not in Scope

- production milestones
- shipment tracking
- supplier auto notification
- payment
- invoice
- customer portal

## Partner Split Rules

- one split per partner per order
- HOSUN / JOOBOO / future partners are equal
- split is internal execution unit, not purchase order

## Supplier Confirmation Rules

- manual only
- no automatic notification
- does not start production
- does not create shipment
- inventory / certification / lead time are false unless explicitly recorded

## Safety

- no supplier notification
- no production start
- no shipment creation
- no inventory / certification / lead-time promise unless manually recorded

## Acceptance Criteria

- partner splits can be generated
- supplier confirmation can be recorded
- timeline updates
- safety flags correct
- tests pass

## Smoke

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8013"
python scripts/d7_4_partner_supplier_check.py
```
