# D8.31 Next External Actions Tracker

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Tracker status: pending external execution

No real external action is recorded as complete in this tracker. Pending must not be written as complete.

## Status Values

Allowed status values:

- pending
- requested
- received
- blocked
- complete

## Action Tracker

| Action ID | Action Type | Owner | Target Partner or System | Dependency | Status | Due Date | Next Step |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXT-001 | partner rehearsal | business owner / presenter | HOSUN | D8.18 rehearsal pack and D8.23 execution log | pending | pending | schedule rehearsal; capture real partner quotes |
| EXT-002 | partner rehearsal | business owner / presenter | JOOBOO | D8.18 rehearsal pack and D8.23 execution log | pending | pending | schedule rehearsal; capture education/project furniture feedback |
| EXT-003 | partner rehearsal | business owner / presenter | Chongqing Huiju / future partner | D8.18 future partner narrative | pending | pending | identify target stakeholder and schedule |
| EXT-004 | business signoff | business owner | HOSUN UAT data | D8.25-D8.26 UAT/signoff docs | pending | pending | review customer-safe/internal-only HOSUN fields |
| EXT-005 | business signoff | business owner | JOOBOO UAT data | D8.25-D8.26 UAT/signoff docs | pending | pending | review education furniture/project furniture fields |
| EXT-006 | business signoff | business owner | future partner UAT data | D8.25-D8.26 UAT/signoff docs | pending | pending | review onboarding data and product field model |
| EXT-007 | security review | security reviewer | Portal bridge | D8.27 security readiness package | pending | pending | review token/CORS/logs/forbidden fields/rollback |
| EXT-008 | credentials request | infrastructure / backend operator | staging backend | D8.28 credentials intake playbook | pending | pending | request backend HTTPS origin, token, allowed origins, PUBLIC_BASE_URL through secure channels |
| EXT-009 | credentials request | Portal operator | service.intelli-opus.com | D8.28 credentials intake playbook | pending | pending | confirm real Portal origin and CORS expectations |
| EXT-010 | staging smoke | backend operator + security reviewer | real staging | D8.29 smoke plan and evidence template | pending | pending | execute only after credentials/signoff are available |
| EXT-011 | staging smoke | rollback owner | Portal bridge rollback | D8.29 rollback drill | pending | pending | assign rollback owner and verify disable/revoke plan |

## Partner-Specific Tracking Notes

HOSUN action items must cover lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply, load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, and project demand.

JOOBOO action items must cover education furniture, school desks/chairs, project furniture, school procurement timing, delivery consistency, installation, resource needs, feedback after use, and project acceptance criteria.

Future partner action items must cover onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, and Market Response metrics.

## Boundary

- Do not mark pending as complete.
- Do not fabricate partner feedback.
- Do not fabricate credentials, evidence, or sign-off.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not process or record real token values.
