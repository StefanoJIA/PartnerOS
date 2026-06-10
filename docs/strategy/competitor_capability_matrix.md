# Competitor Capability Matrix: PartnerOS Growth Loop

Status: READY_FOR_STAGING_HANDOFF

Evidence boundary: WAITING_FOR_REAL_STAGING_EVIDENCE remains active until real staging token, origin, and UAT evidence exist.

## Purpose

This matrix compares useful capability patterns from Tencent SalesEasy and Constant Contact, then adapts them to PartnerOS as an internal operating system for high-quality export brands. It is not an integration plan for either vendor.

## Adapted Capability Matrix

| Capability Pattern | SalesEasy / CRM Value | Constant Contact / Campaign Value | PartnerOS Adaptation |
| --- | --- | --- | --- |
| Customer records | Accounts, contacts, leads, sales stages | Contact lists and audience metadata | Existing Company, Contact, Lead, lead intelligence, and follow-up queues remain the source of truth. |
| Sales process | Pipeline, opportunities, task follow-up | Campaign goals and conversion milestones | Growth campaign planning maps partner focus, product focus, target segment, goal, status, and next action. |
| Partner management | Channel and partner operations | Not a core focus | PartnerOS links campaign focus to HOSUN, JOOBOO, and future partner onboarding as equal brand directions. |
| Campaign planning | Sales plays and customer journeys | Email campaign planning and segmentation | PartnerOS uses lightweight segments from company/contact/lead data and keeps outreach manual. |
| Outreach | CRM activity logging | Email templates and follow-up sequences | PartnerOS generates Chinese/English drafts and records manual sent/replied/interested/quote requested touchpoints only. |
| Conversion tracking | Opportunity to order | Campaign performance | PartnerOS attributes campaign focus to quote lines and order lines using product/partner keywords. |
| Service loop | Service tickets and account health | Post-campaign engagement | PartnerOS feeds feedback tickets, shipment risk, and market signals back into campaign review. |
| Safety | Permissioned CRM records | Email compliance tools | PartnerOS does not connect external CRM/email APIs, does not auto-send, and does not change quote/order status from campaign screens. |

## PartnerOS Positioning

PartnerOS is not a single CRM, email sender, or HOSUN-only demo. Its growth loop joins customer development, product fit, quote preparation, order delivery, Portal visibility, customer feedback, and market response in one internal workflow.

HOSUN lifting systems and JOOBOO education/project furniture remain reference scenarios, while future partner onboarding proves the same operating loop can support more export brands.

## Explicit Non-Goals

- No Tencent SalesEasy API connection.
- No Constant Contact API connection.
- No automated email, SMS, LinkedIn, webhook, customer notification, or supplier notification.
- No quote status or order status change from the growth operations screen.
- No `STAGING_VALIDATED` claim before real staging credentials and origin are available.
