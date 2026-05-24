# D7.1 Order Schema & API Design Review

**Status:** Design review complete · **Not implemented** · **Date:** 2026-05-23  
**Phase:** 3 · **Stage:** D7.1  
**Prerequisite:** D6 closed · Order Input Contract available via `GET /api/v1/quotes/{id}/order-readiness`

---

## Business Decisions

| # | Rule |
|---|---|
| 1 | **Quote ≠ Order** — a sent quote is a commercial offer, not a binding order |
| 2 | **Sent Quote ≠ Order** — delivery log records quote sent, not customer acceptance |
| 3 | **Order must be created manually** — no auto-conversion from quote readiness |
| 4 | **Order must be based on customer confirmation** — explicit evidence required before supplier stage |
| 5 | **Order must trace to source quote** — `source_quote_id`, version, PDF export, delivery log |
| 6 | **Structured input only** — D7 consumes Order Input Contract JSON, **not PDF parsing** |
| 7 | **All partners equal** — HOSUN, JOOBOO, future factories via `partner_id`; no platform default |
| 8 | **Multi-partner orders** — one customer order may split into multiple partner execution splits |
| 9 | **Price snapshot** — order lines inherit quote line prices; reprice only via explicit human action |
| 10 | **No auto production** — supplier confirmation required before production planning |
| 11 | **No auto shipment** — shipment plans created manually in later stages |
| 12 | **No auto supplier notification** — no email/LinkedIn/Outlook in D7 MVP |
| 13 | **No payment assumption** — payment status is future scope; never auto-set to received |
| 14 | **Existing `quotations` unchanged** — RFQ supplier quotes remain separate from customer orders |
| 15 | **Order number format** — `O-YYYY-NNNN` (e.g. `O-2026-0001`) |

### Terminology

| Name | Proposed table | Meaning |
|---|---|---|
| **Customer Order** | `customer_orders` | Formal customer purchase order in D7 |
| **Customer Quote** | `quotes` (D6) | Commercial quote to customer |
| **Partner Quotation** | `quotations` (existing) | Supplier quote within RFQ workflow |
| **Partner Split** | `order_partner_splits` | Internal execution unit per manufacturing partner |
| **Order Input Contract** | derived (D6.6) | Structured JSON handoff from quote readiness |

---

## D6 Input Boundary

D7 order creation consumes the D6 **Order Input Contract** produced by `build_quote_order_readiness()`.

### Contract structure (from D6.6)

```json
{
  "customer": { "company_id", "company_name", "contact_id", "contact_name" },
  "billing": { "bill_to_name", "bill_to_company", "bill_to_address" },
  "shipping": { "ship_to_name", "ship_to_company", "ship_to_address" },
  "line_items": [{ "quote_line_item_id", "partner_id", "partner_name", "product_catalog_id", ... }],
  "partner_routes": [{ "partner_name", "line_item_ids" }],
  "totals": { "subtotal", "adjustments", "grand_total", "currency" },
  "terms": { "payment_terms", "shipping_terms", "valid_until" },
  "source_quote": { "quote_id", "quote_number", "quote_version_id", "pdf_export_id", "delivery_log_id" },
  "safety": { "order_created": false, "production_started": false, "shipment_created": false }
}
```

### Readiness gate fields (also consumed)

| Field | Use in D7 |
|---|---|
| `readiness_status` | Gate before `from-quote` API |
| `blocking_items` | Reject order creation if any blocking |
| `warning_items` | Allow creation with warnings logged |
| `checklist` | Audit trail on order creation |
| Quote timeline summary | Optional context on order timeline |

### Pre-conditions for `POST /api/v1/orders/from-quote`

1. Quote status = **`sent`**
2. Quote **not expired**
3. At least one **delivery log** exists
4. **Order readiness** result available (no unresolved blocking items for confirmed path)
5. Selected line items complete (product, qty, price, partner)
6. **Human actor** initiates creation

### Design decision: pending vs reject without confirmation

**Recommended (D7.2 MVP):**

| Scenario | Behavior |
|---|---|
| Customer confirmation provided at creation | Create order with status **`confirmed`** |
| No customer confirmation at creation | Create order with status **`pending_customer_confirmation`** — **cannot** advance to supplier stage |
| Blocking readiness items | **Reject** creation (HTTP 422) |
| Quote not sent / expired | **Reject** creation |

