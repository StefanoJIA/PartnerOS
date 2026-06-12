# D8.25 UAT Data Selection Plan

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Scope: documentation-only data selection plan for rehearsal, staging UAT, and pilot preparation.

This document defines how the business owner selects staging-safe sample data before any partner rehearsal, service Portal staging UAT, or pilot. It does not approve any real staging record, does not enter D9, does not create proof records, and does not write STAGING_VALIDATED.

## Why Business Owner Selection Is Required

PartnerOS is the internal source of truth for intelliOffice operations. service.intelli-opus.com is the customer-facing Portal and must only read customer-safe fields. Before any data is shown externally, the business owner must decide which records can be used and which fields must remain internal-only.

staging, rehearsal, and pilot data selection is required because unreviewed operational records can contain sensitive information:

- unreviewed real customers may include confidential names, projects, addresses, or commercial context.
- Real orders may include negotiated terms, delivery risk, supplier issues, or customer-specific commitments.
- Real prices may expose cost, margin, pricing breakdown, discount logic, or quote strategy.
- Real supplier notes may expose supplier private notes, internal-only comments, delivery risk analysis, or partner negotiation details.

Unreviewed real customers, real orders, real prices, and real supplier notes must not be copied directly into staging, rehearsal, pilot, screenshots, partner demos, or customer-facing Portal responses.

## Data Coverage Required For UAT

A representative UAT set should cover the full PartnerOS operating loop:

| Data Area | Required Coverage | Customer-Safe | Internal-Only | Demo-Only | Requires Approval |
| --- | --- | --- | --- | --- | --- |
| products | Product family, customer-facing name, approved specs, resources | Approved descriptions and approved public specs | Raw test notes, supplier costs, private partner notes | Synthetic product names and simplified specs | Any real product claim, certification, warranty, or performance number |
| customers | Segment, region, product interest, partner fit | Sanitized segment and high-level profile | Real contact details, account notes, negotiation context | Mock buyer personas | Any real customer name, project, or contact reference |
| quotes | Quote status, product focus, customer-visible summary | Quote reference, public product summary, planned next step | Cost, margin, pricing breakdown, approval rationale | Demo quote with synthetic values | Any real quote amount, term, or customer-specific commitment |
| orders | Order status, customer-safe order summary, partner split summary | Order reference, high-level status, customer-visible delivery summary | Internal IDs, private supplier notes, profitability, escalation notes | Demo order chain | Any real order, project name, PO, PI, contract, or shipment reference |
| production milestones | Planned and actual milestone status | Planned or completed milestone labels and dates marked clearly | Delay root cause, supplier accountability, internal risk notes | Synthetic milestone progression | Any real delay reason or production performance claim |
| shipment status | Shipment plan, status, customer-safe risk wording | Planned window, status label, customer-safe risk summary | Carrier negotiation, internal risk analysis, storage keys, private route notes | Synthetic shipment plan | Any real tracking reference, carrier detail, or risk statement |
| resources | Product sheets, installation guide, public warranty summary | Approved resource title, category, public-safe download manifest | Backend paths, storage keys, draft files, private technical notes | Mock resource manifest | Any real file or resource link |
| feedback | Ticket status, high-level topic, customer-safe next action | Sanitized feedback theme and status | Complaint details, customer identity, cost exposure, internal comments | Demo feedback examples | Any real feedback quote, complaint, or after-sales issue |
| Market Response preview | High-level product or partner signal | Customer-safe market signal preview and operating recommendation | Internal scoring, ranking, private analysis, watchlist rationale | Synthetic signal examples | Any real market observation attributed to a partner or customer |

## Selection Workflow

1. Business owner chooses candidate records by partner, product family, customer segment, and intended use.
2. Operator classifies every field as customer-safe, internal-only, demo-only, or requires approval.
3. Security reviewer checks forbidden fields, token leakage, unsafe raw IDs, backend paths, and storage keys.
4. Business owner signs the approved customer-visible field set.
5. Only signed records move from pending to approved for staging UAT or pilot.
6. Records without sign-off remain pending and must not be presented as approved.

## Intended Use Levels

| Use Level | Allowed Sources | Approval Requirement | Notes |
| --- | --- | --- | --- |
| demo | demo seed, synthetic sample | Presenter review | Must not claim real partner feedback or real customer outcome |
| rehearsal | demo seed, synthetic sample, sanitized real record | Business owner review before external rehearsal | Must keep partner feedback pending until real session happens |
| staging UAT | sanitized real record or approved seed | Business owner sign-off and security review | Requires real staging credentials before validation |
| pilot | approved real or sanitized records | Business owner sign-off, security review, partner/pilot approval | Must not be treated as production deployment approval |

## HOSUN Data Preparation

HOSUN coverage should support lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply without exposing internal risk or supplier details.

Customer-safe candidate fields:

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

Internal-only fields:

- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- supplier private notes
- internal Market Response scoring

HOSUN technical claims such as load, stability, noise, test cycle, certification, and warranty must remain pending until the business owner approves the exact customer-visible wording.

## JOOBOO Data Preparation

JOOBOO coverage should support education furniture, school desks/chairs, and project furniture as a peer partner track, not as a secondary HOSUN example.

Customer-safe candidate fields:

- school procurement timing
- delivery consistency
- installation notes approved for customer display
- resource needs
- feedback after use
- project acceptance criteria

Internal-only fields:

- procurement negotiation notes
- project margin assumptions
- unresolved installation risk
- internal feedback triage
- private partner notes

## Future Partner Data Preparation

Future partner onboarding should use the same PartnerOS operating loop while preserving partner-specific data needs:

- onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields
- Market Response metrics

Each future partner must receive an explicit field review before any record is moved from pending to approved.

## Boundaries

- READY_FOR_STAGING_HANDOFF remains the current status.
- WAITING_FOR_REAL_STAGING_EVIDENCE remains the external staging state.
- Do not enter D9.
- Do not create proof records.
- Do not write STAGING_VALIDATED.
- Do not fabricate real business owner sign-off.
- Do not fabricate real partner feedback.
- Do not automatically send email, SMS, LinkedIn, customer notification, supplier notification, webhook, or carrier request.
- Do not automatically change quote or order status.
