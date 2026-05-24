# D7.3 Customer Confirmation Flow

**Status:** Implemented · **Date:** 2026-05-24 · **Migration:** `0011_order_confirmations`

## Goal

Structured recording of customer order confirmation evidence without notifying suppliers, starting production, or creating shipments.

## Scope

- `order_confirmations` table
- Confirmation type / strength mapping
- Add confirmation (`POST .../confirm-customer`)
- List confirmations (`GET .../confirmations`)
- Void confirmation (`POST .../confirmations/{id}/void`)
- Order status `pending_customer_confirmation` → `confirmed`
- Order timeline confirmation events
- Frontend Customer Confirmations section on `/orders/:id`

## Not in Scope

- Supplier confirmation
- Production milestones
- Shipment tracking
- Payment / invoice
- Customer portal
- Real attachment upload (evidence fields only)

## Confirmation Types

| Type | Strength |
|---|---|
| purchase_order | strong |
| signed_quote | strong |
| email | medium |
| verbal | weak |
| internal_note | weak |
| other | weak |

## Safety

- No supplier notification
- No production start
- No shipment creation
- No inventory / certification / lead-time promise
- `payment_received=false` always

## Acceptance Criteria

- [x] Confirmation can be recorded with metadata
- [x] Order status updates from pending to confirmed
- [x] Multiple confirmations per order supported
- [x] Void marks confirmation inactive without deleting
- [x] Timeline includes add/void events
- [x] `d7_3_customer_confirmation_check.py` PASS

## References

- [D7.2 Order CRUD MVP](d7_2_order_crud_mvp.md)
- [Phase 3 Roadmap](phase3_roadmap.md)
