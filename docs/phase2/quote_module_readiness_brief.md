# Phase 2 Quote Module Readiness Brief

**Status:** Design preparation only · **Not implemented** · **Date:** 2026-05-23

This document defines how Phase 2 Quote should start. **Do not implement Phase 2 in the D5 closure branch.**

## Why Phase 2 Can Start Later

D5 has produced **Quote Input Contract** as the boundary object between customer development and formal quoting. Operators can:

- Classify product fit and opportunity
- Prepare pre-quote questions and outreach
- Generate soft quote handoff briefs
- Export a structured **Quote Input Contract** (JSON + summary)

No quote record, pricing, or customer commitment exists until Phase 2 is explicitly authorized and designed.

## Phase 2 Should Consume

From D5 Quote Input Contract (`GET /api/a-domain/leads/{lead_id}/quote-input-contract`):

| Field group | Contents |
|---|---|
| Identity | `lead_id`, `company_name` |
| Contact | `quote_input_fields.customer` (name, contact method availability) |
| Routing | `recommended_partner_route`, `recommended_product_scope` |
| Intent | `quote_input_fields.product_intent` |
| Requirements | `quote_input_fields.known_requirements`, `missing_requirements` |
| Questions | `quote_input_fields.recommended_questions` |
| Supplier prep | `quote_input_fields.supplier_preparation_notes` |
| Readiness | `quote_module_readiness`, `handoff_status` |
| Safety | `safety` flags (must remain false at handoff) |
| Copyable payload | `copyable_json`, `copyable_handoff_summary` |

Phase 2 Quote draft creation should **validate** that safety flags are false and that required customer fields are confirmed before any price field is editable.

## Phase 2 Should Add

- **Quote record** — persistent entity linked to lead/company
- **Quote line items** — product/SKU rows with quantity and pricing fields
- **SKU / product catalog** — structured product reference (not present in D5)
- **Partner route** — confirmed manufacturing partner assignment
- **Pricing fields** — unit price, extended price, currency, margin
- **Discount / margin** — commercial terms
- **Validity date** — quote expiration
- **PDF export** — customer-facing document
- **Quote status** — draft / internal review / sent / accepted / expired
- **Approval flow** — internal sign-off before customer release
- **Customer-facing version** — sanitized export separate from internal notes

## Phase 2 Must Not Assume

At contract handoff from D5, Phase 2 must **not** assume:

- Price is known
- Inventory is available
- Certification is confirmed
- Delivery time is confirmed
- Customer has approved quantity
- Supplier has approved specs

D5 `known_requirements` may contain nulls by design. Phase 2 must treat missing fields as **blocking for customer-facing quote**, not auto-fill with guesses.

## Recommended Phase 2 Start

**D6.1 Quote Schema & API Design Review**

Suggested agenda (design only):

1. Review Quote Input Contract schema and sample payloads from UAT leads
2. Define quote / quote_line_item tables and status enum
3. Define product catalog / SKU minimum viable structure
4. Define pricing source (manual entry vs partner price list)
5. Define PDF template requirements
6. Define approval roles and audit requirements
7. Confirm safety boundary: no auto-send, no auto-pricing from D5 derived fields

**Do not implement Phase 2 in this branch yet.**

## D6.1 Status

**D6.1 Quote Schema & API Design Review — complete (2026-05-23).**

Design documents (no implementation):

- [D6.1 Quote Schema & API Design Review](d6_1_quote_schema_api_design_review.md)
- [Phase 2 Roadmap](phase2_roadmap.md)
- [D6.1 Closure Record](../records/d6_1_quote_schema_api_design_review_20260523.md)

**Next implementation stage:** D6.2 Product Catalog & Pricing Foundation (when authorized).

## Prerequisites Before Implementation

- [ ] D5 Final Release accepted and regression baseline recorded
- [x] Product catalog / SKU design reviewed (D6.1 design — see [d6_1_quote_schema_api_design_review.md](d6_1_quote_schema_api_design_review.md))
- [ ] Quote PDF and approval workflow agreed (D6.4 / D6.5 design in roadmap)
- [ ] Production `SECRET_KEY`, `PUBLIC_BASE_URL`, HTTPS ready (if deploying)
- [ ] Explicit user authorization to enter Phase 2 development

## Related Documents

- [D5 Final MVP Release](../releases/d5_final_mvp_release_20260523.md)
- [D5 Capability Map](../architecture/d5_capability_map.md)
- [D5.19 UAT Record](../records/d5_19_soft_quote_handoff_uat_quote_input_contract_20260523.md)
