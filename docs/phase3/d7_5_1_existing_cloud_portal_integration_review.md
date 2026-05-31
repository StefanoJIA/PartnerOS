# D7.5.1 Existing Cloud Portal Integration Review

**Status:** Review retained and refreshed for current D7.6-D7.9 implementation state.
**Date:** 2026-05-30.
**Alembic head:** `0017_order_resources`.

## Goal

Confirm how the existing customer-facing cloud portal should integrate with PartnerOS without rebuilding the portal UI in this repository.

PartnerOS remains the internal source of truth for quote, order, production, shipment, feedback, and resource metadata. The existing cloud portal, expected at `service.intelli-opus.com` or an equivalent deployed customer domain, is retained as the customer-facing portal and should consume carefully filtered PartnerOS bridge APIs.

This review does not deploy the cloud portal, change nginx, create portal sessions, send notifications, call carrier APIs, or expose internal cost and supplier-private fields.

## Existing Cloud Portal Capabilities

| Cloud portal capability | Current understanding | PartnerOS role |
|---|---|---|
| Product selection | Customer-facing browse and product selection UI exists outside this repository | Provide published product catalog data through whitelisted APIs |
| Quote and price display | Customer side may display accepted quote artifacts | Provide customer-visible quote summaries and PDFs only |
| Order tracking | Customer side needs order state and progress | Provide customer-visible order status and production milestones |
| Logistics / shipment tracking | Customer side needs ETD, ETA, carrier, and tracking reference | Provide D7.6 shipment plans through the D7.7 portal bridge |
| Feedback | Customer side needs feedback intake | Provide D7.7+ feedback ticket intake without auto-reply or notifications |
| Resource download | Customer side needs document/resource listing | Provide D7.9 resource metadata and safe download references |
| Customer account / access | Auth is owned by the portal integration boundary | PartnerOS validates bridge tokens; it does not store portal passwords |

Repository search still shows no source code or deployment configuration for the external cloud portal. The correct integration model is therefore bridge API consumption, not a rewrite of the customer portal inside PartnerOS.

## Current PartnerOS Capabilities

| Domain | Current state | Source of truth |
|---|---|---|
| Product catalog | Implemented | `product_catalog`, `product_price_tiers` |
| Quote | Implemented | `quotes`, `quote_line_items`, `quote_pdf_exports` |
| Customer order | Implemented | `customer_orders`, `order_line_items` |
| Customer confirmation | Implemented | `order_confirmations` |
| Partner split | Implemented | `order_partner_splits` |
| Supplier confirmation | Implemented | `supplier_confirmations` |
| Production milestones | Implemented | `order_production_milestones` |
| Shipment tracking | Implemented in D7.6 | `shipment_plans`, `shipment_tracking_events` |
| Customer portal API | Implemented in D7.7 | `/api/v1/portal/customer/*` read APIs and feedback intake |
| Feedback tickets | Implemented in D7.7/D7.8 | `feedback_tickets` |
| Resource center | Implemented in D7.9 | order resources and customer-visible resource DTOs |

## Mapping Table

| Cloud portal capability | PartnerOS source of truth | Integration direction |
|---|---|---|
| Product selection | `product_catalog`, `product_price_tiers` | Portal reads published SKU data; PartnerOS remains the product data source |
| Quote / price display | `quotes`, `quote_line_items`, `quote_pdf_exports` | Portal displays customer-visible quote summaries and approved PDFs; no margin or cost exposure |
| Order tracking | `customer_orders`, `order_line_items`, `order_confirmations` | Portal reads order number, customer-visible status, and visible line items |
| Production progress | `order_production_milestones` | Portal reads milestone labels and statuses; no supplier notes |
| Shipment tracking | `shipment_plans`, `shipment_tracking_events` | Portal reads ETD, ETA, carrier, tracking reference, and customer-visible shipment status maintained by Operators |
| Feedback | `feedback_tickets` | Portal POST creates a PartnerOS ticket; no auto-reply, email, webhook, or promise of resolution time |
| Resource download | order resources, quote PDFs, customer-visible document metadata | Portal lists safe customer-visible resources; storage paths and private files remain hidden |
| Customer account | Portal auth boundary plus PartnerOS bridge token validation | PartnerOS does not store portal passwords or session state |
| Lead intelligence | existing internal `/api/v1/portal/summary` family | Remains internal; do not mix lead intelligence with customer order portal APIs |

