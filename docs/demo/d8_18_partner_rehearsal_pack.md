# D8.18 Partner Rehearsal Pack

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- Audience: HOSUN, JOOBOO, Chongqing Huiju, and future premium export-brand partners
- Purpose: prepare a 10-15 minute partner-facing rehearsal based on the D8.17 verified local business flow
- Scope: demo script, partner narratives, rehearsal checklist, feedback collection, and safety boundaries
- Boundary: no D9 entry, no proof record expansion, no real external staging claim

D8.18 is a rehearsal package. It does not add a new product module, does not deploy anything, does not connect real sales or marketing APIs, and does not claim real external staging validation.

## Core Positioning

PartnerOS is the internal source of truth for intelliOffice operations.

`service.intelli-opus.com` remains the customer-facing Portal. It should read only customer-safe fields from PartnerOS bridge APIs after the real backend HTTPS origin, Portal token, allowed origin, and public base URL are provided.

PartnerOS is not a single CRM and not a HOSUN-only tool. It is a multi-partner agent operating system for premium export brands. The same operating loop can support HOSUN lifting systems, JOOBOO education furniture, Chongqing Huiju, and future partner brands.

## 10-15 Minute Demo Route

Use this route for the partner-facing rehearsal:

1. Workbench
   - Start at `/`.
   - Explain that this is the daily operating entrance for business development, delivery operations, and management review.
   - Show entry cards for customer development, Growth Operations, quotes, orders, feedback, Market Response, Partner Onboarding, and Demo Walkthrough.

2. Customer Development
   - Open Companies, Contacts, and Lead Intelligence.
   - Explain how a lead is evaluated by customer type, industry, region, product interest, and partner fit.
   - Key message: before quoting, the team can understand which partner and product direction fits the customer.

3. Growth Operations / Campaign
   - Open `/growth-operations`.
   - Show HOSUN and JOOBOO as peer partner directions.
   - Explain Campaign as a manual operating workspace for segment, product focus, next action, and attribution.
   - Key message: PartnerOS plans and records outreach work, but does not send messages automatically.

4. Manual Outreach
   - Open or create a manual outreach task under a campaign.
   - Show Chinese and English drafts, follow-up task, and manual status updates such as manual sent, interested, and quote requested.
   - Key message: the business team stays in control of when and how customers are contacted.

5. Quote
   - Open `/quotes`.
   - Explain that product interest becomes a quote opportunity.
   - Key message: quote work is connected back to customer development and campaign context, but status changes remain operator-controlled.

6. Order
   - Open `/orders`, then one Order Detail page.
   - Show customer order summary, partner split, supplier confirmation, production, shipment, and feedback summary.
   - Key message: confirmed orders become operational records, not isolated sales records.

7. Production
   - In Order Detail, show production milestones.
   - Explain that operators can maintain real progress without automatically notifying customers or suppliers.

8. Shipment
   - In Order Detail, show shipment plans and shipment risk summary.
   - Explain that logistics status is maintained by operators and can later be exposed to the customer Portal through safe fields.

9. Customer Portal
   - Open Portal Operations.
   - Explain that the Portal is the customer-facing window, while PartnerOS remains the internal source of truth.
   - Show recent customer-visible orders, shipment status, feedback, market signal preview, and forbidden-field safety.

10. Feedback
    - Open Feedback Tickets.
    - Show list/detail, status, priority, owner, resolution, and close controls.
    - Key message: feedback is an internal operating loop; the system does not auto-reply or promise SLA.

11. Market Response
    - Open Market Response.
    - Explain why product lines need attention based on order demand, logistics risk, production delays, feedback, and watchlist signals.
    - Key message: Market Response helps decide where to focus next, but recommendations require human review.

12. Partner Onboarding
    - Open Partner Onboarding.
    - Show HOSUN, JOOBOO, and future partner readiness.
    - Key message: any premium export brand can enter the same operating loop through onboarding, product setup, campaigns, quote, order, delivery, feedback, and market response.

## HOSUN Scenario Talk Track

Use HOSUN to show how PartnerOS supports technical product lines and project-style demand.

Suggested line:

HOSUN represents lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply. A customer may start with an adjustable workstation requirement, but the real operating question is whether the partner can support load, stability, noise control, production timing, shipment planning, and post-delivery feedback. PartnerOS keeps those facts connected from customer interest through campaign, quote, order, production, shipment, feedback, and Market Response.

Business points to emphasize:

- Product interest can be captured around lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply.
- Project-style demand can be tracked from early outreach to quote request.
- Order execution can show partner split, supplier confirmation, production progress, shipment plan, and customer-visible status.
- Feedback about load, stability, noise, packaging, delivery, or installation can become Market Response input.
- HOSUN is one partner direction, not the only system identity.