Rationale: sales may draft an order record while awaiting PO; supplier workflow remains locked until confirmation.

---

## Proposed Data Model

> **Design only.** No migration in D7.1. Tables below are proposed for D7.2+.

### A. `customer_orders`

**Purpose:** Primary customer order record; one row per customer purchase.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | PK |
| `order_number` | VARCHAR(32) | NO | Unique; format `O-YYYY-NNNN` |
| `source_quote_id` | UUID | NO | FK → `quotes.id` |
| `source_quote_version_id` | UUID | YES | FK → `quote_versions.id` |
| `source_pdf_export_id` | UUID | YES | FK → `quote_pdf_exports.id` |
| `source_delivery_log_id` | UUID | YES | FK → `quote_delivery_logs.id` |
| `company_id` | UUID | YES | FK → `companies.id` |
| `contact_id` | UUID | YES | FK → `contacts.id` |
| `status` | VARCHAR(48) | NO | See lifecycle |
| `order_date` | DATE | NO | Business order date |
| `customer_confirmed_at` | TIMESTAMPTZ | YES | Set when confirmation recorded |
| `customer_confirmation_method` | VARCHAR(32) | YES | email / purchase_order / signed_quote / verbal / internal_note / other |
| `bill_to_name` | VARCHAR(255) | YES | Snapshot from quote |
| `bill_to_company` | VARCHAR(255) | YES | |
| `bill_to_address` | TEXT | YES | |
| `ship_to_name` | VARCHAR(255) | YES | |
| `ship_to_company` | VARCHAR(255) | YES | |
| `ship_to_address` | TEXT | YES | |
| `currency` | VARCHAR(8) | NO | Default USD |
| `subtotal` | NUMERIC(14,2) | NO | From quote snapshot |
| `adjustment_total` | NUMERIC(14,2) | NO | |
| `tax_total` | NUMERIC(14,2) | YES | Future |
| `grand_total` | NUMERIC(14,2) | NO | |
| `payment_terms` | TEXT | YES | |
| `shipping_terms` | TEXT | YES | |
| `internal_notes` | TEXT | YES | |
| `customer_notes` | TEXT | YES | |
| `created_by` | UUID | YES | FK → users |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

**Relationships:** → `order_line_items`, `order_partner_splits`, `order_confirmations`, `supplier_confirmations`  
**Indexes:** `order_number` (unique), `source_quote_id`, `company_id`, `status`, `order_date`  
**Future scope:** payment_status, invoice_id, customer_portal_token

---

### B. `order_line_items`

**Purpose:** Line-level product snapshot linked to source quote line.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | PK |
| `order_id` | UUID | NO | FK → `customer_orders.id` |
| `source_quote_line_item_id` | UUID | NO | FK → `quote_line_items.id` |
| `partner_id` | UUID | NO | FK → `manufacturing_partners.id` |
| `product_catalog_id` | UUID | YES | FK → `product_catalog.id` |
| `internal_sku` | VARCHAR(64) | YES | |
| `partner_product_code` | VARCHAR(64) | YES | |
| `product_name` | VARCHAR(255) | NO | Snapshot |
| `product_category` | VARCHAR(128) | YES | |
| `description_customer` | TEXT | YES | |
| `description_internal` | TEXT | YES | |
| `quantity` | NUMERIC(12,3) | NO | |
| `uom` | VARCHAR(16) | YES | e.g. pcs, set |
| `unit_price` | NUMERIC(14,4) | NO | Inherited from quote |
| `total_price` | NUMERIC(14,2) | NO | |
| `currency` | VARCHAR(8) | NO | |
| `incoterm` | VARCHAR(16) | YES | |
| `color_finish` | VARCHAR(128) | YES | |
| `size_dimension` | VARCHAR(128) | YES | |
| `attributes_snapshot_json` | JSONB | YES | Full attribute freeze |
| `customer_visible` | BOOLEAN | NO | Default true |
| `supplier_visible` | BOOLEAN | NO | Default true |
| `status` | VARCHAR(32) | NO | active / cancelled / on_hold |
| `notes` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

**Rules:** inherit quote line snapshot; preserve `source_quote_line_item_id`; no auto-reprice  
**Indexes:** `order_id`, `partner_id`, `source_quote_line_item_id`

