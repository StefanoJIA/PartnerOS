# D8.22 Pilot Readiness Matrix

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE
- Source input: partner rehearsal feedback intake
- Boundary: no D9 entry, no proof record expansion, no real staging validation claim

This matrix converts HOSUN, JOOBOO, Chongqing Huiju, and future partner rehearsal feedback into executable priorities.

## Priority Definitions

- P0: staging / pilot 前必须解决.
- P1: partner rehearsal 后优先解决.
- P2: pilot 期间增强.
- P3: 长期平台化能力.

## Decision Values

Use one of these decisions for each row:

- do now
- defer
- needs feedback
- blocked

## Pilot Readiness Matrix

| Priority | Feature or Issue | Related Module | Impacted Partner | Business Value | Risk | Needs Real Staging Credentials | Needs Security Review | Needs Business Owner Sign-Off | Suggested Owner | Suggested Stage | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | Real service Portal staging credentials | Portal bridge / staging handoff | HOSUN, JOOBOO, Chongqing Huiju, future partner | Enables real customer-facing UAT against `service.intelli-opus.com`. | Without credentials, staging cannot be validated. | yes | yes | yes | infrastructure / backend operator | D8.23 | blocked |
| P0 | Customer-safe field approval | Portal Operations / Portal bridge | all partners | Prevents exposure of internal cost, margin, supplier private notes, private partner notes, backend paths, storage keys, token values, and unsafe raw database IDs. | Field leakage could block pilot. | yes for final validation | yes | yes | business owner + security reviewer | D8.23 | do now |
| P0 | Token, CORS, and origin review | Portal bridge / security | all partners | Proves server-to-server Portal access boundary. | Wrong origin or token handling could expose data. | yes | yes | no | security reviewer + backend operator | D8.23 | blocked |
| P0 | RBAC role matrix before pilot users | RBAC / admin / operations | all partners | Separates sales, operator, manager, security reviewer, and admin responsibilities. | Pilot users may see or change data outside role. | no | yes | yes | product + backend operator | D8.23 | needs feedback |
| P0 | Audit log event taxonomy | audit log / order / quote / feedback / campaign | all partners | Makes quote, order, production, shipment, feedback, and campaign changes accountable. | Cannot investigate pilot issues without operator trace. | no | yes | yes | backend operator | D8.23 | needs feedback |
| P0 | Real data import template and review workflow | customer / product / quote / order import | all partners | Moves from demo records to real partner/customer records. | Bad import can pollute pilot data. | no for template, yes for staging rehearsal | yes | yes | operations owner | D8.23 | do now |
| P1 | Campaign field adjustments from rehearsal | Growth Operations / Campaign | HOSUN, JOOBOO, future partner | Makes campaigns match real segment, product focus, and next action needs. | Wrong segmentation reduces business usefulness. | no | no | yes | business owner | D8.x | needs feedback |
| P1 | Manual Outreach status and draft tuning | Manual Outreach | all partners | Improves sales follow-up while keeping manual-send boundary. | Over-automation expectation could create safety risk. | no | no | yes | sales operations | D8.x | needs feedback |
| P1 | Quote approval / margin review design | Quote | all partners | Adds management control before quotes are released. | Approval gaps may cause bad commercial decisions. | no | yes if margin fields exist | yes | business owner + finance | Pilot | defer |
| P1 | Order Detail customer-visible summary tuning | Orders / Portal | all partners | Helps customers understand current order state. | Ambiguous wording could create customer disputes. | yes for Portal validation | yes | yes | operations owner | D8.23 / Pilot | needs feedback |
| P1 | Feedback to Market Response signal mapping | Feedback / Market Response | all partners | Turns repeated feedback into product and partner priorities. | Unstructured feedback may not produce decisions. | no | no | yes | market response owner | D8.x | do now |
| P1 | HOSUN lifting systems metric dictionary | Market Response / product fields | HOSUN | Tracks load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, and project demand. | Wrong metrics could misread HOSUN product-market fit. | no | yes for customer-visible subset | yes | HOSUN business owner | D8.x | needs feedback |
| P1 | JOOBOO project furniture metric dictionary | Market Response / product fields | JOOBOO | Tracks school procurement timing, delivery consistency, installation, resource needs, feedback after use, and project acceptance criteria. | Wrong project metrics could miss education furniture risks. | no | yes for customer-visible subset | yes | JOOBOO business owner | D8.x | needs feedback |
| P2 | Task due date and internal handoff queue | Task / Workbench | all partners | Improves daily follow-up during pilot. | Missed follow-up if still manual-only. | no | no | yes | operations owner | Pilot | defer |
| P2 | Shipment status refinement before carrier integration | Shipment / Portal | all partners | Improves delivery visibility without real carrier API. | Status ambiguity may create customer confusion. | yes for Portal validation | yes | yes | logistics owner | Pilot | needs feedback |
| P2 | Partner resource taxonomy | Resources / Portal | HOSUN, JOOBOO, future partner | Makes specs, docs, and customer-safe resources easier to expose. | Resource leakage or stale docs. | yes for Portal validation | yes | yes | product operations | Pilot | needs feedback |
| P2 | Analytics dashboard for conversion and delivery | Workbench / analytics | all partners | Gives management view of campaign, quote, order, feedback, and delivery performance. | Premature metrics may mislead without real data. | no | no | yes | management owner | Pilot | defer |
| P3 | Constant Contact integration | external integrations / campaign | all partners | Reduces duplicate campaign work after manual process is validated. | Real external send risk and token exposure. | yes | yes | yes | integration owner | Later | defer |
| P3 | Sales CRM / 销售易 integration | external integrations / customer development | all partners | Syncs lead/account/opportunity data after workflow stabilizes. | Data ownership and sync conflicts. | yes | yes | yes | integration owner | Later | defer |
| P3 | Carrier integration | shipment tracking | all partners | Automates shipment status after manual model is stable. | Carrier status may incorrectly change customer expectations. | yes | yes | yes | logistics + integration owner | Later | defer |
| P3 | Partner self-service Portal | partner collaboration / RBAC | future partner | Lets partners update selected data directly. | Requires mature RBAC, audit, field contract, and partner access boundary. | yes | yes | yes | platform owner | Later | defer |

