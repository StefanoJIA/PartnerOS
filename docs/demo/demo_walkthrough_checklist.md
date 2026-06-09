# Demo Walkthrough Checklist

Current state: READY_FOR_STAGING_HANDOFF. This checklist is for repeated local or handoff demos. It does not prove real `service.intelli-opus.com` staging validation and does not enter D9.

## Before The Demo

1. Start Docker Postgres.
2. Start backend on `http://127.0.0.1:8014`.
3. Start frontend with `VITE_API_PROXY_TARGET=http://127.0.0.1:8014`.
4. Run the idempotent demo seed:

```powershell
cd backend
python scripts/d8_3_business_demo_seed.py
```

5. Run the D8.5 demo environment check:

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
$env:FRONTEND_BASE_URL="http://127.0.0.1:5173"
python scripts/d8_5_demo_environment_check.py
```

## Pages To Open

Use `/demo-walkthrough` as the starting point. The one-click control panel should provide stable jumps to:

- Dashboard.
- Portal Operations.
- Market Response.
- Orders.
- Featured Order Detail.
- Feedback Tickets.
- Quotes.
- System Health.

## Talk Track

1. Customer development: show how the project starts from customer and brand context.
2. Product adaptation: explain why the product line fits the opportunity.
3. Quote: show that quote work remains operator-controlled.
4. Order: show the confirmed order as the source of truth.
5. Partner split: show HOSUN and JOOBOO as peer partner directions.
6. Production: show operator-maintained milestones.
7. Shipment: show manual logistics planning with no carrier automation.
8. Customer Portal: show customer-safe products, orders, production, shipment, resources, and feedback.
9. Feedback: show internal handling and linked order context.
10. Market Response: explain why repeated demand, shipment risk, production friction, and feedback deserve operator review.

## Required Stable Demo Data

- HOSUN lifting systems scenario: desk frames, desk legs, lifting columns, heavy-duty lifting systems.
- JOOBOO education furniture scenario: education furniture and project furniture.
- At least one featured customer-visible order.
- Production milestones for the featured order.
- Shipment plans for the featured order.
- Feedback tickets linked to the demo order.
- Market signals for HOSUN and JOOBOO focus areas.

## Safety Boundaries

- Do not claim real staging validation.
- Do not deploy or modify `service.intelli-opus.com`.
- Do not send email, webhooks, LinkedIn messages, customer notifications, or supplier notifications.
- Do not call carrier APIs.
- Do not expose internal cost, margin, pricing breakdown, supplier private notes, backend paths, storage keys, or tokens.
- Do not commit `.env`, token files, PDFs, `local_data/`, or `backend/storage/`.

