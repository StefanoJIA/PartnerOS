# D8.29 Real-Staging Smoke Test Plan

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Smoke test status: pending real credentials

No real staging evidence recorded yet. This plan converts the D8.28 secure validation plan into a real-staging smoke test sequence that can be executed only after real credentials, real origin values, security sign-off, and business owner sign-off are available through approved channels. It does not deploy, does not call real APIs, does not handle real tokens, and does not write STAGING_VALIDATED.

## Preconditions

Before execution, the operator must confirm:

- backend HTTPS origin is provided through approved channel
- service.intelli-opus.com real origin is provided through approved channel
- `PORTAL_CUSTOMER_API_ENABLED=true` is configured only in staging
- `PORTAL_CUSTOMER_API_TOKEN` is configured securely and not recorded
- `PORTAL_CUSTOMER_ALLOWED_ORIGINS` contains explicit approved origins and no wildcard
- `PUBLIC_BASE_URL` is configured for staging
- security sign-off is available
- business owner sign-off is available for staged customer-safe data
- rollback owner is assigned
- no P0 blockers remain

If any prerequisite is missing, the test remains pending.

## Test Sequence

| Step | Test | Expected Result | Evidence Required | Status |
| --- | --- | --- | --- | --- |
| 1 | backend HTTPS `/health` | Backend responds healthy over approved HTTPS origin | redacted endpoint, status code, timestamp | pending |
| 2 | migration/database ready | Database lifecycle and migration status are ready/head | redacted readiness output | pending |
| 3 | Portal bridge readiness | Portal bridge reports safe configured state | redacted readiness response | pending |
| 4 | `enabled=true` only in staging | Customer Portal API is enabled only in staging | redacted config status | pending |
| 5 | correct token success | Server-to-server request with correct token succeeds | redacted request id and response status | pending |
| 6 | missing token fail | Request without token fails safely | redacted request id and failure status | pending |
| 7 | wrong token fail | Request with wrong token fails safely | redacted request id and failure status | pending |
| 8 | allowed origin success | Approved service.intelli-opus.com origin succeeds | redacted origin status | pending |
| 9 | disallowed origin fail | Non-allowlisted origin fails safely | redacted origin status | pending |
| 10 | `PUBLIC_BASE_URL` correct | Public URLs use approved staging base URL | redacted URL sample | pending |
| 11 | customer-safe payload check | products/orders/order detail/resources/feedback/market preview are customer-safe | redacted payload audit | pending |
| 12 | forbidden fields absent | No forbidden fields appear in customer-facing payloads | field audit summary | pending |
| 13 | feedback submit does not auto-reply | Feedback submission does not automatically reply to customers | event/log reference without secrets | pending |
| 14 | Portal read does not auto-change quote/order status | Read-only Portal access does not mutate quote/order state | before/after status comparison | pending |
| 15 | no external notifications | No email/SMS/LinkedIn/customer/supplier notification is sent | notification audit summary | pending |
| 16 | rollback / disable drill | Portal API can be disabled and token/origin access revoked safely | rollback evidence without secrets | pending |

## Customer-Safe Payload Scope

The smoke test must cover customer-safe fields for:

- products
- orders
- order detail
- resources
- feedback
- Market Response preview
- production milestones
- shipment status

## Forbidden Fields

The payload audit must confirm absence of:

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

## HOSUN Payload Boundary

HOSUN customer-safe payload must not expose:

- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- supplier private notes
- internal scoring
- internal Market Response scoring/ranking

HOSUN customer-safe fields may be tested only when business owner sign-off exists:

- product family
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

- This plan is pending until real credentials arrive.
- Script pass, template pass, local test, or dry-run does not count as real staging evidence.
- Do not write STAGING_VALIDATED before all real smoke tests pass and are reviewed.
- Do not enter D9.
- Do not create proof records.
- Do not fabricate endpoint, token, origin, evidence, reviewer, or sign-off.
- Do not process or record real token values.
