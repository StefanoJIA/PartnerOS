# D8.26 Business Owner Sign-off Checklist

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Sign-off status: pending / approved / changes required

No real business owner sign-off recorded yet. This checklist is an execution template for a future business owner review session. Until a real responsible owner completes the checklist, every data record, field, resource, and wording item remains pending and must not be written as approved.

## Sign-off Session Information

| Field | Value |
| --- | --- |
| Owner | pending |
| Date | pending |
| Scope | partner rehearsal / staging UAT / pilot |
| Partner | HOSUN / JOOBOO / Chongqing Huiju / future partner / pending |
| Product family | pending |
| Customer segment | pending |
| Reviewer notes | pending |
| Sign-off status | pending / approved / changes required |

## Customer-Visible Fields Checklist

| Item | Review Question | Status | Notes |
| --- | --- | --- | --- |
| product names | Are customer-visible product names approved? | pending | pending |
| product specifications | Are visible specs approved and supported? | pending | pending |
| customer segment | Is the segment safe to show without identifying a real customer? | pending | pending |
| quote summary | Does the quote summary avoid cost, margin, and pricing breakdown? | pending | pending |
| order summary | Does the order summary avoid unsafe raw IDs and internal notes? | pending | pending |
| production status | Are planned/completed statuses clear and customer-safe? | pending | pending |
| shipment status | Is shipment risk rewritten into customer-safe wording? | pending | pending |
| feedback status | Is feedback summarized without complaint details or private comments? | pending | pending |
| Market Response preview | Is the signal high-level and free of internal scoring/ranking? | pending | pending |

## Forbidden Fields Checklist

Each item must remain blocked from customer-facing Portal, partner-facing screenshots, rehearsal copy, staging seeds, and pilot handoff unless a future security and business review explicitly changes the rule.

| Forbidden Field | Still Blocked? | Notes |
| --- | --- | --- |
| cost | pending | Must remain internal-only |
| margin | pending | Must remain internal-only |
| pricing breakdown | pending | Must remain internal-only |
| supplier private notes | pending | Must remain internal-only |
| internal comments | pending | Must remain internal-only |
| private partner notes | pending | Must remain internal-only |
| backend paths | pending | Must remain internal-only |
| storage keys | pending | Must remain internal-only |
| token values | pending | Must remain internal-only |
| unsafe raw database IDs | pending | Must remain internal-only |

## Approved Products Checklist

| Partner | Product Family | Candidate Use | Status | Required Evidence |
| --- | --- | --- | --- | --- |
| HOSUN | lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply | partner rehearsal / staging UAT / pilot | pending | business wording and supporting product material |
| JOOBOO | education furniture / school desks/chairs / project furniture | partner rehearsal / staging UAT / pilot | pending | business wording and project furniture material |
| Chongqing Huiju | pending | partner rehearsal / staging UAT / pilot | pending | partner-specific product field review |
| future partner | onboarding data / product family | partner rehearsal / staging UAT / pilot | pending | onboarding field review |

## Approved Customer Segments Checklist

| Segment | Intended Use | Status | Required Review |
| --- | --- | --- | --- |
| HOSUN distributor or project buyer | rehearsal / staging UAT / pilot | pending | Confirm no real customer identity is exposed |
| JOOBOO school, institution, or project buyer | rehearsal / staging UAT / pilot | pending | Confirm procurement context is sanitized |
| future partner segment | rehearsal / staging UAT / pilot | pending | Confirm partner-specific segment wording |

## Approved Orders Checklist

| Order Candidate | Partner | Intended Use | Status | Required Review |
| --- | --- | --- | --- | --- |
| HOSUN order sample | HOSUN | demo / rehearsal / staging UAT / pilot | pending | Remove PO, PI, contract terms, pricing breakdown, supplier notes |
| JOOBOO order sample | JOOBOO | demo / rehearsal / staging UAT / pilot | pending | Remove real school/institution identity and private delivery notes |
| future partner order sample | future partner | demo / rehearsal / staging UAT / pilot | pending | Confirm quote logic and delivery requirement visibility |

## Approved Feedback Records Checklist

| Feedback Candidate | Partner | Intended Use | Status | Required Review |
| --- | --- | --- | --- | --- |
| HOSUN feedback sample | HOSUN | demo / rehearsal / staging UAT / pilot | pending | Remove complaint details, warranty cost exposure, raw test notes |
| JOOBOO feedback sample | JOOBOO | demo / rehearsal / staging UAT / pilot | pending | Remove private project acceptance and buyer identity |
| future partner feedback sample | future partner | demo / rehearsal / staging UAT / pilot | pending | Confirm customer-visible feedback summary |

## Approved Market Response Preview Checklist

| Preview Candidate | Partner | Intended Use | Status | Required Review |
| --- | --- | --- | --- | --- |
| HOSUN lifting systems signal | HOSUN | partner rehearsal / staging UAT / pilot | pending | Must avoid internal scoring, ranking, delivery risk analysis, warranty cost exposure |
| JOOBOO project furniture signal | JOOBOO | partner rehearsal / staging UAT / pilot | pending | Must avoid procurement negotiation and private partner notes |
| future partner signal | future partner | partner rehearsal / staging UAT / pilot | pending | Must define partner-specific Market Response metrics |

## Approved Resources Checklist

| Resource Candidate | Partner | Intended Use | Status | Required Review |
| --- | --- | --- | --- | --- |
| product sheet | HOSUN / JOOBOO / future partner | demo / rehearsal / staging UAT / pilot | pending | No backend paths, storage keys, draft files, or unsupported claims |
| installation guide | HOSUN / JOOBOO / future partner | demo / rehearsal / staging UAT / pilot | pending | Customer-safe installation wording only |
| warranty summary | HOSUN / JOOBOO / future partner | demo / rehearsal / staging UAT / pilot | pending | Warranty wording must be business-confirmed |
| case material | HOSUN / JOOBOO / future partner | demo / rehearsal / staging UAT / pilot | pending | Remove real customer identities unless separately approved |

## Pilot Entry Condition Checklist

| Condition | Status | Notes |
| --- | --- | --- |
| Real business owner sign-off completed | pending | No real sign-off recorded yet |
| Customer-safe fields approved | pending | pending |
| Forbidden fields confirmed blocked | pending | pending |
| Staging-safe seed records selected | pending | pending |
| Security review completed | pending | pending |
| Real staging credentials available | pending | backend HTTPS origin, token, allowed origin, PUBLIC_BASE_URL |
| service Portal staging smoke passed | pending | Must not write STAGING_VALIDATED before real evidence |
| Pilot partner selected | pending | pending |
| Pilot product family selected | pending | pending |
| Pilot customer segment selected | pending | pending |

## Boundary

- Pending does not mean approved.
- No real business owner sign-off recorded yet.
- Do not enter D9.
- Do not create proof records.
- Do not write STAGING_VALIDATED.
- Do not fabricate real sign-off.
- Do not fabricate real partner feedback.
- Do not automatically send email, SMS, LinkedIn, customer notification, supplier notification, webhook, or carrier request.
- Do not automatically change quote or order status.
