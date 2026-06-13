# D8.32 External Action Tracker Dry-Run

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Dry-run status: template only

No external message has been sent from this dry-run. No real reply, credentials, evidence, sign-off, or partner feedback is recorded here. All placeholder actions remain `status=pending`.

## Dry-Run Tracker

| Action ID | Action Type | Owner Role | Target | Dependency | Expected Response | Next Step | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MSG-001 | partner rehearsal | business owner / presenter | HOSUN | D8.32 partner rehearsal message, D8.18 demo script | available time, attendees, product focus, questions | manually send invitation when owner approves | pending |
| MSG-002 | partner rehearsal | business owner / presenter | JOOBOO | D8.32 partner rehearsal message, D8.18 demo script | available time, education/project furniture focus, questions | manually send invitation when owner approves | pending |
| MSG-003 | partner rehearsal | business owner / presenter | Chongqing Huiju / future partner | D8.32 partner rehearsal message | target stakeholder, product family, questions | identify stakeholder and manually send | pending |
| MSG-004 | business signoff | business owner | HOSUN UAT data | D8.32 business UAT signoff message, D8.25-D8.26 docs | customer-safe wording approval or changes required | manually request sign-off | pending |
| MSG-005 | business signoff | business owner | JOOBOO UAT data | D8.32 business UAT signoff message, D8.25-D8.26 docs | approved fields or changes required | manually request sign-off | pending |
| MSG-006 | business signoff | business owner | future partner UAT data | D8.32 business UAT signoff message | approved onboarding/product/field model or changes required | manually request sign-off | pending |
| MSG-007 | security review | security reviewer | Portal bridge | D8.32 security review request, D8.27 docs | required fixes, signoff status, rollback review | manually send security request | pending |
| MSG-008 | credentials request | infrastructure / backend operator | PartnerOS staging backend | D8.32 staging credentials request, D8.28 docs | backend HTTPS origin, owner, staging window, rollback owner | manually request credentials | pending |
| MSG-009 | credentials request | Portal operator | service.intelli-opus.com | D8.32 staging credentials request, D8.28 docs | real Portal origin, allowed origin expectations | manually request Portal confirmation | pending |
| MSG-010 | staging smoke | backend operator + security reviewer | real staging | D8.29 smoke test plan and evidence template | redacted smoke evidence after credentials arrive | wait for credentials/signoff; do not execute yet | pending |

## HOSUN Dry-Run Coverage

HOSUN messages must cover lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply, load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, and project demand. Customer-safe and internal-only fields require sign-off.

## JOOBOO / Future Partner Dry-Run Coverage

JOOBOO messages must cover education furniture, school desks/chairs, project furniture, school procurement timing, delivery consistency, installation, resource needs, feedback after use, and project acceptance criteria.

Future partner messages must cover onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, and Market Response metrics.

## Boundary

- No external message has been sent from this dry-run.
- Status remains pending for every placeholder action.
- Pending does not mean complete or approved.
- Do not fabricate replies, credentials, evidence, sign-off, or partner feedback.
- Do not process or record real token values.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
