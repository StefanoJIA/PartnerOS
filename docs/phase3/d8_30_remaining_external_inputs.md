# D8.30 Remaining External Inputs

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
External input status: pending

No real staging credentials, evidence, sign-off, or partner feedback are recorded in this repository. This document lists external inputs still required before real staging UAT, pilot, or D9 consideration.

## External Inputs

| Input | Owner | Status | Dependency | Next Action |
| --- | --- | --- | --- | --- |
| staging credentials | infrastructure / backend operator / approved secret owner | pending | secure channel and security reviewer | provide backend HTTPS origin, token, allowed origins, PUBLIC_BASE_URL without recording secrets in repo |
| security reviewer signoff | security reviewer | pending | D8.27 checklist, D8.28 credentials, D8.29 smoke evidence | review token/CORS/logs/forbidden fields/rollback after credentials arrive |
| business owner signoff | business owner | pending | D8.25-D8.26 data and wording checklists | approve customer-visible fields, UAT seed data, HOSUN/JOOBOO/future partner wording |
| partner rehearsal feedback | HOSUN / JOOBOO / Chongqing Huiju / future partner stakeholders | pending | partner-facing rehearsal session | capture real partner quotes without inventing feedback |
| UAT seed records | business owner + operator | pending | staging-safe manifest and sign-off | select demo/rehearsal/staging UAT/pilot records |
| Portal operator confirmation | service.intelli-opus.com portal operator | pending | real Portal origin and bridge expectations | confirm origin, CORS expectations, and Portal behavior |
| infrastructure deployment window | infrastructure / deployment operator | pending | staging credentials and rollback owner | schedule staging configuration and smoke execution window |
| rollback owner | infrastructure / backend operator | pending | D8.28 and D8.29 rollback procedures | name owner responsible for disabling Portal API and revoking token |

## Partner-Specific External Inputs

| Partner | Required External Input | Status | Next Action |
| --- | --- | --- | --- |
| HOSUN | business owner + security reviewer approval for lifting systems fields | pending | approve or exclude load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, project demand |
| JOOBOO | business owner approval for education/project furniture fields | pending | approve or exclude education furniture, school desks/chairs, project furniture, procurement timing, delivery consistency, installation, resource needs, feedback after use, project acceptance criteria |
| future partner | onboarding and field model approval | pending | approve onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, Market Response metrics |

## Boundary

- External inputs are pending.
- Pending does not mean approved.
- Do not invent credentials, evidence, sign-off, or partner feedback.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not process or record real token values.
