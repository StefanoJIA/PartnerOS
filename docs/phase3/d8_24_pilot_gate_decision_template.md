# D8.24 Pilot Gate Decision Template

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- Purpose: decide whether PartnerOS can move from rehearsal preparation to staging UAT or pilot
- Boundary: no D9 entry, no proof record expansion, no real staging validation claim

Use this template after real partner feedback, staging credentials, security review, and business UAT preparation are available.

## Gate Summary

- Decision date:
- Decision owner:
- Reviewed partners:
- Reviewed product focus:
- Related feedback board:
- Related UAT records:
- Security reviewer:
- Business owner:
- Final gate decision: allow staging UAT / allow pilot / hold / blocked

## Required Gate Questions

| Gate Question | Answer | Evidence / Notes | Owner |
| --- | --- | --- | --- |
| Is there real partner feedback? | no / yes / pending | No real partner feedback is recorded until actual rehearsal sessions occur. | partner owner |
| Are real staging credentials available? | no / yes / pending | Requires backend HTTPS origin, `PORTAL_CUSTOMER_API_TOKEN`, `PORTAL_CUSTOMER_ALLOWED_ORIGINS`, `PUBLIC_BASE_URL`, and real Portal origin. | infrastructure / backend operator |
| Is security review complete? | no / yes / pending | Must cover token, CORS, forbidden fields, logs, secret exposure, and customer-safe whitelist. | security reviewer |
| Is business UAT field approval complete? | no / yes / pending | Business owner must approve customer-visible fields and internal-only fields. | business owner |
| Are customer-safe fields confirmed? | no / yes / pending | Products, orders, production milestones, shipment status, resources, feedback status, and customer-safe Market Response preview. | business owner + security reviewer |
| Are forbidden fields still prohibited? | yes / no / pending | Cost, margin, pricing breakdown, supplier private notes, backend file paths, storage keys, token values, internal-only comments, private partner notes, and unsafe raw database IDs must remain prohibited. | security reviewer |
| Is there any P0 blocker? | yes / no / pending | Any P0 blocker prevents pilot. | pilot owner |
| Is staging UAT allowed? | no / yes / pending | Requires real credentials and security review. | decision owner |
| Is pilot allowed? | no / yes / pending | Requires staging UAT, business sign-off, and no unresolved P0 blocker. | decision owner |
| Does the system remain READY_FOR_STAGING_HANDOFF until external evidence exists? | yes / no | Must remain yes until external staging evidence exists. | release owner |
| Is writing STAGING_VALIDATED forbidden before real evidence? | yes / no | Must remain yes. | release owner |

## P0 Blocker Review

| P0 Item | Module | Partner | Blocker Type | Owner | Status | Gate Impact |
| --- | --- | --- | --- | --- | --- | --- |
| Real staging credentials | Portal bridge | all partners | staging credentials | infrastructure / backend operator | pending | blocks staging UAT |
| Security review | Portal bridge / forbidden fields | all partners | security review | security reviewer | pending | blocks staging UAT and pilot |
| Business UAT field approval | Portal / customer-visible fields | all partners | business sign-off | business owner | pending | blocks staging UAT and pilot |
| Real partner feedback | Rehearsal / feedback board | HOSUN / JOOBOO / Chongqing Huiju / future partner | partner data | partner owner | pending | blocks partner-specific pilot claim |

## HOSUN Gate Questions

Product focus:

- lifting systems
- desk frames
- desk legs
- lifting columns
- heavy-duty supply

Dimensions to review:

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

Gate questions:

- Which HOSUN fields are customer-safe?
- Which HOSUN fields are internal-only?
- Which HOSUN dimensions are Market Response signals?
- Which HOSUN dimensions are product expectations?
- Are there quote blockers?
- Are there order blockers?
- Are there pilot blockers?

## JOOBOO Gate Questions

Product focus:

- education furniture
- school desks/chairs
- project furniture

Dimensions to review:

- school procurement timing
- delivery consistency
- installation
- resource needs
- feedback after use
- project acceptance criteria

Gate questions:

- Which JOOBOO fields are customer-safe?
- Which JOOBOO fields are internal-only?
- Which dimensions affect project acceptance?
- Which dimensions affect resources or delivery?
- Are there quote, order, or pilot blockers?

## Future Partner Gate Questions

Review for Chongqing Huiju and future partner:

- onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields
- Market Response metrics

Gate questions:

- Is onboarding data complete enough for pilot?
- Are product families defined?
- Does quote logic require partner-specific rules?
- Are delivery requirements customer-visible or internal-only?
- Are resources reviewed for customer visibility?
- Are Market Response metrics partner-specific or shared?

## Gate Decision

Final decision:

- Allow staging UAT: no / yes / pending
- Allow pilot: no / yes / pending
- Remain READY_FOR_STAGING_HANDOFF: yes
- Do not write STAGING_VALIDATED: yes
- D9 remains gated: yes

Decision notes:

- 

## Sign-Off

- Decision owner:
- Security reviewer:
- Business owner:
- Partner owner:
- Date:

This template cannot be used to claim real staging validation without real external staging evidence.
