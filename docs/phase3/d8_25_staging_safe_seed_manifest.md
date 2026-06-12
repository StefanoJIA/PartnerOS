# D8.25 Staging-Safe Seed Manifest

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE

No real staging record approved yet. This manifest is a template for selecting staging-safe seed data after business owner review. Pending rows are not approved for real staging UAT, pilot, or customer-facing Portal display.

## Manifest Template

| Record ID | Display Name | Partner | Product Family | Customer Segment | Intended Use | Customer-Visible Fields | Internal-Only Fields | Approval Owner | Approval Status | Risk Notes | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pending-hosun-001 | HOSUN lifting systems sample | HOSUN | lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply | Distributor or project buyer | demo / rehearsal / staging UAT / pilot | product family; load range; stability summary; noise claim; delivery window; installation summary; after-sales support; warranty summary; test cycle summary; certification summary; packaging summary; project demand category | raw test notes; complaint details; delivery risk analysis; warranty cost exposure; supplier private notes; internal Market Response scoring | pending business owner | pending | Technical claims require exact business confirmation before customer-visible use | demo seed / sanitized real record / synthetic sample / pending |
| pending-jooboo-001 | JOOBOO education furniture sample | JOOBOO | education furniture / school desks/chairs / project furniture | School, institution, or project buyer | demo / rehearsal / staging UAT / pilot | school procurement timing; delivery consistency; approved installation notes; resource needs; feedback after use; project acceptance criteria | procurement negotiation notes; project margin assumptions; unresolved installation risk; internal feedback triage; private partner notes | pending business owner | pending | Project acceptance wording must be reviewed before staging UAT | demo seed / sanitized real record / synthetic sample / pending |
| pending-huiju-001 | Chongqing Huiju partner sample | Chongqing Huiju | pending product family | pending customer segment | demo / rehearsal / staging UAT / pilot | pending customer-visible fields | pending internal-only fields | pending business owner | pending | Requires partner-specific field model before approval | demo seed / sanitized real record / synthetic sample / pending |
| pending-future-001 | Future partner onboarding sample | future partner | onboarding data / product family | pending customer segment | demo / rehearsal / staging UAT / pilot | customer-visible fields; resource taxonomy; Market Response metrics preview | quote logic; delivery requirement details; internal partner notes; private scoring | pending business owner | pending | Must not be treated as a real partner record | demo seed / sanitized real record / synthetic sample / pending |

## Field Definitions

- Record ID: stable manifest identifier, not a raw unsafe database ID.
- Display Name: business-readable title for review.
- Partner: HOSUN, JOOBOO, Chongqing Huiju, or future partner.
- Product Family: product family or product line used in demo, rehearsal, staging UAT, or pilot.
- Customer Segment: sanitized buyer segment, region, industry, or partner fit.
- Intended Use: demo, rehearsal, staging UAT, or pilot.
- Customer-Visible Fields: fields proposed for service Portal or partner-facing walkthrough.
- Internal-Only Fields: fields that must stay inside PartnerOS.
- Approval Owner: business owner responsible for field approval.
- Approval Status: pending, approved, rejected, or needs revision.
- Risk Notes: safety, confidentiality, or wording risks.
- Source: demo seed, sanitized real record, synthetic sample, or pending.

## Approval Rules

- A pending row is not approved.
- No row may be marked approved without business owner sign-off.
- No row may be used for real staging UAT without security review when it includes customer-visible fields.
- No row may contain token values, backend paths, storage keys, cost, margin, pricing breakdown, supplier private notes, or private partner notes in customer-visible fields.
- Sanitized real record means the source was reviewed and sensitive fields were removed; it does not mean approval is automatic.
- Synthetic sample means the record is not real partner feedback, not a real customer commitment, and not real staging evidence.

## HOSUN Staging-Safe Preparation

HOSUN candidate seed rows should cover lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply. Customer-facing fields may include product family, load range, stability summary, noise claim, delivery window, installation summary, after-sales support, warranty summary, test cycle summary, certification summary, packaging summary, and project demand category only after business confirmation.

Internal-only HOSUN fields include raw test notes, complaint details, delivery risk analysis, warranty cost exposure, supplier private notes, and internal Market Response scoring.

## JOOBOO Staging-Safe Preparation

JOOBOO candidate seed rows should cover education furniture, school desks/chairs, and project furniture. Customer-facing fields may include school procurement timing, delivery consistency, approved installation notes, resource needs, feedback after use, and project acceptance criteria.

JOOBOO must remain a peer partner path with HOSUN. The manifest must not present HOSUN as the only primary brand.

## Future Partner Staging-Safe Preparation

Future partner seed rows should capture onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, and Market Response metrics. Partner-specific quote logic and delivery requirements are internal-only until explicitly approved for customer-safe summary.

## Boundary Statement

This manifest does not validate real staging and does not approve real records. It keeps PartnerOS in READY_FOR_STAGING_HANDOFF and external staging in WAITING_FOR_REAL_STAGING_EVIDENCE until real credentials, real business owner approval, and real staging smoke evidence exist.
