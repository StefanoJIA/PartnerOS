# Activity Actions

**Status:** current on 2026-05-30.

## Purpose

`activity_logs.action` stores canonical event names used by timelines, audits, and operator-facing history panels. Action names should remain stable because tests, smoke scripts, and user workflows use them as typed timeline signals.

This document is a naming contract. It is not permission to send notifications, call external systems, or mutate business state.

## Core Rules

- Use lowercase snake_case action names.
- Prefer past-tense business events such as `order_created` or `shipment_plan_updated`.
- Store identifiers and changed fields in `diff` only when they are redacted and useful for audits.
- Do not store tokens, passwords, raw response bodies, backend file paths, storage keys, private customer files, internal cost, margin, pricing breakdowns, or supplier private notes.
- Do not use activity logging as a side effect to trigger email, webhooks, carrier APIs, customer notifications, supplier notifications, order status changes, shipment status changes, payment actions, inventory reservations, or partner-selection changes.

## Order And Timeline Actions

| Action | Object type | Meaning |
|---|---|---|
| `order_created` | order | Manual order record created |
| `order_created_from_rfq` | order | Order created from an RFQ path |
| `order_created_from_sample` | order | Order created from a sample path |
| `customer_confirmation_added` | order | Customer confirmation recorded manually |
| `customer_confirmation_voided` | order | Customer confirmation voided manually |
| `partner_split_created` | order | Partner split created or ensured |
| `partner_split_updated` | order | Partner split updated |
| `supplier_confirmation_added` | order | Supplier confirmation recorded manually |
| `supplier_confirmation_voided` | order | Supplier confirmation voided manually |
| `production_milestones_generated` | order | Production milestone rows generated from template |
| `production_milestone_updated` | order | Production milestone row changed |
| `production_milestone_status_changed` | order | Production milestone status changed |
| `shipment_plan_created` | order | Manual shipment plan created |
| `shipment_plan_updated` | order | Shipment plan fields updated without a status change |
| `shipment_status_changed` | order | Shipment plan status changed manually |
| `order_resource_created` | order | Order resource metadata created |
| `order_resource_updated` | order | Order resource metadata, publication state, or customer visibility changed |

D7.6 shipment actions are manual logistics events. They must not call carriers, create webhooks, send email, notify suppliers/customers, or automatically set the order to shipped or delivered.

## Quote, RFQ, And Sample Actions

| Action | Object type | Meaning |
|---|---|---|
| `quote_created` | quote | Quote record created |
| `quote_marked_sent` | quote | Manual external quote send was recorded |
| `quote_pdf_exported` | quote | Customer PDF export generated |
| `rfq_created` | rfq | RFQ created |
| `rfq_updated` | rfq | RFQ updated |
| `rfq_status_changed` | rfq | RFQ status changed |
| `rfq_item_added` | rfq | RFQ item added |
| `rfq_item_updated` | rfq | RFQ item updated |
| `rfq_item_removed` | rfq | RFQ item removed |
| `rfq_converted_to_sample` | rfq | RFQ manually converted to sample |
| `rfq_converted_to_order` | rfq | RFQ manually converted to order |
| `quotation_added` | rfq | Partner quotation added |
| `quotation_updated` | rfq | Partner quotation updated |
| `quotation_deleted` | rfq | Partner quotation deleted |
| `sample_created` | sample | Sample created |
| `sample_created_from_rfq` | sample | Sample created from RFQ |
| `sample_status_changed` | sample | Sample status changed |
| `sample_shipping_updated` | sample | Sample shipping fields updated |
| `sample_feedback_recorded` | sample | Sample feedback recorded manually |
| `sample_converted_to_order` | sample | Sample manually converted to order |

Quote delivery events are manual records only. Exporting or marking sent must not send the quote.

## CRM And Lead Actions

| Action | Object type | Meaning |
|---|---|---|
| `company_created` | company | Company created |
| `company_updated` | company | Company updated |
| `contact_created` | contact | Contact created |
| `contact_added_from_company` | company | Contact created from company context |
| `contact_updated` | contact | Contact updated |
| `lead_created` | lead | Lead created |
| `lead_created_from_company` | lead | Lead created from company context |
| `lead_created_from_contact` | lead | Lead created from contact context |
| `lead_updated` | lead | Lead updated |
| `lead_stage_changed` | lead | Lead stage changed |
| `interaction_created` | related object | Human-reviewed interaction recorded |
| `task_created` | task or related object | Task created |
| `task_completed` | task | Task completed |
| `contact_research_company_updated` | company | Contact research updated company fields |
| `contact_research_contact_created` | contact | Contact research created contact |
| `contact_research_contact_updated` | contact | Contact research updated contact |

Outreach actions remain human-reviewed. Activity logs must not trigger automatic LinkedIn, email, campaign, or customer messaging.

## Partner And Product Actions

| Action | Object type | Meaning |
|---|---|---|
| `partner_created` | manufacturing_partner | Manufacturing partner created |
| `partner_updated` | manufacturing_partner | Manufacturing partner updated |
| `product_created` | product | Product created |
| `product_updated` | product | Product updated |
| `partner_linked` | product | Partner linked to product |
| `partner_link_updated` | product | Product-side partner link changed |
| `partner_unlinked` | product | Product-side partner link removed |
| `product_linked` | manufacturing_partner | Product linked to partner |
| `product_link_updated` | manufacturing_partner | Partner-side product link changed |
| `product_unlinked` | manufacturing_partner | Partner-side product link removed |

Partner actions must stay partner-neutral and must not hard-code HOSUN, JOOBOO, or any other manufacturer as a privileged default.

## Validation

```powershell
cd backend
python scripts/activity_actions_doc_check.py
python scripts/project_execution_chain_check.py
```

## Related Code

- `backend/app/services/activity.py`
- `backend/app/models/common.py`
- `backend/app/services/orders/order_timeline.py`
- `backend/app/services/orders/shipment_plan_service.py`
