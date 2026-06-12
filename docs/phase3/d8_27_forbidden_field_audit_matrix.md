# D8.27 Forbidden Field Audit Matrix

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Audit status: pending

No real security sign-off recorded yet. This matrix prepares a future security reviewer audit of customer-safe fields and forbidden fields for service Portal bridge responses. It does not approve real staging or production exposure.

## Global Forbidden Fields

The following fields are forbidden across all Portal-facing responses, docs, screenshots, demo seeds, staging UAT seeds, and pilot handoff material:

- cost
- margin
- pricing breakdown
- supplier private notes
- internal-only comments
- private partner notes
- backend paths
- storage keys
- token values
- unsafe raw database IDs
- internal audit events
- internal owner notes
- unreviewed risk notes
- internal Market Response scoring/ranking

## Audit Matrix

| Area | Allowed Customer-Safe Fields | Forbidden Fields |
| --- | --- | --- |
| products | approved product family, customer-facing product name, approved public specs, approved customer-safe resource titles | cost, margin, supplier private notes, raw test notes, private partner notes, backend paths, storage keys, unsafe raw database IDs |
| orders | customer-safe order reference, status label, partner name if approved, customer-visible delivery summary, planned next action | cost, margin, pricing breakdown, supplier private notes, internal owner notes, internal audit events, unsafe raw database IDs, private partner notes |
| order detail | customer-safe order summary, approved product family, approved production summary, approved shipment summary, customer-safe feedback status | pricing breakdown, margin, supplier private notes, internal-only comments, backend paths, storage keys, internal audit events, unreviewed risk notes |
| production milestones | planned milestone label, completed milestone label, planned date marked planned, completed date if approved, customer-safe status | raw test notes, supplier accountability, internal owner notes, internal audit events, private partner notes, unreviewed risk notes |
| shipment status | planned delivery window, shipment status label, customer-safe risk wording, customer-safe next action | carrier negotiation notes, backend paths, storage keys, delivery risk analysis, supplier blame, internal owner notes, unreviewed risk notes |
| resources | approved resource title, category, customer-safe manifest entry, approved download label | backend paths, storage keys, draft file paths, token values, internal-only comments, unsafe raw database IDs |
| feedback status | sanitized topic, ticket status, customer-safe next action, high-level feedback category | complaint details, internal-only comments, private partner notes, internal owner notes, warranty cost exposure, unsafe raw database IDs |
| Market Response preview | high-level product or partner signal, customer-safe operating recommendation, approved product focus | internal Market Response scoring/ranking, watchlist formula, margin logic, supplier analysis, private partner notes, unreviewed risk notes |

## HOSUN Field Boundary

HOSUN lifting systems internal-only fields:

- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- supplier private notes
- internal Market Response scoring

HOSUN customer-safe candidate fields only after business confirmation:

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

## Security Reviewer Questions

- Are customer-safe fields generated from an explicit whitelist?
- Are forbidden fields excluded from API responses?
- Are forbidden fields excluded from docs and screenshots?
- Are unsafe raw database IDs replaced with customer-safe references?
- Are token values absent from docs, logs, and frontend bundles?
- Are internal audit events and internal owner notes blocked?
- Is internal Market Response scoring/ranking blocked?
- Are HOSUN technical claims business-confirmed before customer-visible use?

## Boundary

- No real security sign-off recorded yet.
- Pending audit does not mean approved.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not fabricate real security approval.
