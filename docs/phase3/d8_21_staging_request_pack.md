# D8.21 Staging Request Pack

## Purpose

Use this request pack to ask the responsible operators for the real staging values required by the D8.20 staging handoff contract.

Current state: READY_FOR_STAGING_HANDOFF.

External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE.

This request does not ask anyone to deploy automatically, expose tokens in chat, or claim real external staging validation before verification.

## Request Summary

PartnerOS is ready to receive real staging configuration for the customer-facing Portal bridge. Please provide the following through approved secure channels.

## Required Values

### Backend HTTPS Origin

Request item: backend HTTPS origin.

Requested from: infrastructure / deployment operator.

Need:

- Public HTTPS origin for the PartnerOS backend staging environment.
- It must be reachable by the `service.intelli-opus.com` Portal runtime.
- It must expose backend health and Portal customer bridge APIs over HTTPS.

Validation:

- `GET /health` succeeds from the staging-facing network path.
- Portal bridge endpoints are reachable through the same origin.

### `PORTAL_CUSTOMER_API_ENABLED`

Requested from: intelliOffice backend operator.

Need:

- Set to `true` only for the intended staging environment.
- Keep disabled for internal-only or failed staging states.

Validation:

- Portal readiness endpoint reports enabled state only when staging is intentionally active.

### `PORTAL_CUSTOMER_API_TOKEN`

Requested from: intelliOffice backend operator and security reviewer.

Need:

- Real private server-to-server token.
- Token must be stored in secret management.
- Token must not be committed, pasted into docs, screenshots, browser storage, or logs.

Validation:

- Correct token succeeds.
- Missing token fails.
- Wrong token fails.
- Browser clients cannot see the token.

### `PORTAL_CUSTOMER_ALLOWED_ORIGINS`

Requested from: backend operator, Portal operator, and infrastructure operator.

Need:

- Must include the exact real `service.intelli-opus.com` origin.
- Should not include broad wildcards.
- Should be cleared during rollback.

Validation:

- Allowed origin succeeds.
- Disallowed origin is rejected.

### `PUBLIC_BASE_URL`

Requested from: infrastructure / deployment operator.

Need:

- Customer-safe public base URL used for links, manifests, and external references.

Validation:

- Manifest and customer-safe links use the expected value.

### `service.intelli-opus.com` Real Origin

Requested from: service Portal operator.

Need:

- Exact HTTPS origin used by the customer-facing Portal.
- Confirmation whether there is a separate staging subdomain or path.

Validation:

- Origin matches `PORTAL_CUSTOMER_ALLOWED_ORIGINS`.
- Portal requests are made server-to-server.

## Requested Response Format

Please reply through the approved secure channel with:

- Backend HTTPS origin:
- Portal real origin:
- Whether Portal has a separate staging origin:
- Who will configure `PORTAL_CUSTOMER_API_ENABLED`:
- Who will provision `PORTAL_CUSTOMER_API_TOKEN`:
- Who will configure `PORTAL_CUSTOMER_ALLOWED_ORIGINS`:
- Who will configure `PUBLIC_BASE_URL`:
- Planned staging window:
- Rollback owner:
- Security reviewer:
- Business UAT owner:

Do not include the raw token in this document or in any Git commit.

## Handoff Boundary

Until these values are provided and verified, PartnerOS remains READY_FOR_STAGING_HANDOFF and external staging remains WAITING_FOR_REAL_STAGING_EVIDENCE.

Do not automatically enable staging, deploy, send notifications, or change quote/order status from this request pack.
