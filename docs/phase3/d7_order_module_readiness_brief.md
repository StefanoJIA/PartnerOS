# D7 Order Module Readiness Brief

**Status:** Design preparation only · **Date:** 2026-05-23 · **Do not implement D7 in D6 branch**

## Why D7 Can Start Later

D6 has closed as a Quote MVP. The **Quote-to-Order Readiness Gate** (D6.6) produces a structured **Order Input Contract** from sent quotes without creating any order record. D7 can consume this contract when order schema, supplier confirmation, production, and shipment boundaries are reviewed.

## D7 Should Consume

From D6 readiness / order input contract:

- `quote_id`
- `quote_number`
- `quote_version_id`
- `pdf_export_id`
- `delivery_log_id`
- `company_id`
- `contact_id`
- `bill_to` (name, company, address)
- `ship_to` (name, company, address)
- `quote_line_items` (partner, product, qty, price, incoterm, attributes)
- `partner_routes` (multi-partner split hints)
- `totals` (subtotal, adjustments, grand_total, currency)
- `payment_terms`
- `shipping_terms`
- `order_readiness` checklist (blocking / warning items)
- full `order_input_contract` JSON

## D7 Should Add

- Order record (new table — not in D6)
- Order line items linked to quote lines
- Order status lifecycle
- Customer confirmation (explicit recorded action)
- Supplier / partner confirmation
- Payment status (future)
- Production milestones
- Shipment tracking
- Invoice (future)
- Customer-facing order status portal (future)

## D7 Must Not Assume

- Customer has confirmed the order unless explicitly recorded in D7
- Inventory is available
- Supplier has confirmed production
- Certification is confirmed
- Lead time is confirmed
- Shipment is booked
- Payment is received
- Production has started

All fulfillment assumptions require explicit confirmation in D7+ modules.

## Recommended D7 Start

**D7.1 Order Schema & API Design Review**

- Define order vs quote vs RFQ `quotations` boundary
- Define customer confirmation model
- Define partner split / multi-factory routing
- Define production and shipment milestone schema (design only)
- **Do not implement** in the D6 closure branch

## D7 Suggested Roadmap

| Stage | Name | Scope |
|---|---|---|
| D7.1 | Order Schema & API Design Review | Design only |
| D7.2 | Order CRUD MVP | Order records from readiness contract |
| D7.3 | Order Line Items from Quote | Line mapping, partner binding |
| D7.4 | Supplier Confirmation / Partner Split | Per-partner acknowledgment |
| D7.5 | Production Milestone Planning | Internal milestones |
| D7.6 | Shipment Tracking Foundation | Shipment records |
| D7.7 | Customer Order Status View | Future portal |

## D6 Handoff Artifacts

- `GET /api/v1/quotes/{id}/order-readiness` — readiness + order input contract
- `GET /api/v1/quotes/order-readiness-board` — sent quote summary board
- [D6 Capability Map](../architecture/d6_quote_capability_map.md)
- [D6 Final Closure Record](../records/d6_final_closure_20260523.md)

## Safety Inheritance from D6

D7 must preserve:

- No automatic quote sending
- No automatic order creation from quote without human action
- No inventory / certification / lead-time promises unless explicitly confirmed in D7 workflows
