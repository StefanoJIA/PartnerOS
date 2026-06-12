# D8.25 Business Owner Data Sign-Off Template

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE

No real business owner sign-off recorded yet. This template is for future approval of customer-visible data used in partner rehearsal, staging UAT, or pilot. It must not be treated as an approval record until completed by the responsible business owner.

## Sign-Off Summary

| Field | Value |
| --- | --- |
| Sign-off owner | pending |
| Date | pending |
| Conditions | pending |
| Pilot partner | pending |
| Pilot product family | pending |
| Pilot customer segment | pending |
| Intended use | demo / rehearsal / staging UAT / pilot |
| Approval status | pending |

## Approved Customer-Visible Fields

List the exact fields and wording approved for service Portal or partner-facing walkthrough:

| Field Group | Approved Field | Approved Display Wording | Conditions | Status |
| --- | --- | --- | --- | --- |
| products | pending | pending | pending | pending |
| orders | pending | pending | pending | pending |
| production milestones | pending | pending | pending | pending |
| shipment status | pending | pending | pending | pending |
| resources | pending | pending | pending | pending |
| feedback status | pending | pending | pending | pending |
| Market Response preview | pending | pending | pending | pending |

## Forbidden Fields

The following fields remain forbidden for customer-facing Portal, partner-facing screenshots, staging-safe seeds, and public demo copy unless a separate security and business approval process explicitly changes the rule:

- cost
- margin
- pricing breakdown
- supplier private notes
- internal-only comments
- private partner notes
- backend file paths
- storage keys
- token values
- unsafe raw database IDs
- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- internal Market Response scoring

## Approved Products

| Partner | Product Family | Approved Customer-Safe Description | Approval Status | Conditions |
| --- | --- | --- | --- | --- |
| HOSUN | lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply | pending | pending | load, stability, noise, test cycle, certification, and warranty wording require approval |
| JOOBOO | education furniture / school desks/chairs / project furniture | pending | pending | school procurement timing, delivery consistency, installation notes, and project acceptance criteria require approval |
| Chongqing Huiju | pending | pending | pending | partner-specific fields required |
| future partner | onboarding data / product family | pending | pending | quote logic, delivery requirement, resource taxonomy, and Market Response metrics require review |

## Approved Customers

| Customer Segment | Customer Display Name | Allowed Use | Approval Status | Conditions |
| --- | --- | --- | --- | --- |
| pending | pending | demo / rehearsal / staging UAT / pilot | pending | No real customer may be shown before review |

## Approved Orders

| Order Display Name | Partner | Product Family | Customer-Safe Status | Approval Status | Conditions |
| --- | --- | --- | --- | --- | --- |
| pending | pending | pending | pending | pending | No real order, PO, PI, contract, delivery issue, or status commitment may be shown before review |

## Approved Feedback Records

| Feedback Display Name | Partner | Topic | Customer-Safe Summary | Approval Status | Conditions |
| --- | --- | --- | --- | --- | --- |
| pending | pending | pending | pending | pending | No real customer quote or complaint detail may be shown before review |

## Approved Market Response Preview

| Partner | Product Focus | Approved High-Level Signal | Forbidden Internal Detail | Approval Status |
| --- | --- | --- | --- | --- |
| HOSUN | lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply | pending | internal scoring, ranking, delivery risk analysis, warranty cost exposure | pending |
| JOOBOO | education furniture / school desks/chairs / project furniture | pending | internal prioritization, pricing assumptions, private partner notes | pending |
| future partner | onboarding data / product family | pending | internal quote logic, delivery requirement details, private metrics | pending |

## Approved Resources

| Resource Title | Partner | Resource Type | Customer-Safe Manifest Entry | Approval Status | Conditions |
| --- | --- | --- | --- | --- | --- |
| pending | pending | product sheet / installation guide / warranty summary / case material | pending | pending | Backend paths and storage keys must never be exposed |

## Required Sign-Off Questions

- Are approved customer-visible fields explicitly listed?
- Are forbidden fields still excluded?
- Are approved products explicitly identified?
- Are approved customers explicitly identified or intentionally left pending?
- Are approved orders explicitly identified or intentionally left pending?
- Are approved feedback records explicitly identified or intentionally left pending?
- Is approved Market Response preview wording high-level and customer-safe?
- Are approved resources free of backend paths and storage keys?
- Is the pilot partner named?
- Is the pilot product family named?
- Is the pilot customer segment named?
- Are sign-off owner, date, and conditions completed?

## Boundary Statement

Until this template is completed with real business owner approval, all records remain pending. Pending does not mean approved. This template does not write STAGING_VALIDATED, does not validate real staging, does not enter D9, and does not create proof records.
