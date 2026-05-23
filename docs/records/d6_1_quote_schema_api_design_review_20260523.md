# D6.1 Quote Schema & API Design Review Record

**Date:** 2026-05-23 · **Branch:** `master` · **Stage:** D6.1 (design only)

## Decision

**D6.1 design review is complete.** Expanded design incorporates Excel pricing workbook logic, full data model, API surface, permissions, PDF structure, and safety boundaries. **No migration, no Quote API, no pricing engine implementation.**

## Scope Completed

1. Business decisions and partner equality rules
2. Excel model extraction: Cost Model, Price List, Margin Strategy, Quote template, Profit calculator
3. Proposed tables: product_catalog, product_cost_models, product_price_tiers, margin_strategy_tiers, fx_rates, quotes, quote_versions, quote_line_items, quote_adjustments, quote_terms, quote_pdf_exports
4. Partner mapping to existing `manufacturing_partners` (extensions only)
5. Product attributes JSON (lifting + education)
6. Pricing service interface design (`calculate_line_price`)
7. Quote lifecycle without draft status
8. Version types: partner_specific, combined, revised
9. PDF data model (IntelliOffice header, customer/partner/internal views)
10. `/api/v1/*` API design (products, fx, quotes, pricing)
11. Permission matrix (admin, sales_manager, sales, operator, viewer)
12. `d6_1_design_readiness_check.py` documentation gate

## Key Design Outcomes

| Topic | Outcome |
|---|---|
| Excel → system | DB tables + pricing service, not spreadsheet formulas |
| Table naming | `quotes` (Customer Quote) vs `quotations` (Partner Quotation) |
| No draft | Create requires priced lines → `ready_to_send` or `internal_review` |
| Adjustments | `quote_adjustments` table (discount, shipping, sample_fee, tax) |
| FX | Daily USD/CNY + snapshot on quote |
| Multi-partner | Lines bind partner_id; combined/partner-specific versions |

## Validation

| Check | Result |
|---|---|
| `python scripts/d6_1_design_readiness_check.py` | PASS |
| `python -m pytest -q` | 266 passed, 1 skipped |
| No new Alembic migration | Confirmed (0005 head) |
| No Quote API in app code | Confirmed |

## Safety Confirmation

- no AI pricing in design
- no automatic sending
- no quote table created
- no schema migration
- no price generation at runtime

## Next Step

**D6.2 Product Catalog & Pricing Foundation** — implement catalog, tiers, FX, cost models, pricing service tests.

## Final Judgment

**A. D6.1 design review is complete and ready for D6.2 Quote MVP planning.**

## Documents

- [D6.1 Quote Schema & API Design Review](../phase2/d6_1_quote_schema_api_design_review.md)
- [Phase 2 Roadmap](../phase2/phase2_roadmap.md)
