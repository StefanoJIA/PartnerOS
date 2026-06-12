# D8.22 Rehearsal to Roadmap Decision Log

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- Purpose: define how partner rehearsal feedback becomes D8.23, D9, Pilot, or Later roadmap decisions
- Boundary: no D9 entry, no proof record expansion, no real staging validation claim

This log is a decision framework. It does not implement features, connect real APIs, deploy staging, or process real tokens.

## Decision Flow

1. Capture feedback in `docs/demo/d8_22_partner_rehearsal_feedback_intake.md`.
2. Classify each issue in `docs/phase3/d8_22_pilot_readiness_matrix.md`.
3. Decide whether the item is P0, P1, P2, or P3.
4. Mark decision as do now, defer, needs feedback, or blocked.
5. Assign an owner.
6. Identify dependencies:
   - real staging credentials
   - security review
   - business owner sign-off
   - data model change
   - permission / RBAC change
   - partner-specific product field change
7. Only promote work into D8.23, D9, Pilot, or Later when dependencies are explicit.

## How Feedback Enters D8.23 / D9 / Pilot

### D8.23 Candidates

Use D8.23 for handoff and pilot readiness work that can happen before D9:

- staging credential follow-up
- security review closure
- business UAT record selection
- customer-safe field approval
- RBAC role matrix design
- audit taxonomy design
- real data import templates
- HOSUN metric dictionary
- JOOBOO metric dictionary
- documentation and demo wording corrections

D8.23 must remain pre-D9 unless real staging evidence and governance gates are complete.

### D9 Candidates

D9 should only receive work after real staging validation and production coordination gates are satisfied.

Do not move an item into D9 merely because partners liked the demo. D9 candidates must have:

- real staging evidence
- security review
- business owner sign-off
- production coordination owner
- rollback path
- no unresolved P0 blockers

### Pilot Candidates

Pilot candidates are items that require real usage but can remain controlled:

- limited customer Portal UAT
- selected partner/customer/product records
- campaign-to-quote operating loop
- quote/order/feedback/Market Response loop
- operator-only task and handoff improvements

Pilot items must not automatically send external messages or change quote/order status.

### Later Candidates

Move items to Later when they require platform maturity or external integrations:

- Constant Contact integration
- sales CRM / 销售易 integration
- email automation
- carrier integration
- accounting integration
- partner self-service Portal
- advanced forecasting or recommendation engine

## Feedback That Cannot Be Developed Immediately

Do not immediately develop feedback that requires:

- real staging credentials before validation
- security review before customer exposure
- token storage and rotation policy
- CORS/origin approval
- customer-safe whitelist approval
- RBAC role design
- audit log design
- production deployment planning
- external API credentials
- automatic email/SMS/LinkedIn/customer notification
- quote/order automatic status changes

Decision: blocked or defer until dependency is resolved.

## Feedback That Is Documentation or Demo Copy Only

These can usually be handled in D8.x without waiting for real staging:

- demo wording correction
- partner-specific talk track refinement
- field explanation in docs
- handoff checklist clarification
- partner rehearsal invite wording
- feedback intake form wording
- route explanation
- Chinese UI explanation text if small and non-functional

Decision: do now or defer based on priority.

## Feedback That Affects Data Model or Permissions

These require design review before implementation:

- new partner-specific product fields
- quote approval and margin review fields
- payment / PO / PI / contract fields
- partner self-service fields
- customer-visible resource permissions
- RBAC role-action matrix
- audit log event taxonomy
- customer-safe raw database ID replacement
- external system IDs

Decision: needs feedback or blocked until data model and permission design is approved.

## Feedback That Affects HOSUN / JOOBOO / Future Partner Product Fields

Use partner-specific product field changes only after deciding whether the field is:

- shared core field
- partner-specific internal field
- partner-specific customer-visible field
- Market Response metric
- quote/order blocker
- pilot blocker

Do not hardcode one partner's assumptions into the shared core.

## HOSUN Decision Dimensions

Product scope:

- lifting systems
- desk frames
- desk legs
- lifting columns
- heavy-duty supply

Feedback dimensions:

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

Decision categories:

- customer-safe feedback
- internal-only feedback
- Market Response signal
- product expectation
- quote/order/pilot blocker

HOSUN routing rules:

- Customer-safe feedback may become Portal wording or customer-facing summary after business and security review.
- Internal-only feedback remains inside PartnerOS and must not be exposed to Portal.
- Market Response signal can inform partner/product focus but remains advisory.
- Product expectation should update product field dictionaries or partner onboarding requirements.
- Quote/order/pilot blocker must become P0 or P1 in the pilot readiness matrix.

## JOOBOO Decision Dimensions

Product scope:

- education furniture
- school desks/chairs
- project furniture

Feedback dimensions:

- school procurement timing
- delivery consistency
- installation
- resource needs
- feedback after use
- project acceptance criteria

JOOBOO routing rules:

- Customer-safe project timing may become Portal wording after business review.
- Internal delivery and acceptance risks remain internal-only unless rewritten.
- Resource needs may become resource taxonomy work.
- Feedback after use should feed Market Response.
- Project acceptance criteria may affect quote/order/pilot readiness.

## Future Partner Decision Dimensions

Use for Chongqing Huiju and future partners:

- onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields
- Market Response metrics

Future partner routing rules:

- Onboarding data goes to Partner Onboarding.
- Product family goes to product catalog and campaign configuration.
- Quote logic goes to Quote and approval design.
- Delivery requirement goes to Order, production, and shipment workflow.
- Resource taxonomy goes to Resource Center and Portal whitelist review.
- Customer-visible fields require business owner and security sign-off.
- Market Response metrics become partner-specific signal dictionary entries.

## Decision Log Template

| Date | Partner | Feedback Summary | Classification | Dependency | Owner | Decision | Target Stage | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | HOSUN / JOOBOO / Chongqing Huiju / future partner |  | P0 / P1 / P2 / P3 | staging credentials / security review / business sign-off / data model / RBAC / none |  | do now / defer / needs feedback / blocked | D8.23 / D9 / Pilot / Later |  |

## Guardrails

- Do not enter D9 from rehearsal feedback alone.
- Do not add proof records from rehearsal feedback.
- Do not write a real staging validated status from local or rehearsal-only evidence.
- Do not connect real APIs from feedback intake.
- Do not automatically send email, SMS, LinkedIn, or customer notifications.
- Do not automatically change quote/order status.
- Do not expose cost, margin, pricing breakdown, supplier private notes, backend paths, storage keys, token values, internal-only comments, private partner notes, or unsafe raw database IDs.

## Decision Summary

D8.22 turns partner rehearsal feedback into structured decisions. The next valid step is D8.23 or controlled pilot preparation only after the relevant dependencies are explicit. The system remains READY_FOR_STAGING_HANDOFF until real staging credentials and external staging evidence exist.
