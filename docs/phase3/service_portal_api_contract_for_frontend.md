# Service Portal API Contract for Frontend

Base path: `/api/v1/portal/customer`

Authentication: `Authorization: Bearer <portal-server-token>` or `X-Portal-Customer-Token: <portal-server-token>`.

The preferred production shape is a service portal backend proxy. Browser code should not store the PartnerOS token.

## GET /manifest

Returns the token-gated customer Portal contract manifest for `service.intelli-opus.com`. It includes contract version, source of truth, public base URL, auth header metadata, endpoint paths, customer-visible surfaces, hidden-field categories, and safety flags. It never includes the token value.

Use this before data reads to confirm the bridge contract without relying on internal operator-only readiness endpoints. The manifest also includes a `field_contract` object with customer-visible field names for products, orders, snapshots, production, shipment, resources, feedback creation, feedback form allowed values, customer status stages, progress step states, and the non-guaranteed planned-date policy.

The manifest `field_contract.feedback_form_contract` block is available before an order-specific snapshot is loaded:

```json
{
  "submit_endpoint": "/api/v1/portal/customer/feedback",
  "submit_method": "POST",
  "allowed_feedback_types": ["tracking", "resource", "quality", "general"],
  "allowed_priorities": ["normal", "high", "urgent"],
  "requires_order_id": false,
  "customer_name_required": false,
  "customer_email_required": false,
  "resolution_time_promised": false,
  "customer_notified": false,
  "automatic_reply_sent": false
}
```

## GET /products

Query: `category`, `search`, `page`, `limit`.

```json
{
  "items": [
    {
      "id": "uuid",
      "internal_sku": "SKU-001",
      "product_name": "Adjustable Desk Frame",
      "product_category": "desk_frame",
      "product_family": "ergonomics",
      "description": "Customer-facing description",
      "status": "active",
      "uom": "set",
      "currency": "USD",
      "default_incoterm": "FOB",
      "image_url": null,
      "attributes": {}
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 50
}
```

## GET /orders

Query: `company_id`, `status`, `page`, `limit`.

```json
{
  "id": "uuid",
  "order_number": "O-2026-0001",
  "status": "confirmed",
  "order_date": "2026-05-29",
  "company_id": "uuid",
  "company_name": "Customer Co",
  "currency": "USD",
  "grand_total": "1000.00",
  "customer_confirmed_at": "2026-05-29T12:00:00+00:00",
  "ship_to_company": "Customer Co",
  "ship_to_address": "Customer address"
}
```

## GET /orders/{id}

Returns the order summary plus billing/shipping terms, customer notes, and customer-visible line items.

```json
{
  "id": "uuid",
  "order_number": "O-2026-0001",
  "status": "confirmed",
  "bill_to_company": "Customer Co",
  "ship_to_name": "Receiving Team",
  "payment_terms": "Net 30",
  "shipping_terms": "FOB",
  "customer_notes": "Customer-visible note",
  "line_items": [
    {
      "id": "uuid",
      "product_name": "Adjustable Desk Frame",
      "product_category": "desk_frame",
      "description": "Customer-facing line description",
      "quantity": 10,
      "uom": "set",
      "unit_price": "100.00",
      "total_price": "1000.00",
      "currency": "USD",
      "incoterm": "FOB",
      "status": "confirmed"
    }
  ]
}
```

## GET /orders/{id}/snapshot

Returns a customer-visible rollup for the Portal order tracking page. This combines the safe order detail, production milestones, shipment plans, customer-visible resources, and feedback link metadata.

