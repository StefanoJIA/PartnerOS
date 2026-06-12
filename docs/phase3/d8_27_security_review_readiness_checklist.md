# D8.27 Security Review Readiness Checklist

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Security review status: pending

No real security sign-off recorded yet. This checklist prepares PartnerOS for a future security reviewer session before service Portal staging UAT or pilot. It does not approve production use, does not validate real staging, and does not write STAGING_VALIDATED.

## Review Scope

Security reviewer should verify:

- server-to-server Portal bridge boundaries
- token storage / rotation / revocation
- CORS / allowed origins / no wildcard
- browser token exposure controls
- log and documentation secret handling
- customer-safe whitelist
- forbidden fields blacklist
- rollback / disable Portal API
- no automatic external sending
- no quote/order auto-status-change

## Token Storage / Rotation / Revocation

| Check | Expected Rule | Status | Notes |
| --- | --- | --- | --- |
| token storage | Token is stored only in environment or approved secret storage, not in git, docs, screenshots, or frontend bundle | pending | Do not handle real token in this repo task |
| token rotation | Rotation procedure exists before staging UAT | pending | Requires real operator process |
| token revocation | Revocation procedure exists before staging UAT | pending | Must support immediate disable |
| token scope | Portal token is only for server-to-server customer Portal API access | pending | No browser token |
| token logging | Token value never appears in logs | pending | Review app and reverse proxy logs during real staging |

## CORS / Allowed Origins / No Wildcard

| Check | Expected Rule | Status | Notes |
| --- | --- | --- | --- |
| allowed origins | PORTAL_CUSTOMER_ALLOWED_ORIGINS contains only approved service.intelli-opus.com origin(s) | pending | No wildcard |
| no wildcard | `*` is not allowed for customer Portal API in staging/pilot | pending | Security reviewer must confirm |
| wrong origin | Disallowed origin is rejected | pending | Real staging smoke required later |
| preflight | CORS preflight follows explicit allowlist | pending | No browser token exposure |

## Server-To-Server Portal Bridge

| Check | Expected Rule | Status | Notes |
| --- | --- | --- | --- |
| bridge mode | service.intelli-opus.com calls PartnerOS server-to-server | pending | No public direct browser token |
| auth boundary | Portal token is checked on backend bridge endpoints | pending | Wrong/missing token must fail safely |
| field boundary | Responses are built from customer-safe whitelist only | pending | Forbidden fields remain blocked |
| staging state | External staging remains WAITING_FOR_REAL_STAGING_EVIDENCE until real smoke evidence exists | pending | No STAGING_VALIDATED claim |

## Browser, Logs, Screenshots, Docs

| Area | Expected Rule | Status |
| --- | --- | --- |
| browser | Browser must not see token values | pending |
| frontend bundle | Frontend build must not contain Portal token | pending |
| logs | Logs must not include token values | pending |
| screenshots | Screenshots must not contain secret values | pending |
| docs | Docs must not contain secret values | pending |
| examples | Example tokens must be placeholders only | pending |

## Customer-Safe Whitelist

The customer-safe whitelist for service Portal may include only approved high-level fields:

- products: approved product family, customer-facing name, approved specs, approved resources
- orders: customer-safe order reference, status label, customer-visible delivery summary
- production milestones: planned/completed milestone labels and dates marked clearly
- shipment status: planned window, status label, customer-safe risk summary
- resources: approved title, category, customer-safe manifest entry
- feedback status: sanitized topic, status, customer-safe next action
- Market Response preview: high-level preview only, no internal scoring or ranking

## Forbidden Fields Blacklist

The following must not be exposed through customer Portal, docs, screenshots, logs, staging-safe seeds, or partner-facing material:

- cost
- margin
- pricing breakdown
- supplier private notes
- internal-only comments
- private partner notes
- backend paths
- storage keys
- token values
- unsafe raw database IDs
- internal audit events
- internal owner notes
- unreviewed risk notes
- internal Market Response scoring/ranking

## Rollback / Disable Portal API

Security reviewer should confirm rollback steps:

1. Set `PORTAL_CUSTOMER_API_ENABLED=false`.
2. Revoke or rotate `PORTAL_CUSTOMER_API_TOKEN`.
3. Clear or narrow `PORTAL_CUSTOMER_ALLOWED_ORIGINS`.
4. Confirm wrong/missing token fails safely.
5. Confirm service Portal receives safe error state.
6. Keep PartnerOS internal source of truth available.

## No Automatic External Actions

PartnerOS must not automatically send:

- email
- SMS
- LinkedIn messages
- customer notifications
- supplier notifications
- carrier API requests
- webhooks

## No Quote/Order Auto-Status-Change

Security review must confirm:

- Portal bridge reads customer-safe fields only.
- Customer Portal access does not automatically change quote status.
- Customer Portal access does not automatically change order status.
- Shipment display does not automatically set shipped or delivered.
- Feedback submission does not automatically promise resolution or send external notifications.

## HOSUN Security Boundary

HOSUN lifting systems internal-only fields:

- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- supplier private notes
- internal Market Response scoring

HOSUN customer-safe candidate fields only after business confirmation:

- load range
- stability summary
- noise claim
- delivery window
- installation summary
- after-sales support
- warranty summary
- test cycle summary
- certification summary
- packaging summary

## Boundary

- No real security sign-off recorded yet.
- Pending does not mean approved.
- Do not enter D9.
- Do not create proof records.
- Do not write STAGING_VALIDATED.
- Do not fabricate real security approval.
- Do not process real token values in this task.