---

### C. `order_partner_splits`

**Purpose:** Split one customer order into per-partner internal execution units.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | PK |
| `order_id` | UUID | NO | FK → `customer_orders.id` |
| `partner_id` | UUID | NO | FK → `manufacturing_partners.id` |
| `split_status` | VARCHAR(32) | NO | draft / pending / active / completed / cancelled |
| `partner_reference_number` | VARCHAR(64) | YES | Partner PO ref |
| `supplier_confirmation_status` | VARCHAR(32) | NO | pending / confirmed / rejected |
| `supplier_confirmed_at` | TIMESTAMPTZ | YES | |
| `expected_production_start` | DATE | YES | Manual estimate only |
| `expected_ready_date` | DATE | YES | Manual estimate only |
| `notes` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

**Rules:** auto-created from `partner_routes` on order creation; all partners equal; connects to production milestones in D7.5  
**Indexes:** `order_id`, `partner_id`, unique `(order_id, partner_id)`

---

### D. `order_confirmations`

**Purpose:** Customer order confirmation evidence.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | PK |
| `order_id` | UUID | NO | FK → `customer_orders.id` |
| `confirmation_type` | VARCHAR(32) | NO | email / purchase_order / signed_quote / verbal / internal_note / other |
| `confirmed_by_name` | VARCHAR(255) | YES | |
| `confirmed_by_email` | VARCHAR(255) | YES | |
| `confirmed_at` | TIMESTAMPTZ | NO | |
| `source` | VARCHAR(64) | YES | e.g. customer_email, po_scan |
| `note` | TEXT | YES | |
| `attachment_reference` | VARCHAR(512) | YES | Future doc store ref |
| `created_at` | TIMESTAMPTZ | NO | |

**Rules:** D7 never assumes confirmation; `internal_note` allowed with system warning; multiple confirmations allowed (append-only log)

---

### E. `supplier_confirmations`

**Purpose:** Partner/supplier acknowledgment of product, qty, production, lead time.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | PK |
| `order_id` | UUID | NO | FK → `customer_orders.id` |
| `partner_id` | UUID | NO | FK → `manufacturing_partners.id` |
| `partner_split_id` | UUID | YES | FK → `order_partner_splits.id` |
| `confirmation_status` | VARCHAR(32) | NO | pending / confirmed / rejected / on_hold |
| `confirmed_at` | TIMESTAMPTZ | YES | |
| `confirmed_by` | VARCHAR(255) | YES | Internal user or partner contact name |
| `production_lead_time` | VARCHAR(128) | YES | Manual text — not a promise flag |
| `certification_confirmed` | BOOLEAN | NO | Default false; manual only |
| `inventory_confirmed` | BOOLEAN | NO | Default false; manual only |
| `notes` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | |

**Rules:** production planning locked until `confirmation_status=confirmed`; booleans require explicit human toggle

---

### F. `production_milestones` (D7.5 — design only)

**Purpose:** Internal production progress per order / partner split.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | PK |
| `order_id` | UUID | NO | FK |
| `partner_split_id` | UUID | YES | FK |
| `milestone_type` | VARCHAR(48) | NO | See milestone list |
| `planned_date` | DATE | YES | |
| `actual_date` | DATE | YES | |
| `status` | VARCHAR(32) | NO | pending / in_progress / completed / skipped |
| `notes` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | |

**Milestone types:** `order_received`, `supplier_confirmed`, `materials_prepared`, `production_started`, `assembly`, `quality_check`, `packed`, `ready_to_ship`

**D7.1 boundary:** schema designed; **not implemented** until D7.5

---

### G. `shipment_plans` (D7.6 — design only)

**Purpose:** Shipment planning and tracking foundation.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `id` | UUID | NO | PK |
| `order_id` | UUID | NO | FK |
| `partner_split_id` | UUID | YES | FK |
| `shipment_method` | VARCHAR(64) | YES | sea / air / express |
| `incoterm` | VARCHAR(16) | YES | |
| `origin` | VARCHAR(255) | YES | |
| `destination` | VARCHAR(255) | YES | |
| `estimated_ship_date` | DATE | YES | |
| `estimated_arrival_date` | DATE | YES | |
| `tracking_number` | VARCHAR(128) | YES | |
| `status` | VARCHAR(32) | NO | draft / planned / shipped / delivered / cancelled |
| `notes` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