## JOOBOO Scenario Talk Track

Use JOOBOO to show that the same operating model works for a different partner and product family.

Suggested line:

JOOBOO represents education furniture, school desks and chairs, and project furniture for schools or institutions. The customer journey is different from HOSUN, but the operating loop is the same: identify a segment, prepare outreach, qualify product fit, create quote, manage confirmed order, track production and delivery, handle customer feedback, and turn repeated signals into Market Response.

Business points to emphasize:

- Education furniture and project furniture require project timing, consistency, delivery coordination, and feedback handling.
- School desks/chairs and institutional furniture opportunities can be handled through Campaign and Manual Outreach.
- Order and delivery tracking help the business team answer project progress questions.
- Feedback from schools or institutions can guide product focus and partner readiness.
- JOOBOO appears as a peer partner direction next to HOSUN.

## Future Partner Talk Track

Use this when speaking to Chongqing Huiju or any future premium export-brand partner.

Suggested line:

PartnerOS is not built for one brand. A new partner can enter through Partner Onboarding, product catalog setup, campaign planning, manual outreach, quote, order, partner split, supplier confirmation, production, shipment, customer Portal visibility, feedback, and Market Response. The value is that intelliOffice can operate multiple premium export brands through one consistent system while keeping each brand's product focus, customer segment, and delivery loop distinct.

Business points to emphasize:

- Future partners can be onboarded without changing the core operating model.
- Product setup, customer segments, campaign focus, quote flow, order execution, and feedback can stay partner-specific.
- The system supports multi-brand agency work instead of a single-brand CRM workflow.
- Partner-facing demo feedback should focus on what data each brand needs to operate confidently.

## Demo Feedback Questions

Use `docs/demo/d8_18_partner_feedback_form.md` during or after the rehearsal.

Collect feedback on:

- Whether the PartnerOS positioning is clear.
- Whether the demo route is easy to follow.
- Whether Campaign / Growth Operations is useful.
- Whether the customer Portal direction is valuable.
- Whether order, production, shipment, and feedback tracking match real operating needs.
- Whether Market Response helps the partner decide what to push next.
- What each partner wants to see before staging or pilot.

## Pre-Demo Checklist

1. Runtime
   - Backend is available on `http://127.0.0.1:8014`.
   - Frontend is available on `http://127.0.0.1:5173`.
   - Frontend proxy uses `VITE_API_PROXY_TARGET=http://127.0.0.1:8014`.
   - UI login works with the local demo account.

2. Pages
   - `/`
   - `/demo-walkthrough`
   - `/growth-operations`
   - `/quotes`
   - `/orders`
   - one Order Detail page
   - `/portal-operations`
   - `/feedback-tickets`
   - `/market-response`
   - `/partner-onboarding`

3. Demo Data
   - HOSUN campaign exists or can be created.
   - JOOBOO campaign exists or can be created.
   - At least one manual outreach task can be shown.
   - At least one quote, order, feedback ticket, and Market Response signal can be opened.

4. Talking Boundaries
   - PartnerOS is internal source of truth.
   - `service.intelli-opus.com` is customer-facing Portal.
   - Customer-facing APIs must use field whitelists.
   - Real staging still requires private configuration.

## Safety Boundaries

During the rehearsal, explicitly state:

- PartnerOS does not automatically send email, SMS, LinkedIn messages, or customer notifications.
- PartnerOS does not automatically notify suppliers.
- PartnerOS does not automatically change quote or order status.
- PartnerOS does not call carrier APIs.
- PartnerOS does not connect real Constant Contact or sales CRM APIs in this local demo.
- PartnerOS does not expose internal cost, margin, pricing breakdown, supplier private notes, backend paths, storage keys, or tokens through customer-facing APIs.
- Token values and `.env` files must not be committed.
- Local rehearsal does not equal real external staging validation.

## Staging Boundary

The project remains READY_FOR_STAGING_HANDOFF until the real service Portal integration values are provided and verified:

- Backend HTTPS origin reachable by `service.intelli-opus.com`.
- `PORTAL_CUSTOMER_API_ENABLED=true`.
- `PORTAL_CUSTOMER_API_TOKEN` with a real private server-to-server value.
- `PORTAL_CUSTOMER_ALLOWED_ORIGINS` including the real Portal origin.
- `PUBLIC_BASE_URL` for customer-safe links and manifests.

Before those values exist and are verified, the correct external status is handoff-ready, not validated on real staging.

## Rehearsal Decision

D8.18 is ready when the team can deliver the route above in 10-15 minutes, collect partner feedback with the feedback form, and clearly explain the safety and staging boundaries without claiming real external staging validation.
