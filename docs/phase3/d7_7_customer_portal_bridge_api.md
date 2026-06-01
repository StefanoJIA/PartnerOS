# D7.7 Customer Portal Bridge API

**Status:** Implemented - **Date:** 2026-05-29 - **Migration:** `0015_feedback_tickets`

## Goal

Expose PartnerOS customer-visible product, order, production, shipment, resource, and feedback data for integration testing with the already-deployed `service.intelli-opus.com` customer portal.

PartnerOS remains the internal source of truth. `service.intelli-opus.com` remains customer-facing.

## API

Prefix: `/api/v1/portal/customer`

| Method | Path | Purpose |
|---|---|---|
| GET | `/products` | Customer-visible product catalog |
| GET | `/orders` | Customer-visible order list |
| GET | `/orders/{order_id}` | Customer-visible order detail |
| GET | `/orders/{order_id}/snapshot` | Customer-visible order, production, shipment, resources, and feedback rollup |
| GET | `/orders/{order_id}/production` | Production milestone view |
| GET | `/orders/{order_id}/shipment` | Shipment plan view |
| GET | `/orders/{order_id}/resources` | Customer-safe resource metadata |
| POST | `/feedback` | Feedback ticket intake |

## Auth MVP

Default settings:

```env
PORTAL_CUSTOMER_API_ENABLED=false
PORTAL_CUSTOMER_API_TOKEN=
PORTAL_CUSTOMER_API_REQUIRE_TOKEN=true
PORTAL_CUSTOMER_ALLOWED_ORIGINS=
```

The MVP uses a single server-to-server token. Real tokens belong only in `.env` or deployment secrets.

## Field Whitelist

Customer APIs return explicit whitelisted fields only. They must not return:

- internal cost
- margin
- pricing breakdown JSON
- cost snapshot JSON
- supplier private notes
- supplier references
- internal activity logs
- backend file paths
- storage keys
- tokens/secrets

## Feedback MVP

Feedback creates a `feedback_tickets` row with `FB-YYYY-0001` numbering. It does not:

- auto-reply
- notify customers
- promise resolution time
- create outbound messages

## D8 Launch-Readiness Additions

D8 adds a customer-visible snapshot endpoint and an internal Portal Operations console:

- `GET /api/v1/portal/customer/orders/{order_id}/snapshot` for the service portal order tracking view.
- `GET /api/v1/portal/operations/console` for internal operators to inspect enabled/token/public-base/CORS config, endpoint readiness, recent orders, shipment statuses, feedback tickets, and forbidden-field audit status.

The snapshot exposes only whitelisted customer fields. Planned dates are planning data, not guaranteed lead time. The operations console is read-only and does not notify customers/suppliers, call carrier APIs, or mutate order/shipment status.

## Integration Plan

1. Keep D7.7 disabled by default in PartnerOS.
2. Configure token and allowed origins in deployment secrets.
3. Run `scripts/d7_7_portal_bridge_check.py`.
4. Connect `service.intelli-opus.com` to the read APIs.
5. Verify no internal fields appear in portal network responses.