**D7.1 boundary:** schema designed; **not implemented** until D7.6

---

### H. Activity & documents (optional)

| Resource | Approach |
|---|---|
| `order_activity_logs` | Reuse existing `activity_logs` with `entity_type=customer_order` |
| `order_documents` | Optional future table for PO scans, signed quotes; MVP may use `attachment_reference` on confirmations |

---

## Order Lifecycle

### Full status enum (planned)

```
pending_customer_confirmation → confirmed → internal_review → supplier_confirmation_pending
  → supplier_confirmed → production_pending → in_production → ready_to_ship
  → shipped → delivered

Branches: cancelled, on_hold (from most states with permission)
```

### D7.2 MVP minimum statuses

| Status | Meaning |
|---|---|
| `pending_customer_confirmation` | Order drafted; awaiting customer evidence |
| `confirmed` | Customer confirmation recorded |
| `internal_review` | Manual price / multi-partner review required |
| `supplier_confirmation_pending` | Awaiting partner acknowledgment |
| `supplier_confirmed` | All required splits confirmed |
| `production_pending` | Ready for production planning (D7.5) |
| `cancelled` | Order cancelled |

### Transition rules

| From | To | Condition |
|---|---|---|
| (create) | `pending_customer_confirmation` | No confirmation at creation |
| (create) | `confirmed` | Customer confirmation provided |
| (create) | `internal_review` | Readiness warnings (e.g. high discount, manual pricing) |
| `pending_customer_confirmation` | `confirmed` | `POST .../confirm-customer` |
| `confirmed` | `supplier_confirmation_pending` | Partner splits created |
| `supplier_confirmation_pending` | `supplier_confirmed` | All splits supplier-confirmed |
| `supplier_confirmed` | `production_pending` | Manual promotion (D7.5+) |
| any (permitted) | `cancelled` | admin / sales_manager |
| any | `on_hold` | admin / sales_manager / production_manager |

**Hard rules:**

1. Cannot enter `supplier_confirmation_pending` from `pending_customer_confirmation`
2. Cannot enter `production_pending` without `supplier_confirmed`
3. `production_started` milestone ≠ order status auto-change in D7.2

---

## Partner Split Model

### Creation logic (D7.2)

On order creation from quote:

1. Read `partner_routes` from Order Input Contract
2. For each distinct `partner_id` in selected line items, create one `order_partner_splits` row
3. Link line items to split via shared `partner_id`
4. Initial `split_status=draft`, `supplier_confirmation_status=pending`

### Multi-partner example

Quote with HOSUN lifting columns + JOOBOO desk frames → **one** `customer_orders` row, **two** `order_partner_splits`, lines grouped by partner.

### Merge / split adjustments (D7.4+)

- **Split:** rare — move lines to new split with audit log
- **Merge:** not in MVP — one order per quote conversion
- **Re-quote:** if major change, cancel order and create new quote (D7 policy)

---

## Customer Confirmation

### MVP flow

1. Operator obtains confirmation outside intelliOffice (email, PO, signed PDF)
2. Either:
   - **At creation:** include `customer_confirmation` in `from-quote` payload, or
   - **After creation:** `POST /api/v1/orders/{id}/confirm-customer`
3. System writes `order_confirmations` row and updates `customer_confirmed_at`

### Confirmation types

| Type | MVP support | Warning |
|---|---|---|
| `email` | Yes | — |
| `purchase_order` | Yes | — |
| `signed_quote` | Yes | — |
| `verbal` | Yes | System warning |
| `internal_note` | Yes | System warning — not customer-facing evidence |
| `other` | Yes | Requires note |

---

## Supplier Confirmation

### MVP flow (D7.4)

1. Order in `supplier_confirmation_pending`
2. production_manager / sales_manager records per-partner confirmation via API
3. Explicit toggles for `certification_confirmed`, `inventory_confirmed` — default **false**
4. `production_lead_time` is free text, not an automated promise

### Gate

All partner splits must have `supplier_confirmation_status=confirmed` before order → `supplier_confirmed`.

---

## Production Boundary

