# D8.8 Demo Rehearsal Checklist

Status: READY_FOR_STAGING_HANDOFF

Audience: HOSUN, JOOBOO, Chongqing Huiju, and future premium export-brand partners.

Purpose: run a realistic 10 to 15 minute rehearsal before a partner-facing walkthrough. This checklist keeps the demo focused on PartnerOS as the internal source of truth for a premium export-brand agency, with `service.intelli-opus.com` remaining the customer-facing Portal.

## Rehearsal Boundary

- Do not claim external staging validation.
- Do not enter D9.
- Do not add proof records.
- Do not use real staging tokens during rehearsal.
- Do not show `.env`, local data folders, backend storage paths, internal cost, margin, pricing breakdowns, supplier private notes, backend file paths, or token values.
- Do not auto-send email, webhooks, supplier notifications, customer notifications, or carrier API calls.

## Pre-Demo Startup

1. Start Docker Postgres if the demo environment is clean.
2. Start the backend on `http://127.0.0.1:8014`.
3. Confirm `/health` returns `status=ok` and the database is ready.
4. Start the frontend with `VITE_API_PROXY_TARGET=http://127.0.0.1:8014`.
5. Open the frontend and confirm the main navigation renders.
6. Run or confirm the D8.5 demo environment check if there is time.

## Login

1. Open the PartnerOS frontend.
2. Log in with the local demo operator account.
3. Confirm Dashboard loads without a fatal error.
4. Open System Health only if the audience asks about runtime readiness.

## 10 To 15 Minute Demo Order

Use `/demo-walkthrough` as the primary navigation surface.

| Time | Step | Page | Message |
| --- | --- | --- | --- |
| 0:00-1:00 | Position PartnerOS | `/demo-walkthrough` | PartnerOS is the internal source of truth for intelliOffice operations. |
| 1:00-3:00 | Show the operating chain | `/demo-walkthrough` | Product interest becomes quote, order, partner split, production, shipment, feedback, and market response. |
| 3:00-5:00 | HOSUN scenario | `/demo-walkthrough` -> Market Response | Lifting-system demand becomes a controlled HOSUN operating loop. |
| 5:00-7:00 | JOOBOO scenario | `/demo-walkthrough` -> Market Response | Education furniture and project furniture use the same multi-brand loop. |
| 7:00-9:00 | Portal Operations | `/portal-integration` | Customer-visible orders, shipment readiness, feedback status, market signal preview, and forbidden-field safety. |
| 9:00-11:00 | Featured Order Detail | order detail from `/demo-walkthrough` | Customer-visible production, shipment, resource, and feedback summary on one order. |
| 11:00-13:00 | Feedback Tickets | `/feedback-tickets` | Feedback enters the internal queue without auto-reply, SLA promise, or customer notification. |
| 13:00-15:00 | Staging next step | demo script close | Real Portal UAT needs backend HTTPS origin, token, allowed origin, and public base URL. |

## HOSUN Lifting Systems Talk Track

Show that PartnerOS can support HOSUN beyond a sales list:

- Product interest: adjustable desk frames, desk legs, lifting columns, and heavy-duty lifting systems.
- Quote: operator prepares the customer proposal; PartnerOS does not auto-send.
- Order: confirmed order becomes the source of truth.
- Partner split: HOSUN receives the relevant operating share.
- Production: milestones show customer-safe progress.
- Shipment: plans show manual logistics status without carrier automation.
- Feedback: customer questions about ETD, lift-system specs, or delivery become internal tickets.
- Market Response: repeated demand, production friction, shipment risk, or feedback creates operator attention signals.

Core sentence:

HOSUN can use PartnerOS to turn lifting-system opportunities into coordinated quote, production, shipment, feedback, and market learning operations.

## JOOBOO Education Furniture Talk Track

Show that PartnerOS is not HOSUN-specific:

