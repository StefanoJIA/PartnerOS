# D6 Quote Capability Map

**Status:** D6 closed · **Date:** 2026-05-23 · **Alembic head:** `0009_quote_send_tracking`

This map indexes D6 Customer Quote MVP capabilities by domain, primary API, UI, and persistence.

| Capability | Domain | Main API | Main UI | DB | Status |
|---|---|---|---|---|---|
| Product Catalog | Pricing / Catalog | `GET/POST /api/v1/products`, `GET /api/v1/products/{id}` | `/quote-catalog` · QuoteCatalogPage | `product_catalog`, tiers | **Closed** · read/write |
| Partner Management / Partner Extension | Partners | Partner via product `partner_id`; seed/import scripts | Catalog filters | `manufacturing_partners` | **Closed** · read (D6) |
| FX Rates | Pricing | `GET /api/v1/fx-rates/latest`, `POST /api/v1/fx-rates` | N/A (API/seed) | `fx_rates` | **Closed** · read/write |
| Pricing Preview | Pricing | `POST /api/v1/quotes/pricing/preview` | `/pricing-preview` · PricingPreviewPage | derived (no quote) | **Closed** · read-only preview |
| Excel Pricing Import | Pricing | CLI: `import_pricing_excel.py` | N/A | `product_catalog`, cost/price tiers | **Closed** · write via import |
| Quote CRUD | Customer Quote | `GET/POST /api/v1/quotes`, `GET/PATCH /api/v1/quotes/{id}`, `POST .../from-contract` | `/quotes`, `/quotes/new`, `/quotes/:id` | `quotes` | **Closed** · read/write |
| Quote Line Items | Customer Quote | `POST /api/v1/quotes/{id}/line-items` | Quote detail / new builder | `quote_line_items` | **Closed** · read/write |
| Quote Adjustments | Customer Quote | `POST/PATCH/DELETE .../adjustments` | Quote detail | `quote_adjustments` | **Closed** · read/write |
| Quote Totals | Customer Quote | Derived on quote; `POST .../recalculate` | Quote detail | `quotes` totals columns | **Closed** · computed |
| Quote Versioning | Customer Quote | `GET/POST /api/v1/quotes/{id}/versions` | Quote detail (versions count) | `quote_versions` | **Closed** · read/write |
| PDF Export | Customer Quote | `POST .../export-pdf`, `GET .../pdf-exports`, `GET .../download` | `/quotes/:id` PDF section | `quote_pdf_exports` + local storage | **Closed** · write metadata |
| Delivery Log | Customer Quote | `POST .../mark-sent`, `GET .../delivery-logs`, `GET .../delivery-due` | `/quotes/:id` delivery form | `quote_delivery_logs` | **Closed** · read/write |
| Quote Timeline | Customer Quote | `GET /api/v1/quotes/{id}/timeline` | `/quotes/:id` timeline | derived | **Closed** · read-only |
| Order Readiness | Customer Quote → D7 handoff | `GET .../order-readiness`, `GET .../order-readiness-board` | `/quotes/:id` readiness | derived (no order table) | **Closed** · read-only |

## Supporting APIs

| API | Purpose |
|---|---|
| `POST /api/v1/quotes/{id}/mark-ready` | Move quote to ready_to_send |
| `POST /api/v1/quotes/{id}/mark-expired` | Mark quote expired |
| `GET /health`, `GET /api/v1/system/readiness` | Backend health |

## D6 to D7 Boundary

### D6 (closed)

- Product catalog and pricing foundation
- Quote records, line items, adjustments, totals
- Quote versioning
- Customer PDF export (manual delivery outside system)
- Manual send tracking and delivery logs
- Quote timeline
- Quote-to-order readiness check and **Order Input Contract** (derived payload)

**D6 does not create orders.**

D6 only produces Order Input Contract through Quote-to-Order Readiness.

### D7 (not started)

- Order records and order line items
- Order confirmation workflow
- Customer confirmation tracking
- Supplier / partner confirmation
- Production milestones
- Shipment tracking
- Payment / invoice (future)
- Customer-facing order status (future)

## Safety (all D6 quote APIs)

- `automatic_sending_enabled=false`
- `order_created=false`
- `production_started=false`
- `shipment_created=false`
- No inventory / certification / lead-time promises in customer-facing outputs

## References

- [D6 Final Release](../releases/d6_final_quote_mvp_release_20260523.md)
- [D7 Readiness Brief](../phase3/d7_order_module_readiness_brief.md)
- [Phase 2 Roadmap](../phase2/phase2_roadmap.md)