| In D7 scope | Stage | Notes |
|---|---|---|
| Order record + lines | D7.2 | Core MVP |
| Partner splits | D7.4 | Multi-factory routing |
| Supplier confirmation | D7.4 | Manual only |
| `production_pending` status | D7.2 | Status only — no shop floor |
| `production_milestones` table + API | D7.5 | First production tracking |
| Auto MES / factory integration | Future | Out of scope |

**D7.1 does not implement production.** Order status `production_pending` means "cleared for planning," not "production started."

---

## Shipment Boundary

| In D7 scope | Stage | Notes |
|---|---|---|
| `shipping_terms` snapshot on order | D7.2 | From quote |
| `ship_to` address on order | D7.2 | From quote |
| `shipment_plans` table + API | D7.6 | First shipment tracking |
| `shipped` / `delivered` order status | D7.6+ | After shipment plan exists |
| Carrier API integration | Future | Out of scope |
| Auto booking | **Never in MVP** | Manual only |

---

## API Design

> Design only. Routes marked **MVP** target D7.2–D7.4; **Future** target D7.5–D7.7.

### Orders

| Method | Path | Stage | Purpose |
|---|---|---|---|
| POST | `/api/v1/orders/from-quote` | **D7.2 MVP** | Create order from quote + contract |
| GET | `/api/v1/orders` | **D7.2 MVP** | List orders (filter by status, company) |
| GET | `/api/v1/orders/{id}` | **D7.2 MVP** | Order detail |
| PATCH | `/api/v1/orders/{id}` | **D7.2 MVP** | Update notes, addresses (not prices) |
| POST | `/api/v1/orders/{id}/confirm-customer` | **D7.3 MVP** | Record customer confirmation |
| POST | `/api/v1/orders/{id}/cancel` | **D7.2 MVP** | Cancel order |
| GET | `/api/v1/orders/{id}/timeline` | **D7.2 MVP** | Order event timeline |

### Order Lines

| Method | Path | Stage | Purpose |
|---|---|---|---|
| GET | `/api/v1/orders/{id}/line-items` | **D7.2 MVP** | List lines |
| PATCH | `/api/v1/orders/{id}/line-items/{line_id}` | **D7.3+** | Update notes, visibility; reprice = restricted |

### Partner Splits

| Method | Path | Stage | Purpose |
|---|---|---|---|
| GET | `/api/v1/orders/{id}/partner-splits` | **D7.4 MVP** | List splits |
| POST | `/api/v1/orders/{id}/partner-splits` | **D7.4 MVP** | Manual split adjustment |
| PATCH | `/api/v1/orders/{id}/partner-splits/{split_id}` | **D7.4 MVP** | Update split status, refs |

### Supplier Confirmation

| Method | Path | Stage | Purpose |
|---|---|---|---|
| POST | `/api/v1/orders/{id}/supplier-confirmations` | **D7.4 MVP** | Record supplier confirmation |
| GET | `/api/v1/orders/{id}/supplier-confirmations` | **D7.4 MVP** | List confirmations |

### Production (Future)

| Method | Path | Stage |
|---|---|---|
| GET | `/api/v1/orders/{id}/production-milestones` | D7.5 |
| POST | `/api/v1/orders/{id}/production-milestones` | D7.5 |

### Shipment (Future)

| Method | Path | Stage |
|---|---|---|
| GET | `/api/v1/orders/{id}/shipment-plans` | D7.6 |
| POST | `/api/v1/orders/{id}/shipment-plans` | D7.6 |

### `from-quote` request (D7.2)

```json
{
  "quote_id": "uuid",
  "quote_version_id": "uuid",
  "customer_confirmation": {
    "type": "email",
    "confirmed_at": "2026-05-23T10:00:00Z",
    "confirmed_by_name": "Jane Buyer",
    "note": "Customer confirmed by email."
  },
  "selected_line_item_ids": ["uuid"],
  "bill_to": { "name": "", "company": "", "address": "" },
  "ship_to": { "name": "", "company": "", "address": "" },
  "notes": ""
}
```

**Response safety block (required on all order payloads):**

```json
{
  "safety": {
    "production_started": false,
    "shipment_created": false,
    "payment_received": false,
    "inventory_confirmed": false,
    "certification_confirmed": false,
    "lead_time_confirmed": false,
    "automatic_sending_enabled": false
  }
}
```

---

