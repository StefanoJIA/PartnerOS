# D7.8 Service Portal Live Integration UAT

**Status:** Implemented - **Date:** 2026-05-29 - **Migration:** `0016_feedback_ops`

## Goal

D7.8 moves the D7.7 customer portal bridge from "API exists" to "ready for staging integration testing" with `service.intelli-opus.com`.

PartnerOS remains the source of truth. `service.intelli-opus.com` remains the customer-facing portal.

## Base URL

Local UAT:

```text
http://127.0.0.1:8014/api/v1/portal/customer
```

Staging should configure the PartnerOS backend origin in the service portal environment. Do not hard-code secrets or internal development URLs in portal code.

## Auth

Portal customer APIs are disabled by default and token-required:

```env
PORTAL_CUSTOMER_API_ENABLED=false
PORTAL_CUSTOMER_API_TOKEN=
PORTAL_CUSTOMER_API_REQUIRE_TOKEN=true
PORTAL_CUSTOMER_ALLOWED_ORIGINS=
```

The staging caller sends `Authorization: Bearer <portal-server-token>` or `X-Portal-Customer-Token: <portal-server-token>`.

Real tokens belong only in `.env`, deployment secrets, or the service portal backend secret store.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/products` | Customer-visible product catalog |
| GET | `/orders` | Customer-visible order list |
| GET | `/orders/{order_id}` | Customer-visible order detail |
| GET | `/orders/{order_id}/production` | Customer production milestones |
| GET | `/orders/{order_id}/shipment` | Customer shipment plans |
| GET | `/orders/{order_id}/resources` | Customer-safe resource metadata |
| POST | `/feedback` | Create TEST or customer feedback ticket |

Internal Operator endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/feedback-tickets` | List feedback tickets |
| GET | `/api/v1/feedback-tickets/{id}` | Ticket detail |
| PATCH | `/api/v1/feedback-tickets/{id}` | Update status, priority, owner, response summary |
| GET | `/api/v1/portal/customer/readiness` | Internal readiness view; never exposes token |

## Error Codes

Disabled:

```json
{"ok": false, "error": {"code": "SERVICE_UNAVAILABLE", "message": "Customer portal bridge API is disabled"}}
```

Missing token:

```json
{"ok": false, "error": {"code": "VALIDATION_ERROR", "message": "Customer portal token required"}}
```

Wrong token:

```json
{"ok": false, "error": {"code": "VALIDATION_ERROR", "message": "Invalid customer portal token"}}
```

## Customer Field Whitelist

Portal responses may include:

- Product: id, sku, name, category, family, customer description, status, uom, currency, incoterm, image URL, public attributes.
- Order: id, order number, status, order date, company id/name, customer totals, shipping address fields, payment/shipping terms, customer notes, visible line items.
- Production: milestone type, label, sequence, status, planned date, actual date.
- Shipment: status, method, estimated dates, tracking number, origin/destination when customer-visible.
- Resources: file id, filename, mime, size, purpose, created_at.
- Feedback response: ticket_number, status, safety flags.

Portal responses must not include internal cost, margin, pricing breakdown JSON, cost snapshot JSON, supplier private notes, supplier references, internal activity logs, backend file paths, storage keys, tokens, or secrets.

## Service Portal Frontend Notes

1. Prefer a service portal backend proxy that stores the PartnerOS token server-side.
2. Treat PartnerOS as authoritative for products, order state, production, shipment, resources, and feedback ticket creation.
3. Render empty production/shipment/resources arrays as "not available yet", not as an error.
4. Mark all staging feedback as `TEST` until production data is explicitly approved.

## UAT Checklist

- `PORTAL_CUSTOMER_API_ENABLED=true` only in the staging environment under test.
- `PORTAL_CUSTOMER_API_TOKEN` configured as a secret.
- `PORTAL_CUSTOMER_ALLOWED_ORIGINS` includes `https://service.intelli-opus.com` or the staging service portal origin.
- No token appears in browser-visible API responses.
- Missing token returns 401.
- Wrong token returns 403.
- Correct token returns products/orders.
- At least one order detail can load production, shipment, and resources.
- TEST feedback creates a `feedback_tickets` row with no auto reply.
- Operator can view and resolve the ticket in `/feedback-tickets`.
- `python scripts/d7_8_portal_live_integration_check.py` returns PASS.
