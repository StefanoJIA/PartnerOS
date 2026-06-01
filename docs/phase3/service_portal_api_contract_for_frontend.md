# Service Portal API Contract for Frontend

Base path: `/api/v1/portal/customer`

Authentication: `Authorization: Bearer <portal-server-token>` or `X-Portal-Customer-Token: <portal-server-token>`.

The preferred production shape is a service portal backend proxy. Browser code should not store the PartnerOS token.

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
    "order_confirmed": true,
    "production_started": true,
    "production_completed": true,
    "ready_to_ship": true,
    "shipped": false,
    "delivered": false,
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

`stage` is display guidance for the Portal. Planned dates are planning data only and are not guaranteed lead time.

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

Staging feedback must be clearly marked as `TEST`. PartnerOS does not auto-reply, notify customers, or promise resolution time.

## Internal Operations Console

Internal PartnerOS operators can inspect launch readiness at:

```text
GET /api/v1/portal/operations/console
```

This is an internal authenticated endpoint, not a customer Portal API. It shows Portal API config, endpoint readiness, recent customer-visible orders, customer snapshots, shipment status counts, feedback ticket counts, and forbidden-field audit status. It is read-only and does not notify customers or suppliers, call carrier APIs, or mutate order/shipment state.

The response includes `portal_contract` for staging handoff: public base URL, allowed origins, server-to-server auth header name, token required/configured booleans, customer Portal endpoint paths, and endpoint readiness. It never includes the token value.

The console also includes `market_signal_preview`, a read-only advisory rollup for internal Market Response preparation. It groups order lines, ordered quantity, feedback, production risk, and shipment risk across focus areas: adjustable desk frames, desk legs, lifting columns, education furniture, project furniture, and other products. This preview does not create tickets, change recommendations, notify customers/suppliers, or rank partners.