## Permission Model

| Action | admin | sales_manager | sales | operator | production_manager | viewer |
|---|---|---|---|---|---|---|
| Create order from quote | ✓ | ✓ | ✓ (→ pending) | — | — | — |
| Confirm customer | ✓ | ✓ | ✓ (note types limited) | — | — | — |
| Cancel order | ✓ | ✓ | — | — | — | — |
| View order + financials | ✓ | ✓ | ✓ | ✓ | ✓ | read |
| Update logistics fields | ✓ | ✓ | — | ✓ | ✓ | — |
| Supplier confirmation | ✓ | ✓ | — | — | ✓ | — |
| Production milestones | ✓ | — | — | — | ✓ | read |
| Shipment plans | ✓ | ✓ | — | ✓ | ✓ | read |
| Reprice order line | ✓ | ✓ | — | — | — | — |
| Customer portal view | future | future | future | future | future | future |

**Rules:**

1. `sales` cannot start production or record supplier confirmation
2. `production_manager` cannot change quote-derived prices
3. Supplier confirmation requires `admin`, `sales_manager`, or `production_manager`
4. Cancel requires `admin` or `sales_manager`

---

## Safety Rules

1. **Order ≠ production started** — status and milestones are separate; no auto-start
2. **Supplier confirmation** — never inferred from quote send or readiness pass
3. **Inventory** — `inventory_confirmed` defaults false; manual toggle only
4. **Certification** — same as inventory
5. **Lead time** — text field only; not a system guarantee
6. **Shipment** — no auto-create on order creation
7. **Customer confirmation** — must record type and timestamp
8. **Payment** — not implemented in D7.1; never auto-set received
9. **No auto email** to customer or supplier in D7 MVP
10. **Forbidden customer-facing text** unless explicitly confirmed: `inventory confirmed`, `lead time confirmed`, `production started`, `shipment booked`, `payment received`

---

## Recommended D7.2 MVP Scope

| Deliverable | In D7.2 |
|---|---|
| Migration: `customer_orders`, `order_line_items` | Yes |
| `POST /orders/from-quote` | Yes |
| Order CRUD (list, get, patch, cancel) | Yes |
| Order timeline (derived) | Yes |
| Link to source quote (read-only) | Yes |
| `pending_customer_confirmation` + `confirmed` statuses | Yes |
| Partner splits table | D7.4 |
| Supplier confirmations | D7.4 |
| Customer confirmation flow | D7.3 |
| Production milestones | D7.5 |
| Shipment plans | D7.6 |
| Frontend `/orders` pages | D7.2+ |
| Payment / invoice | Future |

---

## Open Questions

| # | Question | Recommendation | Needs user? |
|---|---|---|---|
| 1 | One order per quote or allow multiple partial orders? | **One active order per quote** in MVP; partial via selected lines only | Yes |
| 2 | Allow order without customer confirmation? | **Yes** → `pending_customer_confirmation` | Confirm |
| 3 | Reprice on order line — who approves? | sales_manager + audit log | Yes |
| 4 | Quote expired but customer confirms — allow order? | **Reject** unless quote renewed | Yes |
| 5 | Auto-create partner splits on order creation? | **Yes** from `partner_routes` | No |
| 6 | Sample orders vs production orders — same table? | Same `customer_orders`; `order_type` field future | Yes |
| 7 | Integration with existing RFQ `quotations`? | **No link in MVP** — separate workflows | No |
| 8 | Order PDF / packing list? | Future D7.x | Yes |
| 9 | Multi-currency orders? | MVP: single currency from quote | No |
| 10 | Archive vs cancel for completed orders? | `delivered` terminal + soft archive flag | Yes |

---

## References

- [D7 Order Module Readiness Brief](d7_order_module_readiness_brief.md)
- [Phase 3 Roadmap](phase3_roadmap.md)
- [D6 Capability Map](../architecture/d6_quote_capability_map.md)
- [D6.6 Quote-to-Order Readiness Gate](../phase2/d6_6_quote_to_order_readiness_gate.md)
- [D6 Final Closure Record](../records/d6_final_closure_20260523.md)

---

## Final Judgment

**D7.1 design review is complete.** Ready for D7.2 Order CRUD MVP implementation planning. No tables, migrations, or order APIs were added in this stage.
