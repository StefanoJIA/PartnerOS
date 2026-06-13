# D8.29 Staging Failure Triage

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Triage status: pending real smoke execution

No real staging evidence recorded yet. This triage guide defines failure categories and response owners for future real staging smoke tests. Any failed or pending category must not be described as validated.

## Failure Matrix

| Failure Category | Impact | Owner | Rollback Step | Do Not Claim Validated |
| --- | --- | --- | --- | --- |
| network / DNS / TLS | service Portal cannot reach backend HTTPS origin or certificate is invalid | infrastructure / deployment operator | keep Portal API disabled; confirm internal PartnerOS remains available | do not claim validated |
| backend health | `/health` fails or backend runtime is unstable | intelliOffice backend operator | stop staging UAT; disable Portal API if enabled | do not claim validated |
| migration/database | database not ready or migration not at head | intelliOffice backend operator | disable Portal API; keep staging read-only or offline | do not claim validated |
| token auth | correct token fails, missing token succeeds, or wrong token succeeds | security reviewer + backend operator | revoke/rotate token; set `PORTAL_CUSTOMER_API_ENABLED=false` | do not claim validated |
| CORS/origin | allowed origin fails or disallowed origin succeeds | security reviewer + portal operator | clear or restrict `PORTAL_CUSTOMER_ALLOWED_ORIGINS` | do not claim validated |
| forbidden field exposure | customer payload exposes forbidden fields | security reviewer + backend operator | disable Portal API; remove field exposure before retest | do not claim validated |
| unsafe customer copy | payload uses unapproved wording or exposes internal responsibility/risk | business owner + security reviewer | remove customer-visible field or revert to pending wording | do not claim validated |
| automatic external action risk | feedback/read/Portal action may send email/SMS/LinkedIn/customer/supplier notification | backend operator + security reviewer | disable risky flow; confirm no notification was sent | do not claim validated |
| quote/order status mutation risk | Portal read changes quote/order/shipment state | backend operator | disable Portal bridge; restore state from internal source of truth if needed | do not claim validated |
| rollback failure | disable/revoke/origin rollback does not work | infrastructure / backend operator + security reviewer | isolate Portal bridge and block external access | do not claim validated |

## Triage Workflow

1. Stop the affected smoke test.
2. Record only redacted endpoint, request id, and failure category.
3. Do not paste token values, raw `.env`, secret screenshots, or sensitive logs.
4. Assign owner and rollback step.
5. Disable Portal API if customer-safe field exposure or auth/CORS risk exists.
6. Fix locally or in staging according to owner scope.
7. Retest only the failed category and any dependent categories.
8. Keep status as WAITING_FOR_REAL_STAGING_EVIDENCE until all required real smoke tests pass and are reviewed.

## HOSUN Failure Triggers

HOSUN staging smoke must fail if customer-facing payload exposes:

- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- supplier private notes
- internal scoring
- internal Market Response scoring/ranking

HOSUN staging smoke must also fail if customer-safe fields such as load range, stability summary, noise claim, delivery window, installation summary, after-sales support, warranty summary, test cycle summary, certification summary, or packaging summary appear without business sign-off.

## Boundary

- A failed smoke test does not block PartnerOS internal source of truth.
- A pending smoke test does not count as validated.
- A local script pass does not count as real staging evidence.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not fabricate credentials, evidence, or sign-off.
