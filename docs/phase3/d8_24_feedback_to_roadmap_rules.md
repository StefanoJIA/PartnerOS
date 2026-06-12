# D8.24 Feedback to Roadmap Rules

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- Purpose: define how feedback becomes roadmap or pilot decisions
- Boundary: no D9 entry, no proof record expansion, no real staging validation claim

## Core Rules

1. Do not treat internal dry-run as partner feedback.
2. Do not treat presenter guess as a real requirement.
3. Real partner original words must be preserved.
4. Internal observation must be labeled as internal observation.
5. System issue must be labeled as system issue.
6. Roadmap candidate must include priority, dependency, owner, and decision.
7. No real partner feedback may be invented for HOSUN, JOOBOO, Chongqing Huiju, or future partner.

## Priority Rules

P0:

- Only use P0 for problems that must be solved before staging / pilot.
- Examples: staging credentials, token/CORS safety, customer-safe field approval, forbidden-field leakage, unresolved P0 security issue, pilot-blocking quote/order/data issue.

P1:

- Use P1 for partner rehearsal follow-up that should be prioritized after feedback.
- Examples: HOSUN metric dictionary, JOOBOO project field tuning, Manual Outreach status tuning, Campaign field refinement.

P2:

- Use P2 for pilot-period enhancements.
- Examples: due date queue, resource taxonomy refinement, shipment status wording, pilot analytics.

P3:

- Use P3 for long-term platform capabilities.
- Examples: Constant Contact integration, sales CRM / 销售易 integration, carrier integration, accounting integration, partner self-service Portal.

## Security Review Rules

Any feedback involving these topics must pass security review first:

- token
- CORS
- customer-safe fields
- forbidden fields
- backend file paths
- storage keys
- logs
- secret exposure
- unsafe raw database IDs
- private partner notes
- supplier private notes

Security review is required before any customer-facing Portal or staging UAT claim.

## Business Sign-Off Rules

Any feedback involving customer-visible fields must pass business owner sign-off first.

Business sign-off is required for:

- product display fields
- order status wording
- production milestone wording
- shipment status wording
- resource titles and descriptions
- feedback status wording
- customer-safe Market Response preview
- HOSUN customer-safe performance wording
- JOOBOO customer-safe project wording
- future partner customer-visible fields

## Roadmap Routing Rules

- Partner quote with no blocker -> D8.23/D8.24 board, then P1/P2 as appropriate.
- Partner quote with staging dependency -> blocked until staging credentials exist.
- Partner quote with security dependency -> blocked until security review.
- Partner quote with customer-visible field dependency -> blocked until business sign-off.
- Internal observation -> may become documentation/demo polish or system issue, but not partner feedback.
- System issue -> next action queue.
- Roadmap candidate -> pilot readiness matrix.
- External integration request -> P3 unless real workflow and safety review justify earlier work.

## HOSUN Routing Rules

Product scope:

- lifting systems
- desk frames
- desk legs
- lifting columns
- heavy-duty supply

Review dimensions:

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

Each HOSUN item must be classified as:

- customer-safe feedback
- internal-only feedback
- Market Response signal
- product expectation
- quote blocker
- order blocker
- pilot blocker

Routing:

- Customer-safe feedback -> business sign-off and security review before Portal use.
- Internal-only feedback -> PartnerOS internal notes only.
- Market Response signal -> Market Response metrics and human review.
- Product expectation -> product field dictionary or Partner Onboarding.
- Quote blocker -> Quote workflow / approval review.
- Order blocker -> Order Detail / production / shipment review.
- Pilot blocker -> P0 or blocked in pilot gate.

## JOOBOO Routing Rules

Product scope:

- education furniture
- school desks/chairs
- project furniture

Review dimensions:

- school procurement timing
- delivery consistency
- installation
- resource needs
- feedback after use
- project acceptance criteria

Routing:

- Customer-safe project wording -> business sign-off and security review.
- Internal-only project risk -> PartnerOS internal notes only.
- Resource needs -> Resource Center / Portal whitelist review.
- Feedback after use -> Feedback / Market Response mapping.
- Project acceptance criteria -> Quote / Order / Pilot gate review.

## Future Partner Routing Rules

Review dimensions:

- onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields
- Market Response metrics

Routing:

- Onboarding data -> Partner Onboarding.
- Product family -> Product Catalog / Campaign.
- Quote logic -> Quote workflow / approval rules.
- Delivery requirement -> Order / Production / Shipment.
- Resource taxonomy -> Resource Center / Portal whitelist.
- Customer-visible fields -> business sign-off and security review.
- Market Response metrics -> partner-specific metric dictionary.

## Gate Rules

- Do not allow staging UAT without real staging credentials.
- Do not allow pilot with unresolved P0 blockers.
- Do not write STAGING_VALIDATED without real external staging evidence.
- Do not enter D9 while external staging remains WAITING_FOR_REAL_STAGING_EVIDENCE.
- Do not add proof records from feedback review.
- Do not automatically send email, SMS, LinkedIn messages, or customer notifications.
- Do not automatically change quote/order status.

## Decision Output

Each reviewed item must produce:

- priority: P0 / P1 / P2 / P3
- dependency: staging credentials / security review / business sign-off / partner data / none
- decision: do now / defer / needs more feedback / blocked
- owner
- due date
- status

PartnerOS remains READY_FOR_STAGING_HANDOFF until real staging credentials and external staging evidence exist.
