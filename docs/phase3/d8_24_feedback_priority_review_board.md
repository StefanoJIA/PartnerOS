# D8.24 Feedback Priority Review Board

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- Purpose: convert partner rehearsal feedback into priority, roadmap, and pilot decisions
- Boundary: no D9 entry, no proof record expansion, no real staging validation claim, no fabricated partner feedback

This review board is for real partner rehearsal feedback after it has been captured with the D8.22 intake and D8.23 execution log. Until real sessions happen, real partner quote rows must remain pending.

## Source Type Values

- real partner quote
- internal observation
- system issue
- roadmap candidate

Internal observations and system issues may be recorded, but they are not partner feedback.

## Partner Values

- HOSUN
- JOOBOO
- Chongqing Huiju
- future partner
- internal

## Priority Values

- P0: staging / pilot 前必须解决
- P1: partner rehearsal 后优先做
- P2: pilot 期间增强
- P3: 长期平台能力

## Dependency Values

- staging credentials
- security review
- business sign-off
- partner data
- none

## Decision Values

- do now
- defer
- needs more feedback
- blocked

## Review Board

| Feedback ID | Source Type | Partner | Product Focus | Original Quote or Observation | Related Module | Impact | Risk | Priority | Dependency | Decision | Owner | Due Date | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D8.24-PENDING-HOSUN-001 | real partner quote | HOSUN | lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply | pending real partner session | Market Response / Product Fields / Quote / Order | pending | pending | P1 | partner data | needs more feedback | pending | pending | pending |
| D8.24-PENDING-JOOBOO-001 | real partner quote | JOOBOO | education furniture / school desks/chairs / project furniture | pending real partner session | Market Response / Product Fields / Order / Resources | pending | pending | P1 | partner data | needs more feedback | pending | pending | pending |
| D8.24-PENDING-HUIJU-001 | real partner quote | Chongqing Huiju | pending product family | pending real partner session | Partner Onboarding / Product Fields | pending | pending | P1 | partner data | needs more feedback | pending | pending | pending |
| D8.24-PENDING-FUTURE-001 | real partner quote | future partner | pending product family | pending real partner session | Partner Onboarding / Product Fields / Market Response | pending | pending | P2 | partner data | needs more feedback | pending | pending | pending |
| D8.24-INTERNAL-001 | internal observation | internal | PartnerOS rehearsal flow | Internal observation: review board is ready, but real partner quote rows remain pending. | Documentation / Pilot Readiness | Keeps feedback routing disciplined. | Risk of confusing dry-run with partner feedback if rules are ignored. | P0 | none | do now | intelliOffice operator | pending | ready |

## HOSUN Review Dimensions

Use for HOSUN lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply.

| Dimension | Review Notes | Customer-Safe Feedback | Internal-Only Feedback | Market Response Signal | Product Expectation | Quote Blocker | Order Blocker | Pilot Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| load | pending real HOSUN feedback |  |  |  |  |  |  |  |
| stability | pending real HOSUN feedback |  |  |  |  |  |  |  |
| noise | pending real HOSUN feedback |  |  |  |  |  |  |  |
| delivery | pending real HOSUN feedback |  |  |  |  |  |  |  |
| installation | pending real HOSUN feedback |  |  |  |  |  |  |  |
| after-sales | pending real HOSUN feedback |  |  |  |  |  |  |  |
| packaging | pending real HOSUN feedback |  |  |  |  |  |  |  |
| warranty | pending real HOSUN feedback |  |  |  |  |  |  |  |
| test cycle | pending real HOSUN feedback |  |  |  |  |  |  |  |
| certification | pending real HOSUN feedback |  |  |  |  |  |  |  |
| project demand | pending real HOSUN feedback |  |  |  |  |  |  |  |

## JOOBOO Review Dimensions

Use for JOOBOO education furniture, school desks/chairs, and project furniture.

| Dimension | Review Notes | Customer-Safe Feedback | Internal-Only Feedback | Market Response Signal | Product Expectation | Quote Blocker | Order Blocker | Pilot Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| school procurement timing | pending real JOOBOO feedback |  |  |  |  |  |  |  |
| delivery consistency | pending real JOOBOO feedback |  |  |  |  |  |  |  |
| installation | pending real JOOBOO feedback |  |  |  |  |  |  |  |
| resource needs | pending real JOOBOO feedback |  |  |  |  |  |  |  |
| feedback after use | pending real JOOBOO feedback |  |  |  |  |  |  |  |
| project acceptance criteria | pending real JOOBOO feedback |  |  |  |  |  |  |  |

## Future Partner Review Dimensions

Use for Chongqing Huiju and future partner feedback.

| Dimension | Review Notes | Customer-Safe Feedback | Internal-Only Feedback | Roadmap Impact | Pilot Blocker |
| --- | --- | --- | --- | --- | --- |
| onboarding data | pending real partner feedback |  |  |  |  |
| product family | pending real partner feedback |  |  |  |  |
| quote logic | pending real partner feedback |  |  |  |  |
| delivery requirement | pending real partner feedback |  |  |  |  |
| resource taxonomy | pending real partner feedback |  |  |  |  |
| customer-visible fields | pending real partner feedback |  |  |  |  |
| Market Response metrics | pending real partner feedback |  |  |  |  |

## Review Rules

- A real partner quote must include session id, partner, attendee or role, date, and original words.
- Internal observations must stay labeled as internal observation.
- System issues must be routed to next action queue.
- Roadmap candidates must be routed to pilot readiness matrix.
- Anything involving token, CORS, customer-safe fields, or forbidden fields requires security review.
- Anything involving customer-visible fields requires business sign-off.
- Do not move any item to D9 while the system remains READY_FOR_STAGING_HANDOFF and external staging remains WAITING_FOR_REAL_STAGING_EVIDENCE.