```json
{
  "order": {
    "id": "uuid",
    "order_number": "O-2026-0001",
    "status": "confirmed"
  },
  "customer_status": {
    "stage": "ready_to_ship",
    "label": "Ready to ship",
    "next_action_label": "Shipment planning",
    "next_action_detail": "The order is ready to ship and logistics details will appear when an operator adds a shipment plan.",
    "order_confirmed": true,
    "production_started": true,
    "production_completed": true,
    "ready_to_ship": true,
    "shipped": false,
    "delivered": false,
    "current_step_index": 2,
    "progress_steps": [
      {
        "key": "confirmed",
        "label": "Order confirmed",
        "state": "complete",
        "date": "2026-05-29T12:00:00+00:00",
        "planned_dates_are_guarantees": false
      },
      {
        "key": "in_production",
        "label": "Production in progress",
        "state": "complete",
        "date": null,
        "planned_dates_are_guarantees": false
      },
      {
        "key": "ready_to_ship",
        "label": "Ready to ship",
        "state": "current",
        "date": null,
        "planned_dates_are_guarantees": false
      },
      {
        "key": "shipped",
        "label": "Shipment in transit",
        "state": "pending",
        "date": null,
        "planned_dates_are_guarantees": false
      },
      {
        "key": "delivered",
        "label": "Delivered",
        "state": "pending",
        "date": null,
        "planned_dates_are_guarantees": false
      }
    ],
    "planned_dates_are_guarantees": false
  },
  "tracking_summary": {
    "stage": "ready_to_ship",
    "production_item_count": 3,
    "shipment_item_count": 1,
    "resource_visible_count": 0,
    "feedback_open_count": 0,
    "has_production_updates": true,
    "has_active_shipment": true,
    "has_visible_resources": false,
    "has_open_feedback": false,
    "planned_dates_are_guarantees": false
  },
  "production": {
    "items": [],
    "status_counts": {
      "completed": 3
    },
    "blocked_count": 0,
    "delayed_count": 0
  },
  "shipment": {
    "items": [],
    "status_counts": {
      "planned": 1
    },
    "active_count": 1
  },
  "resources": {
    "items": [],
    "visible_count": 0
  },
  "feedback": {
    "submit_endpoint": "/api/v1/portal/customer/feedback",
    "submit_method": "POST",
    "allowed_feedback_types": ["tracking", "resource", "quality", "general"],
    "allowed_priorities": ["normal", "high", "urgent"],
    "requires_order_id": false,
    "customer_name_required": false,
    "customer_email_required": false,
    "resolution_time_promised": false,
    "total_count": 0,
    "open_count": 0,
    "customer_notified": false,
    "automatic_reply_sent": false
  },
  "safety": {
    "customer_visible_only": true,
    "forbidden_field_filter_enabled": true,
    "cost_fields_exposed": false,
    "private_supplier_fields_exposed": false,
    "server_file_path_exposed": false,
    "customer_notified": false
  }
}
```

`stage`, `current_step_index`, `progress_steps`, `next_action_*`, and `tracking_summary` are display guidance for the Portal. Planned dates are planning data only and are not guaranteed lead time. The `feedback` block gives the Portal backend enough safe metadata to render the customer feedback form without guessing allowed types or priorities; it still does not promise resolution time or send any notification.

## GET /orders/{id}/production

```json
{
  "order_id": "uuid",
  "items": [
    {
      "milestone_type": "production",
      "milestone_label": "Assembly",
      "sequence": 20,
      "status": "in_progress",
      "planned_date": "2026-06-10",
      "actual_date": null
    }
  ],
  "total": 1,
  "completed_count": 0
}
```

## GET /orders/{id}/shipment

```json
{
  "order_id": "uuid",
  "items": [
    {
      "status": "planned",
      "shipment_method": "sea",
      "estimated_ship_date": "2026-06-20",
      "estimated_arrival_date": "2026-07-20",
      "tracking_number": null
    }
  ],
  "total": 1
}
```

## GET /orders/{id}/resources

```json
{
  "order_id": "uuid",
  "items": [
    {
      "id": "uuid",
      "file_id": "uuid",
      "filename": "packing-list.pdf",
      "mime": "application/pdf",
      "size": 12345,
      "category": "packing_list",
      "description": "Customer-visible resource",
      "status": "published",
      "customer_visible": true,
      "download_url": "/api/v1/portal/customer/resources/uuid/download?expires_at=1780000000&token=...",
      "download_expires_at": 1780000000,
      "created_at": "2026-05-29T12:00:00+00:00",
      "safety": {
        "download_link_signed": true,
        "file_location_exposed": false,
        "filesystem_path_exposed": false,
        "customer_notified": false,
        "automatic_email_sent": false
      }
    }
  ],
  "total": 1
}
```

No storage key or backend path is exposed. Download URLs are signed and expire.

## POST /feedback

```json
{
  "order_id": "uuid or null",
  "company_id": "uuid or null",
  "feedback_type": "tracking",
  "subject": "TEST shipment question",
  "message": "TEST: customer asks for an updated ETA.",
  "priority": "normal",
  "customer_name": "TEST Portal User",
  "customer_email": "portal-uat@example.com"
}
```

```json
{
  "ticket_number": "FB-2026-0001",
  "status": "new",
  "feedback_received": true,
  "customer_notified": false,
  "automatic_reply_sent": false,
  "resolution_time_promised": false
}
```

Staging feedback must be clearly marked as `TEST`. PartnerOS does not auto-reply, notify customers, or promise resolution time. PartnerOS validates `feedback_type` and `priority` against the values advertised in the snapshot feedback metadata; unknown values return HTTP 400 and do not create a ticket.

## Internal Operations Console

Internal PartnerOS operators can inspect launch readiness at:

```text
GET /api/v1/portal/operations/console
```

This is an internal authenticated endpoint, not a customer Portal API. It shows Portal API config, endpoint readiness, recent customer-visible orders, customer snapshots, shipment status counts, feedback ticket counts, and forbidden-field audit status. It is read-only and does not notify customers or suppliers, call carrier APIs, or mutate order/shipment state.