## HOSUN Readiness Matrix

Use this table after HOSUN rehearsal feedback.

| Dimension | Customer-Safe Feedback | Internal-Only Feedback | Market Response Signal | Product Expectation | Quote / Order / Pilot Blocker | Priority | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| load |  |  |  |  |  | P1 | needs feedback |
| stability |  |  |  |  |  | P1 | needs feedback |
| noise |  |  |  |  |  | P1 | needs feedback |
| delivery |  |  |  |  |  | P0/P1 | needs feedback |
| installation |  |  |  |  |  | P1 | needs feedback |
| after-sales |  |  |  |  |  | P1 | needs feedback |
| packaging |  |  |  |  |  | P1 | needs feedback |
| warranty |  |  |  |  |  | P1 | needs feedback |
| test cycle |  |  |  |  |  | P1 | needs feedback |
| certification |  |  |  |  |  | P0/P1 | needs feedback |
| project demand |  |  |  |  |  | P1 | needs feedback |

Product scope:

- lifting systems
- desk frames
- desk legs
- lifting columns
- heavy-duty supply

## JOOBOO Readiness Matrix

Use this table after JOOBOO rehearsal feedback.

| Dimension | Customer-Safe Feedback | Internal-Only Feedback | Market Response Signal | Product Expectation | Quote / Order / Pilot Blocker | Priority | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| school procurement timing |  |  |  |  |  | P1 | needs feedback |
| delivery consistency |  |  |  |  |  | P1 | needs feedback |
| installation |  |  |  |  |  | P1 | needs feedback |
| resource needs |  |  |  |  |  | P1/P2 | needs feedback |
| feedback after use |  |  |  |  |  | P1 | needs feedback |
| project acceptance criteria |  |  |  |  |  | P1 | needs feedback |

Product scope:

- education furniture
- school desks/chairs
- project furniture

## Future Partner Readiness Matrix

Use this table for Chongqing Huiju and future partners.

| Dimension | Related Module | Business Value | Risk | Needs Real Staging Credentials | Needs Security Review | Needs Business Owner Sign-Off | Suggested Owner | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| onboarding data | Partner Onboarding | Defines partner readiness. | Missing data blocks pilot setup. | no | no | yes | partner operations | needs feedback |
| product family | Products / Campaign | Defines product focus and campaign segmentation. | Wrong product grouping weakens Market Response. | no | yes if customer-visible | yes | product operations | needs feedback |
| quote logic | Quote | Keeps commercial workflow partner-specific. | Wrong quote rules create margin/commercial risk. | no | yes if margin review included | yes | finance + sales | needs feedback |
| delivery requirement | Orders / shipment | Keeps fulfillment expectations partner-specific. | Delivery mismatch blocks pilot. | yes for Portal display | yes | yes | operations | needs feedback |
| resource taxonomy | Resources / Portal | Controls customer-safe docs and files. | Resource leakage or confusion. | yes for Portal validation | yes | yes | product operations | needs feedback |
| customer-visible fields | Portal bridge | Prevents internal data exposure. | Field leakage blocks staging. | yes | yes | yes | security + business owner | blocked |
| Market Response metrics | Market Response | Defines partner-specific decision signals. | Generic metrics may hide real risks. | no | yes if customer-visible | yes | market response owner | needs feedback |

## Pilot Entry Decision

Pilot can be considered only when:

1. P0 rows are either complete or explicitly accepted by security and business owner.
2. Real staging credentials are provided through secure channels.
3. Customer-safe field contract is approved.
4. Security review is complete.
5. Business UAT records are selected.
6. No automatic external send is enabled.
7. No quote/order automatic status change is enabled.
8. Partner feedback has been converted into owner-assigned decisions.

Until then, the correct state remains READY_FOR_STAGING_HANDOFF.
