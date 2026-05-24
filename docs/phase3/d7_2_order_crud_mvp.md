# D7.2 Order CRUD MVP

**Status:** Implemented · **Date:** 2026-05-23 · **Migration:** `0010_order_crud_mvp`

## Goal

Create **customer orders** manually from **sent quotes** using the D6 Order Input Contract — without starting production, shipment, or supplier notification.

## Scope

- `customer_orders` table
- `order_line_items` table
- `POST /api/v1/orders/from-quote`
- Order list, detail, patch, cancel
- Customer confirmation (`pending_customer_confirmation` → `confirmed`)
- Order timeline
- Frontend `/orders`, `/orders/:id`
- Create Order entry on quote detail (manual only)

## Not in Scope

- Supplier confirmation
- Partner splits
- Production milestones
- Shipment tracking
- Payment / invoice
- Customer portal
- Auto order creation from quote send

## Safety

- Order creation sets `order_created=true` on order payloads only
- `production_started=false`, `shipment_created=false`, `supplier_notified=false`
- No inventory / certification / lead-time promises
- Quote readiness API still reports `order_created=false` (quote domain)

## Business Rules

1. One **active** order per quote (`status != cancelled`)
2. Quote must be **sent**, not **expired**, with line items and `grand_total > 0`
3. Quote must pass readiness (no blocking items)
4. Without customer confirmation → `pending_customer_confirmation`
5. With customer confirmation → `confirmed`

## Acceptance Criteria

- [x] Order created from sent quote
- [x] Line items inherit quote line snapshot
- [x] Duplicate active order returns 409
- [x] Confirm customer and cancel work
- [x] Timeline shows order_created / customer_confirmed / order_cancelled
- [x] `d7_2_order_crud_check.py` PASS

## References

- [D7.1 Design Review](d7_1_order_schema_api_design_review.md)
- [Phase 3 Roadmap](phase3_roadmap.md)
