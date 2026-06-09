# Service Portal Staging Handoff Checklist

Status: READY_FOR_STAGING_HANDOFF

This checklist describes the real `service.intelli-opus.com` staging handoff. It must not be used to claim real staging validation before the real staging environment and private values are available.

## Required Private Values

The staging operator must provide or confirm:

- Backend HTTPS origin reachable by `service.intelli-opus.com`.
- `PORTAL_CUSTOMER_API_ENABLED=true`.
- `PORTAL_CUSTOMER_API_TOKEN` with a real private server-to-server value.
- `PORTAL_CUSTOMER_ALLOWED_ORIGINS` including the real service Portal origin.
- `PUBLIC_BASE_URL` for customer-safe links and manifests.

Do not commit token values, `.env` files, screenshots containing secrets, local storage dumps, generated PDFs, `IE Auto.pdf`, `local_data/`, or `backend/storage/`.

## PartnerOS / Portal Boundary

PartnerOS is the internal source of truth.

`service.intelli-opus.com` is the customer-facing Portal.

The Portal should call the server-to-server bridge API and render only whitelisted fields.

## UAT Scope

Verify these customer-facing data surfaces:

- Products.
- Order list.
- Order detail.
- Customer order snapshot.
- Production.
- Shipment.
- Resources.
- Feedback submission.

## Safety Requirements

UAT must confirm:

- No internal cost fields.
- No margin fields.
- No pricing breakdown JSON.
- No cost snapshot JSON.
- No supplier private notes.
- No backend file paths.
- No storage keys.
- No token values.
- Planned dates are presented as planned dates, not guarantees.
- Feedback submission creates a ticket but does not auto-reply or notify customers.
- Shipment data does not call a carrier API.
- Order status is not automatically changed by Portal reads.

## Suggested Smoke Sequence

1. Confirm PartnerOS backend health from the staging-facing HTTPS origin.
2. Confirm unauthenticated Portal API requests are rejected.
3. Confirm wrong token is rejected.
4. Confirm correct token is accepted.
5. Fetch products and inspect field whitelist.
6. Fetch orders and inspect field whitelist.
7. Fetch one order detail and customer snapshot.
8. Fetch production and shipment for that order.
9. Fetch resources and confirm no file path exposure.
10. Submit one test feedback ticket.
11. Confirm the feedback ticket appears in PartnerOS Feedback Tickets.
12. Re-run forbidden-field checks against returned payloads.

## Acceptance Boundary

Until the real token, allowed origin, backend HTTPS origin, and public base URL are verified against `service.intelli-opus.com`, the project remains at READY_FOR_STAGING_HANDOFF.

Do not mark the environment staging-validated from local rehearsal alone.
