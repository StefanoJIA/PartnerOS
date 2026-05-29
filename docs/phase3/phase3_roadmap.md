# Phase 3 Roadmap — Order / Production / Shipment

**Status:** D7.8 implemented · **D6 closed** · **Date:** 2026-05-29

Phase 3 builds the **Customer Order** module and downstream production/shipment foundations. D6 Quote MVP remains frozen.

---

## Principles

1. **Quote ≠ Order** — orders created manually from Order Input Contract
2. **Customer confirmation required** before supplier/production stages
3. **All partners equal** — multi-partner splits, no platform default factory
4. **No auto-send** — no email/LinkedIn/Outlook automation in D7 MVP
5. **No auto production / shipment / payment** — all explicit human actions
6. **Structured handoff** — consume D6 JSON contract, not PDF parsing

---

## Stages

| Stage | Name | Scope | Status |
|---|---|---|---|
| **D7.1** | Order Schema & API Design Review | Data model, lifecycle, API, permissions, safety | ✅ **Design complete** |
| **D7.2** | Order CRUD MVP | `customer_orders`, `order_line_items`, from-quote API, list/detail/cancel | ✅ **Implemented** |
| **D7.3** | Customer Confirmation Flow | `order_confirmations`, add/list/void, timeline | ✅ **Implemented** |
| **D7.4** | Partner Split & Supplier Confirmation | `order_partner_splits`, `supplier_confirmations` | ✅ **Implemented** |
| **D7.5** | Production Milestone Foundation | `order_production_milestones`, milestone API | ✅ **Implemented** |
| **D7.5.1** | Existing Cloud Portal Integration Review | Mapping, architecture, API boundary (no code) | ✅ **Review complete** |
| **D7.6** | Shipment Tracking Foundation | `shipment_plans`, shipment API | ✅ **Implemented** |
| **D7.7** | Customer Portal Bridge | `/api/v1/portal/customer/*` read API + auth, `feedback_tickets` MVP | ✅ **Implemented** |
| **D7.8** | Service Portal UAT & Feedback Operations | consumer contract pack, staging readiness, feedback console | ✅ **Implemented** |
| **D7.9** | Resource Center | Customer document catalog + signed download | Future |
| **D8** | Deployment & Integration Hardening | CORS, HTTPS, token rotation, cloud 联调 | Future |

---

## Dependency Graph

```mermaid
flowchart TD
  D6[D6 Closed · Order Input Contract]
  D71[D7.1 Design Review]
  D72[D7.2 Order CRUD MVP]
  D73[D7.3 Customer Confirmation]
  D74[D7.4 Partner Split & Supplier]
  D75[D7.5 Production Milestones]
  D751[D7.5.1 Cloud Portal Review]
  D76[D7.6 Shipment Tracking]
  D77[D7.7 Portal Bridge]
  D78[D7.8 Feedback]
  D79[D7.9 Resource Center]
  D8[D8 Integration Hardening]

  D6 --> D71
  D71 --> D72
  D72 --> D73
  D73 --> D74
  D74 --> D75
  D75 --> D751
  D751 --> D76
  D76 --> D77
  D77 --> D78
  D78 --> D79
  D79 --> D8
```

---

## D7.2 MVP Checklist

- [x] Migration: `customer_orders`, `order_line_items`
- [x] `POST /api/v1/orders/from-quote`
- [x] Order list, detail, patch, cancel
- [x] Order timeline
- [x] Source quote linkage (read-only)
- [x] Safety flags on all responses
- [x] Frontend `/orders` pages
- [x] No production / shipment / payment

---

## Out of Scope (Phase 3 MVP)

- Automatic email / LinkedIn / Outlook
- Payment processing
- Invoice generation
- Customer portal UI replacement (retain existing cloud portal UI)
- Inventory reservation system
- Factory MES integration
- PDF parsing for order creation

---

## Related Documents

- [D7.5.1 Existing Cloud Portal Integration Review](d7_5_1_existing_cloud_portal_integration_review.md)
- [D7.6 Shipment Tracking Foundation](d7_6_shipment_tracking_foundation.md)
- [D7.7 Customer Portal Bridge API](d7_7_customer_portal_bridge_api.md)
- [D7.2 Order CRUD MVP](d7_2_order_crud_mvp.md)
- [D7.1 Order Schema & API Design Review](d7_1_order_schema_api_design_review.md)
- [D7 Order Module Readiness Brief](d7_order_module_readiness_brief.md)
- [D6 Final Release](../releases/d6_final_quote_mvp_release_20260523.md)
- [D6 Capability Map](../architecture/d6_quote_capability_map.md)
- [Phase 2 Roadmap](../phase2/phase2_roadmap.md)
