# D8.30 No-Go Conditions

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE

This document defines conditions that block real staging UAT, D9 entry, or pilot. Any one no-go condition is sufficient to stop progression.

## Hard No-Go Conditions

| No-Go Condition | Why It Blocks | Required Response |
| --- | --- | --- |
| local-only test is treated as staging evidence | local evidence cannot prove service.intelli-opus.com staging behavior | keep WAITING_FOR_REAL_STAGING_EVIDENCE |
| dry-run is treated as real validation | dry-run does not use real credentials or real Portal origin | keep READY_FOR_STAGING_HANDOFF |
| pending is written as approved | creates false approval state | revert wording to pending and require real sign-off |
| token appears in Git/docs/logs/screenshots/chat | secret exposure risk | revoke/rotate token and stop staging UAT |
| forbidden fields appear in Portal payload | customer-safe contract breach | disable Portal API and remove exposure |
| automatic email/SMS/LinkedIn/customer notification occurs | violates D8 safety boundary | stop flow and disable risky integration |
| quote/order is automatically changed | violates read-only/customer-safe Portal boundary | disable Portal bridge and restore state |
| rollback owner is missing | cannot safely disable staging on failure | assign owner before proceeding |
| security signoff is missing | security gate incomplete | do not proceed |
| business signoff is missing | customer-visible field gate incomplete | do not proceed |
| partner feedback or sign-off is fabricated | invalid evidence and governance failure | remove fabricated content |
| STAGING_VALIDATED is written before real evidence | false status claim | revert status claim |
| D9 is entered before all gates pass | phase boundary breach | return to READY_FOR_STAGING_HANDOFF |

## Forbidden Field No-Go List

Portal payload must not expose:

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

## HOSUN No-Go Conditions

D9 or customer-visible pilot is blocked if HOSUN lifting systems, desk frames, desk legs, lifting columns, or heavy-duty supply expose unapproved customer-facing fields.

The following must not be shown to customers without business owner and security reviewer approval:

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

HOSUN internal-only content must remain blocked:

- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- supplier private notes
- internal Market Response scoring/ranking

## JOOBOO And Future Partner No-Go Conditions

D9 or pilot is blocked if sign-off is missing for:

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

- No-go conditions are active while external inputs remain pending.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not fabricate credentials, evidence, sign-off, or partner feedback.
- Do not process or record real token values.