- Product interest: education furniture, classroom tables, project furniture, and institutional procurement programs.
- Quote: project requirements stay connected to the proposal.
- Order: confirmed project demand remains traceable.
- Partner split: JOOBOO receives the relevant work package.
- Production: project readiness stays visible to the operator.
- Shipment: delivery timing supports project coordination.
- Feedback: finish quality, classroom durability, documents, and delivery concerns are handled internally.
- Market Response: repeated education furniture questions guide resource and partner focus.

Core sentence:

JOOBOO proves the same operating system works for a different product category and buying context.

## Portal Operations Talking Points

Use Portal Operations to show the bridge between internal truth and customer-safe visibility:

- Recent customer-visible orders.
- Shipment status and logistics risk.
- Feedback tickets and internal status.
- Market signal preview.
- Product, order, production, shipment, resources, and feedback readiness.
- Forbidden-field safety: no internal cost, margin, pricing breakdown, supplier private notes, backend paths, or tokens.

## Market Response Talking Points

Market Response should answer why a product line deserves attention:

- Quote and order demand.
- Production delay or blocking signal.
- Shipment issue or ETD risk.
- Customer feedback pattern.
- Product data gaps.
- Watchlist focus.

Operator message:

Market Response is advisory. Operators still decide what to pursue, update, escalate, or defer.

## Order Detail Talking Points

Open Featured Order Detail from `/demo-walkthrough`.

Show:

- Customer order summary.
- Current customer-visible step.
- Production summary.
- Shipment summary.
- Resource summary.
- Feedback summary.

Core sentence:

Order Detail is where internal operating facts become a customer-safe status story.

## Feedback Tickets Talking Points

Show:

- Feedback ticket list.
- Detail drawer.
- Internal update.
- Resolve and close controls if the rehearsal data supports it.

Boundary:

Feedback tickets do not auto-reply, notify customers, notify suppliers, or promise a resolution time.

## Common Questions And Answers

**Is this just a CRM?**  
No. A CRM records relationship activity. PartnerOS connects customer development to quote, order, partner split, production, shipment, feedback, and market response.

**Is this built only for HOSUN?**  
No. HOSUN lifting systems and JOOBOO education furniture are peer demo scenarios. Chongqing Huiju and future premium export brands can use the same operating loop.

**Is `service.intelli-opus.com` replaced by PartnerOS?**  
No. PartnerOS is the internal source of truth. `service.intelli-opus.com` remains the customer-facing Portal and reads only customer-safe fields.

**Can customers see costs or supplier notes?**  
No. Customer-facing APIs must remain field-whitelisted and must not expose internal cost, margin, pricing breakdowns, supplier private notes, backend paths, or tokens.

**Is staging already validated?**  
No. The project remains READY_FOR_STAGING_HANDOFF until the real backend HTTPS origin, token, allowed origin, and public base URL are configured and verified.

## Finish Within 15 Minutes

- Keep positioning to 1 minute.
- Do not explain every table column.
- Use `/demo-walkthrough` control links instead of manual navigation.
- Pick one HOSUN order detail and one JOOBOO market signal; do not browse every record.
- Keep Portal Operations focused on safe customer visibility.
- Close with the staging credential request instead of broad roadmap discussion.

## Backup Paths

If `/demo-walkthrough` temporarily has no data:

- Open Dashboard for operating context.
- Open Portal Operations directly at `/portal-integration`.
- Open Orders and choose a customer-visible order with production or shipment summary.
- Open Market Response directly at `/market-intelligence`.
- Open Feedback Tickets directly at `/feedback-tickets`.
- Use the D8.7 partner demo script as the verbal fallback.

If an API call returns a friendly empty state:

- Say the UI is handling an empty or unavailable state.
- Switch to the next page in the demo chain.
- Do not debug live unless the page is blocked.

If a page shows a fatal error:

- Stop using that page.
- Continue with the documented business narrative.
- Record the page and symptom as a follow-up after the rehearsal.