The internal `/portal-customer-bridge` UAT page provides a read-only service Portal read path check: manifest, products, orders, then the first returned order's detail, snapshot, production, shipment, and resources. TEST feedback creation remains a separate explicit action.

The response includes `portal_contract` for staging handoff: public base URL, allowed origins, server-to-server auth header name, token required/configured booleans, customer Portal endpoint paths, endpoint readiness, and the same customer-visible `field_contract` exposed by `GET /api/v1/portal/customer/manifest`. It never includes the token value.

The response includes `portal_launch_readiness`, a read-only rollup for staging connection preparation. It aggregates config, runtime, endpoint readiness, forbidden-field audit, customer snapshots, resources, and feedback queue checks into blockers and warnings. It never marks staging validated, deploys, notifies anyone, calls carriers, or exposes token values.

The `staging_integration_checklist` block turns the same readiness state into operator-facing launch tasks: configure Portal API env, verify backend runtime and migrations, confirm endpoint contract, clear forbidden-field audit, review customer snapshots, complete shipment tracking, publish customer resources, triage feedback, and run the real service Portal smoke externally. It is a checklist only: it does not create proof records, deploy, validate staging, expose tokens, notify customers/suppliers, call carriers, or send automatic replies.

The internal `recent_customer_visible_orders.items[]` rows include a `portal_tracking` summary when a snapshot is available for that row: stage, customer label, next action label, active shipment count, open feedback count, production/shipment/resource/feedback signal booleans, and `planned_dates_are_guarantees=false`. This helps operators compare recent order rows with the customer Portal tracking state during staging integration without exposing internal fields.

The `shipment_readiness` block summarizes logistics tracking readiness for Portal launch: active, planned, shipped, delivered, cancelled, shipment plans missing estimated dates, shipped plans missing tracking numbers, and read-only `action_items`. Action items identify shipment plans needing estimated dates, shipment method confirmation, tracking number entry, or arrival monitoring. They expose only metadata and booleans such as `tracking_number_present`; they do not expose tracking-number values, call carrier APIs, create shipments, notify customers/suppliers, mutate order status, or make planned dates guarantees.

The response also includes `runtime_health`, a read-only summary of database status, Alembic current/head revisions, migration pending state, Portal API config readiness, and sanitized warnings. It does not expose database URLs, storage paths, secrets, or token values.

The `feedback_operations` block summarizes internal feedback triage for Portal launch readiness: open tickets, high-priority tickets, tickets needing internal review, missing response summaries, resolved tickets ready to close, oldest open age, and metadata-only `action_items`. Action items identify tickets that need internal assignment, prioritized review, response summaries, or closure. They are internal queue guidance only and do not create replies, notify customers, send email/webhooks, or promise an SLA.

Internal operators can use `POST /api/v1/feedback-tickets/{id}/resolve` and `POST /api/v1/feedback-tickets/{id}/close` for explicit workflow actions. Both actions update PartnerOS internal status and response summary only; they do not send customer replies, email, webhooks, or SLA promises.

The `customer_snapshot_readiness` block summarizes the customer-visible snapshots currently shown in the console: stage counts, production-visible count, active shipment count, open feedback count, missing progress-step count, and read-only `action_items`. Snapshot action items identify orders that need customer-visible production updates, shipment plans, resource publishing, feedback review, or progress-step review before Portal staging integration. They do not notify customers/suppliers, create shipments, mutate order status, or make planned dates guarantees.

The `multi_partner_flow_readiness` block is an internal read-only summary of partner-neutral execution coverage. It shows partner count, order/split count, partners with production/shipment data, partners with risk flags, and per-partner operational counts. It must not rank partners, change partner selection, notify suppliers/customers, create shipments, or mutate order status.

The `resource_readiness` block summarizes customer resource availability for Portal launch: portal-visible resources, customer-visible resources that still need publishing, hidden published resources, status/category counts, metadata-only `action_items`, and signed-download safety flags. Action items identify the internal resource id, order id, title, category, status, customer visibility, portal visibility, and the suggested internal action such as `publish_customer_visible_resource` or `review_hidden_published_resource`. They must not expose storage keys, filesystem paths, download URLs, original filenames, or raw token values.

`forbidden_field_audit` scans the current customer-visible order list, customer snapshots, and portal contract metadata. It reports marker names and payload paths only, never raw token values or hidden field values.

The console also includes `market_signal_preview`, a read-only advisory rollup for internal Market Response preparation. It groups order lines, ordered quantity, feedback, production risk, and shipment risk across focus areas: adjustable desk frames, desk legs, lifting columns, education furniture, project furniture, and other products. This preview does not create tickets, change recommendations, notify customers/suppliers, or rank partners.