## Recommended Architecture

```text
Existing Cloud Customer Portal
  product selection / order tracking / shipment / feedback / resources
        |
        | HTTPS bridge with scoped token
        v
PartnerOS Portal API Layer
  /api/v1/portal/customer/*
  field whitelist DTOs
  no cost, margin, supplier-private notes, storage paths, or tokens
        |
        v
PartnerOS Internal Source of Truth
  products -> quotes -> orders -> production -> shipment -> feedback -> resources
```

## API Boundary

The D7.7-D7.9 bridge route family is implemented as PartnerOS server-side APIs for the external portal to consume:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/portal/customer/products` | Customer-visible product list |
| GET | `/api/v1/portal/customer/orders` | Customer-visible order list |
| GET | `/api/v1/portal/customer/orders/{id}/status` | Customer-visible order status summary |
| GET | `/api/v1/portal/customer/orders/{id}/production` | Customer-visible production milestones |
| GET | `/api/v1/portal/customer/orders/{id}/shipment` | Customer-visible shipment summary from D7.6 shipment plans |
| POST | `/api/v1/portal/customer/feedback` | Feedback ticket intake |
| GET | `/api/v1/portal/customer/resources` | Customer-visible resource list |

Responses must keep safety fields explicit where relevant:

- `shipment_created = false` unless a human-created shipment plan exists.
- `supplier_notified = false`.
- `customer_notified = false`.
- `automatic_sending_enabled = false`.

## Safety Boundaries

- Do not expose internal cost, margin, pricing breakdowns, supplier private notes, backend file paths, raw storage paths, or tokens.
- Do not call carrier APIs.
- Do not create webhooks.
- Do not send email.
- Do not notify suppliers or customers automatically.
- Do not automatically change order status to `shipped` or `delivered`.
- Do not add `portal_customer_sessions` or store customer portal passwords in PartnerOS.
- Do not deploy or modify `service.intelli-opus.com` from this repository.

## Development Route

| Stage | Name | Current state |
|---|---|---|
| D7.6 | Shipment Tracking Foundation | Implemented |
| D7.7 | Customer Portal Bridge | Implemented |
| D7.8 | Service Portal Integration UAT / feedback hardening | Implemented locally; staging evidence still required |
| D7.9 | Resource Center | Implemented |
| D8 | Deployment and integration hardening | Ready for staging handoff, not staging validated |

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Two systems drift on visible status | Customer sees stale data | PartnerOS remains the single write source; portal reads bridge APIs and shows `updated_at` |
| Customer-visible field leakage | Trust and compliance issue | Strict DTO whitelists and bridge smoke tests |
| Manual shipment maintenance lags | Tracking delay | Operator-owned D7.6 shipment plan workflow |
| Feedback intake appears to promise support SLA | Misaligned customer expectations | Feedback tickets are intake only; no auto-reply or promised resolution time |
| Staging credentials are incomplete | Cannot prove live integration | Use D8 staging access request and strict evidence workflow |

## Final Judgment

**A. Existing cloud portal should be retained as customer-facing portal and integrated with PartnerOS as source of truth.**

Reasons:

1. The customer-facing portal already exists outside this repository.
2. PartnerOS has now implemented the internal order, production, shipment, feedback, and resource source-of-truth path.
3. The D7.7-D7.9 bridge APIs provide a safer integration route than rewriting the portal UI.
4. The integration boundary is clear: PartnerOS exposes customer-visible DTOs; the cloud portal owns customer presentation and access.
5. The remaining proof point is strict staging evidence with real private values, not more local architecture speculation.

## Validation

```powershell
cd backend
python scripts/d7_5_1_portal_integration_review_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/d8_staging_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
python scripts/project_execution_status.py
```
