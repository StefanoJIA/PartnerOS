# D8.25 Customer-Safe Copy Rules

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE

These rules define how PartnerOS internal data may be rewritten into customer-safe copy for partner rehearsal, staging UAT, pilot preparation, and service.intelli-opus.com Portal responses. They do not approve real records and do not validate staging.

## Forbidden Content

Customer-safe copy must never expose:

- cost
- margin
- pricing breakdown
- supplier private notes
- internal-only comments
- private partner notes
- backend paths
- backend file paths
- storage keys
- token values
- unsafe raw database IDs
- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- internal Market Response scoring
- internal ranking

## Date And Status Wording

- Planned dates must be labeled as planned.
- Estimated windows must not be written as confirmed dates.
- Production milestones must distinguish planned, in progress, completed, delayed, and pending review states.
- Shipment status must distinguish planned, booked, in transit, delivered, delayed, blocked, and cancelled without implying automatic customer notification.
- Quote and order copy must not imply automatic status changes.

Examples:

| Internal Meaning | Customer-Safe Copy |
| --- | --- |
| Shipment risk exists but is not customer-confirmed | Shipment plan is under operations review; customer-facing schedule remains planned. |
| Production milestone is delayed due to supplier issue | Production milestone needs follow-up; updated customer-safe timing is pending review. |
| Market Response score increased | Product interest is being monitored for follow-up. |
| Customer complaint includes sensitive details | Feedback has been received and is under internal review. |

## Shipment Risk Copy

Shipment risk must be converted into customer-safe wording:

- Do not expose carrier negotiation, route risk analysis, supplier blame, storage keys, or backend file paths.
- Use high-level status and planned timing.
- Mark uncertainty clearly.
- Keep internal escalation notes inside PartnerOS.

Allowed wording pattern:

`Shipment status: planned. Delivery window: planned for [window]. Operations note: schedule is being monitored and will be updated after internal review.`

## Market Response Copy

Market Response shown outside PartnerOS must be a high-level preview only:

- Do not expose internal scoring.
- Do not expose ranking.
- Do not expose watchlist formulas.
- Do not expose internal cost, margin, quote logic, or supplier analysis.
- Explain why the product line deserves attention in customer-safe business language.

Allowed wording pattern:

`Market signal preview: Recent interest and operating feedback suggest this product family should remain in active follow-up.`

## HOSUN Copy Rules

HOSUN content may cover lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply. HOSUN technical metrics may only become customer-visible after business confirmation. The following metrics require exact approval:

- load
- stability
- noise
- test cycle
- certification
- warranty

Customer-safe HOSUN candidate copy may include:

- product family
- load range
- stability summary
- noise claim
- delivery window
- installation summary
- after-sales support
- warranty summary
- test cycle summary
- certification summary
- packaging summary
- project demand category

Internal-only HOSUN content must stay inside PartnerOS:

- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- supplier private notes
- internal Market Response scoring

## JOOBOO Copy Rules

JOOBOO content may cover education furniture, school desks/chairs, and project furniture. Customer-safe JOOBOO copy may include approved wording for:

- school procurement timing
- delivery consistency
- installation notes
- resource needs
- feedback after use
- project acceptance criteria

Internal-only JOOBOO content includes procurement negotiation notes, project margin assumptions, unresolved installation risk, internal feedback triage, and private partner notes.

## Future Partner Copy Rules

Future partner copy must be reviewed partner by partner. Required preparation areas include:

- onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields
- Market Response metrics

Quote logic, delivery requirement details, and Market Response metrics should remain internal-only until business owner sign-off defines customer-safe summaries.

## Approval Rule

No real business owner sign-off means the copy is not approved. No real partner feedback means partner quote fields remain pending. No real staging evidence means the system remains READY_FOR_STAGING_HANDOFF and external staging remains WAITING_FOR_REAL_STAGING_EVIDENCE.

## Operating Boundaries

- Do not enter D9.
- Do not create proof records.
- Do not write STAGING_VALIDATED.
- Do not fabricate business owner sign-off.
- Do not fabricate partner feedback.
- Do not automatically send email, SMS, LinkedIn, customer notification, supplier notification, webhook, or carrier request.
- Do not automatically change quote or order status.
