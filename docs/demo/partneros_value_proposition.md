# PartnerOS Value Proposition

Status: READY_FOR_STAGING_HANDOFF

PartnerOS is the internal multi-brand operating system for intelliOffice as a premium export-brand agency. It connects the work that is usually scattered across spreadsheets, chat threads, PDFs, supplier messages, shipment notes, and customer follow-up.

## The Traditional Export-Agent Problem

Premium export brands often have strong manufacturing and product capability, but the operating loop between the customer and the factory is fragmented.

Common pain points:

- Customer development lives in one place while product fit lives somewhere else.
- Quotes are prepared manually but are not connected to later order execution.
- Confirmed orders lose context once supplier coordination starts.
- Partner splits and supplier confirmations are hard to track across brands.
- Production updates are maintained manually and inconsistently.
- Logistics plans are not connected to customer-visible status.
- Feedback arrives after delivery but rarely feeds market response.
- Customers ask for status updates, but internal teams need to avoid exposing cost, margin, supplier notes, backend files, or private operating data.

## What PartnerOS Connects

PartnerOS connects the agency operating loop:

- Customer development: identify customer need, segment, and opportunity.
- Product adaptation: map the need to the correct product line and partner.
- Quote: prepare a controlled quote without automatic sending.
- Order: convert customer confirmation into a source-of-truth order.
- Partner split: assign order lines to HOSUN, JOOBOO, Chongqing Huiju, or future partners.
- Supplier coordination: record confirmations without automatic notification.
- Production: maintain milestones and readiness status.
- Shipment: maintain logistics plans without carrier API automation.
- Customer Portal: expose only whitelisted customer-safe status.
- Feedback: collect and triage customer feedback internally.
- Market response: convert demand, friction, logistics risk, and feedback into human-reviewed product and partner priorities.

## Why This Is Not A Single CRM

A CRM mainly tracks contacts, deals, and sales activities. PartnerOS goes beyond that by connecting the operational chain after a quote becomes a real order.

PartnerOS tracks:

- Quote-to-order continuity.
- Multi-partner manufacturing coordination.
- Production milestones.
- Shipment plans.
- Customer-visible Portal status.
- Feedback operations.
- Market response intelligence.

That makes it an agent operating system for multiple export brands, not a single-vendor CRM.

## Why This Matters To Premium Export Brands

For HOSUN, PartnerOS can turn lifting-system demand into a controlled operating loop for desk frames, desk legs, lifting columns, and heavy-duty lifting systems.

For JOOBOO, PartnerOS can support education furniture and project furniture opportunities from customer requirement to delivery feedback.

For Chongqing Huiju and future partners, the same model can support additional product categories without rebuilding the workflow from scratch.

## Source Of Truth Boundary

PartnerOS is the source of truth for internal operations.

`service.intelli-opus.com` is the customer-facing Portal.

The Portal should only read filtered, customer-visible fields from PartnerOS. It must not expose internal cost, margin, pricing breakdown, supplier private notes, backend paths, storage keys, or tokens.

## Current Handoff State

The system is ready for staging handoff, not real staging validation. Real staging still requires the production-side private token and allowed origin setup before external UAT can be claimed.
