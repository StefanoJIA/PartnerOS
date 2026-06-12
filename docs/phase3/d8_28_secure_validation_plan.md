# D8.28 Secure Validation Plan

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Validation status: pending real credentials

No real staging credentials recorded in repository. This plan defines the required secure validation order after real credentials are provided through secure channels. It is not a real staging validation record.

## Prerequisites

All prerequisites must be complete before this plan can be executed against real staging:

- backend HTTPS origin received through approved channel
- service.intelli-opus.com real origin received through approved channel
- `PORTAL_CUSTOMER_API_ENABLED` configured only for staging
- `PORTAL_CUSTOMER_API_TOKEN` configured securely without recording the value
- `PORTAL_CUSTOMER_ALLOWED_ORIGINS` configured without wildcard
- `PUBLIC_BASE_URL` configured for staging
- security reviewer assigned
- business owner sign-off pending or complete according to scope
- rollback owner assigned

## Validation Order

| Step | Validation | Expected Result | Status |
| --- | --- | --- | --- |
| 1 | backend HTTPS `/health` | backend returns healthy status over HTTPS | pending |
| 2 | Portal bridge readiness | bridge readiness endpoint reports safe configured state | pending |
| 3 | `enabled=true` only in staging | Portal customer API is enabled only in staging environment | pending |
| 4 | correct token success | server-to-server request with correct token succeeds | pending |
| 5 | missing token fail | request without token fails safely | pending |
| 6 | wrong token fail | request with wrong token fails safely | pending |
| 7 | allowed origin success | approved service.intelli-opus.com origin succeeds | pending |
| 8 | disallowed origin fail | non-allowlisted origin fails safely | pending |
| 9 | `PUBLIC_BASE_URL` correct | generated public URLs use approved staging base URL | pending |
| 10 | customer-safe payload has no forbidden fields | products, orders, resources, feedback, shipment, and Market Response preview contain no forbidden fields | pending |
| 11 | feedback submit does not auto-reply | feedback submission creates allowed state only; no automatic customer reply | pending |
| 12 | Portal read does not auto-change quote/order status | read operations do not change quote/order/shipment state | pending |
| 13 | no external notifications | no email/SMS/LinkedIn/customer/supplier notification is sent | pending |
| 14 | rollback drill | disable/revoke/origin rollback works safely | pending |

## Forbidden Fields During Payload Validation

The customer-safe payload must not contain:

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

## HOSUN Validation Condition

HOSUN staging validation may only expose business owner approved customer-safe fields for lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply:

- load
- stability
- noise
- delivery
- installation
- after-sales
- packaging
- warranty
- test cycle
- certification
- project demand

If any HOSUN field remains pending, it must stay out of customer-visible staging payloads.

## JOOBOO And Future Partner Validation Condition

JOOBOO and future partner staging validation must confirm sign-off for:

- education furniture
- school desks/chairs
- project furniture
- future partner onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields

If any field remains pending, it must stay internal-only or excluded.

## Rollback Drill

Rollback drill must confirm:

1. `PORTAL_CUSTOMER_API_ENABLED=false` disables bridge access.
2. Revoked token fails safely.
3. Wrong token fails safely.
4. Disallowed origin fails safely.
5. PartnerOS internal source of truth remains available.
6. No customer/supplier notification is sent during rollback.

## Boundary

- This plan is pending until real credentials exist.
- Do not write STAGING_VALIDATED until all real staging smoke tests pass and are reviewed.
- Do not enter D9.
- Do not create proof records.
- Do not fabricate endpoint, token, origin, evidence, reviewer, or sign-off.
- Do not process or record real token values.
