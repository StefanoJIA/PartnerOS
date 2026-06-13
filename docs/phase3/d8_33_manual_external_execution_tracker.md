# D8.33 Manual External Execution Tracker

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Tracker status: manual tracker template, no external message sent

No external message has been sent from this tracker. No real reply, credentials, evidence, sign-off, or partner feedback is recorded here. If a message has not been manually sent, status must remain `draft` or `ready to send`.

## Allowed Status Values

Only these status values are allowed:

- draft
- ready to send
- sent manually
- response received
- blocked
- complete

Do not use `approved` as a tracker status. Approval must be recorded only inside the relevant sign-off record with owner, date, and scope.

## Manual External Execution Tracker

| Action ID | Action Type | Recipient Role | Target Partner/System | Sent By | Sent Date | Channel | Expected Response | Dependency | Status | Next Step | Owner | Due Date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D8.33-001 | partner rehearsal request | partner stakeholder / business owner | HOSUN | pending | pending | pending | available time, attendees, product focus, questions | D8.32 partner rehearsal message | draft | prepare manual send | business owner / presenter | pending |
| D8.33-002 | partner rehearsal request | partner stakeholder / business owner | JOOBOO | pending | pending | pending | available time, education/project furniture focus, questions | D8.32 partner rehearsal message | draft | prepare manual send | business owner / presenter | pending |
| D8.33-003 | partner rehearsal request | partner stakeholder / business owner | Chongqing Huiju / future partner | pending | pending | pending | target stakeholder, product family, questions | D8.32 partner rehearsal message | draft | identify recipient | business owner / presenter | pending |
| D8.33-004 | business UAT / data sign-off request | business owner | HOSUN UAT data | pending | pending | pending | field approval or changes required | D8.32 business UAT signoff message | ready to send | manually send when owner confirms | business owner | pending |
| D8.33-005 | business UAT / data sign-off request | business owner | JOOBOO UAT data | pending | pending | pending | field approval or changes required | D8.32 business UAT signoff message | ready to send | manually send when owner confirms | business owner | pending |
| D8.33-006 | business UAT / data sign-off request | business owner | future partner UAT data | pending | pending | pending | field approval or changes required | D8.32 business UAT signoff message | draft | define target partner scope | business owner | pending |
| D8.33-007 | security review request | security reviewer | Portal bridge | pending | pending | pending | required fixes, signoff status, rollback review | D8.32 security review request | ready to send | manually send when reviewer is assigned | security reviewer | pending |
| D8.33-008 | staging credentials request | infrastructure / backend operator | PartnerOS staging backend | pending | pending | pending | backend HTTPS origin, owner, staging window, rollback owner | D8.32 staging credentials request | ready to send | manually send through approved channel | backend operator | pending |
| D8.33-009 | staging credentials request | Portal operator | service.intelli-opus.com | pending | pending | pending | real Portal origin, allowed origin expectations | D8.32 staging credentials request | ready to send | manually send through approved channel | Portal operator | pending |

## HOSUN Tracking Scope

HOSUN actions must track whether replies address lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply, load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, and project demand. Any HOSUN technical claim must be classified as customer-safe candidate, needs validation, internal-only, or pilot blocker.

## JOOBOO And Future Partner Tracking Scope

JOOBOO actions must track education furniture, school desks/chairs, project furniture, school procurement timing, delivery consistency, installation, resource needs, feedback after use, and project acceptance criteria.

Future partner actions must track onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, and Market Response metrics.

## Boundary

- No external message has been sent from this tracker.
- Do not mark response received without a real reply pasted by the user.
- Do not mark complete without required owner/date/scope and resolved next action.
- Do not fabricate external replies, credentials, evidence, sign-off, or partner feedback.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not process or record real token values.
