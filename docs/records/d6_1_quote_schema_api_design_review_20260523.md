# D6.1 Quote Schema & API Design Review Record

**Date:** 2026-05-23 · **Branch:** `master` · **Stage:** D6.1 (design only)

## Decision

**D6.1 design review is complete.** No database migration, no model code, no live Quote API was implemented in this stage.

## Scope Completed

1. Reviewed D5 Quote Input Contract as Phase 2 intake boundary
2. Distinguished **Customer Quote** (new) from existing **Partner Quotation** (`quotations` table)
3. Proposed schema: `customer_quotes`, `customer_quote_lines`, `customer_quote_versions`, `customer_quote_send_events`
4. Referenced D6.2 catalog/pricing tables: SKU, price tiers, exchange rates
5. Defined status lifecycle and no-price-less-quote gate
6. Proposed `/api/v1/quotes/*` API surface (v1 envelope)
7. Documented pricing rules: catalog, cost model, price list, manual, pricing engine — **no AI**
8. Documented safety: human send, human convert, no auto-promises
9. Mapped Phase 2 sub-roadmap D6.1–D6.6

## Key Design Outcomes

| Topic | Outcome |
|---|---|
| Naming | Customer Quote vs Partner Quotation |
| Multi-partner | Line-level `manufacturing_partner_id`; partners equal |
| Creation gate | D5 `ready_for_phase2_quote_draft` + priced lines |
| API namespace | `/api/v1/quotes/*` |
| Currency | USD sell, RMB cost, daily USD/CNY snapshot |
| Incoterms | FOB, EXW, DDP (MVP) |

## Validation

This stage is documentation-only. Existing regression baseline unchanged:

| Check | Result |
|---|---|
| `python -m pytest -q` | 266 passed, 1 skipped |
| No schema migration | Confirmed |
| No new API routes | Confirmed |
| No code changes to quote/pricing logic | Confirmed |

## Safety Confirmation

- no automatic sending introduced
- no quote record created in DB
- no pricing engine implemented
- no AI pricing endpoints designed
- no schema migration applied

## Next Step

**D6.2 Product Catalog & Pricing Foundation** — implement SKU, price tiers, exchange rates after design approval.

## Final Judgment

**A. D6.1 is complete; proceed to D6.2 planning/implementation when authorized.**

## Documents Produced

- [D6.1 Quote Schema & API Design Review](../phase2/d6_1_quote_schema_api_design_review.md)
- [Phase 2 Roadmap](../phase2/phase2_roadmap.md)
