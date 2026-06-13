# D8.30 D9 Entry Gate

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
D9 gate status: blocked pending external evidence

This document defines the hard conditions for entering D9. D8.30 does not enter D9. If any required condition is missing, D9 remains blocked.

## Hard Entry Conditions

| Gate | Required Evidence | Status | Entry Rule |
| --- | --- | --- | --- |
| real backend HTTPS origin verified | HTTPS `/health` and readiness pass on real backend origin | pending | missing means no D9 |
| real Portal origin verified | service.intelli-opus.com real origin confirmed and allowed | pending | missing means no D9 |
| `PORTAL_CUSTOMER_API_TOKEN` securely configured | token configured through secure channel and never recorded in repo | pending | missing means no D9 |
| allowed origins verified | approved origin succeeds and no wildcard is used | pending | missing means no D9 |
| `PUBLIC_BASE_URL` verified | public URLs use approved staging base URL | pending | missing means no D9 |
| security signoff approved | real security reviewer signs off | pending | missing means no D9 |
| business owner signoff approved | real business owner signs off customer-visible fields and wording | pending | missing means no D9 |
| UAT seed data approved | staging-safe seed records approved | pending | missing means no D9 |
| real staging smoke test passed | all D8.29 smoke tests pass with reviewed evidence | pending | missing means no D9 |
| forbidden fields absent | payload audit confirms no forbidden fields | pending | missing means no D9 |
| rollback drill passed | disable/revoke/origin rollback verified | pending | missing means no D9 |
| no P0 blockers | no unresolved security, data, staging, or partner blocker | pending | missing means no D9 |

## D9 Decision Rule

All gates must be present, reviewed, and passed before D9 may be considered. If any one item is pending, rejected, blocked, or unreviewed, the project remains READY_FOR_STAGING_HANDOFF and external staging remains WAITING_FOR_REAL_STAGING_EVIDENCE.

## D9 Entry Is Forbidden When

- credentials are pending
- smoke evidence is pending
- security signoff is pending
- business owner signoff is pending
- UAT seed data is pending
- rollback owner is missing
- P0 blockers remain
- any forbidden field appears in customer-facing Portal payload
- any automatic external notification is observed
- any Portal read mutates quote/order/shipment state

## HOSUN D9 Gate

HOSUN cannot enter D9/customer-visible pilot unless business owner and security reviewer approve customer-safe fields and internal-only exclusions for lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply.

Fields requiring approval before customer-visible use:

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

## JOOBOO And Future Partner D9 Gate

JOOBOO and future partner pilot data cannot enter D9 unless sign-off is complete for:

- education furniture
- school desks/chairs
- project furniture
- future partner onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields
- Market Response metrics

## Boundary

- D8.30 does not enter D9.
- Do not write STAGING_VALIDATED.
- Do not create proof records.
- Do not fabricate credentials, evidence, sign-off, or partner feedback.
- Pending does not mean approved.
