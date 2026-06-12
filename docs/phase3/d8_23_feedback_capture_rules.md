# D8.23 Feedback Capture Rules

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- Purpose: protect feedback quality during real partner rehearsals
- Boundary: no D9 entry, no proof record expansion, no real staging validation claim

## Core Rules

1. Real partner original words must be recorded verbatim or close to the original meaning.
2. Do not write internal guesses as partner feedback.
3. Do not write internal dry-run observations as real customer or partner feedback.
4. Do not merge presenter observations into partner quotes.
5. Do not claim HOSUN, JOOBOO, Chongqing Huiju, or future partner approval unless that partner explicitly said it.
6. Do not record token values, cost, margin, pricing breakdown, supplier private notes, backend file paths, storage keys, internal-only comments, or private partner notes in partner-facing documents.

## Feedback Type Classification

Each feedback item must be classified as one of:

- partner quote
- presenter observation
- system issue
- roadmap candidate

### Partner Quote

Use only when the feedback comes from a real partner attendee.

Required fields:

- Partner.
- Speaker or role.
- Original words.
- Translation if needed.
- Session id.
- Date.
- Product focus.

### Presenter Observation

Use when the presenter or internal team notices an issue during rehearsal.

Required fields:

- Observation.
- Page or module.
- Whether it affected the demo.
- Suggested follow-up.

Presenter observation must not be presented as partner feedback.

### System Issue

Use when a route, page, loading state, wording, or data display blocks or weakens the rehearsal.

Required fields:

- Page or module.
- Error or issue.
- Severity.
- Reproduction notes.
- Suggested owner.

### Roadmap Candidate

Use when feedback suggests a product direction, future feature, or pilot requirement.

Required fields:

- Feature or issue.
- Related module.
- Impacted partner.
- Priority candidate.
- Dependencies.
- Suggested owner.
- Decision: do now / defer / needs feedback / blocked.

## HOSUN Feedback Capture Rules

Product scope:

- lifting systems
- desk frames
- desk legs
- lifting columns
- heavy-duty supply

HOSUN dimensions:

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
- quote/order/pilot blocker

Rules:

- Customer-safe feedback can be used for Portal wording only after business owner and security review.
- Internal-only feedback must not be shown in the customer Portal.
- Market Response signal remains advisory and requires human review.
- Product expectation should be routed to product field or partner onboarding refinement.
- Quote/order/pilot blocker must be reviewed in the pilot readiness matrix.

## JOOBOO Feedback Capture Rules

Product scope:

- education furniture
- school desks/chairs
- project furniture

JOOBOO dimensions:

- school procurement timing
- delivery consistency
- installation
- resource needs
- feedback after use
- project acceptance criteria

Each JOOBOO item must distinguish:

- customer-safe feedback
- internal-only feedback
- Market Response signal
- product expectation
- quote/order/pilot blocker

Rules:

- Customer-safe project timing or delivery wording needs business owner review.
- Internal project risks stay internal unless rewritten into approved Portal language.
- Resource needs should be routed to resource taxonomy.
- Feedback after use should feed Market Response only after classification.

## Future Partner Feedback Capture Rules

Use for Chongqing Huiju and future partners.

Capture:

- onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields
- Market Response metrics

Each item must distinguish:

- customer-safe feedback
- internal-only feedback
- partner-specific product field
- shared platform capability
- pilot blocker

Rules:

- Do not hardcode future partner assumptions into shared core.
- Customer-visible fields require business owner and security review.
- Quote logic that touches margin or approval must remain internal unless explicitly approved.
- Market Response metrics should be partner-specific until real usage proves shared value.

## Forbidden Capture Content

Do not write the following into external-facing rehearsal notes or partner-facing documents:

- token values
- `.env` content
- cost
- margin
- pricing breakdown
- supplier private notes
- private partner notes
- backend file paths
- storage keys
- unsafe raw database IDs
- internal-only comments
- unreviewed security findings

## Routing Rules

- Partner quote -> feedback intake and decision log.
- Presenter observation -> internal dry-run notes or follow-up issue.
- System issue -> next action queue.
- Roadmap candidate -> pilot readiness matrix.
- Staging credential dependency -> staging credential request.
- Security dependency -> security review request.
- Business field dependency -> business UAT request.

PartnerOS remains READY_FOR_STAGING_HANDOFF until real staging credentials and external staging evidence exist.
