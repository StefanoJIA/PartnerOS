# D8.6 Live Walkthrough QA

Status: READY_FOR_STAGING_HANDOFF

D8.6 focused on live browser acceptance for the partner-facing demo. It did not enter D9, did not add proof records, did not add a Go/No-Go gate, did not validate real staging, and did not deploy or modify `service.intelli-opus.com`.

## Runtime

- Backend started on `http://127.0.0.1:8014`.
- Frontend started on `http://127.0.0.1:5173`.
- Demo data was seeded with `python scripts/d8_3_business_demo_seed.py`.
- Browser login used the seeded operator account.

## Pages Checked

| Page | Result | Notes |
| --- | --- | --- |
| `/` | Pass | Dashboard rendered with daily operations and demo walkthrough entry. |
| `/demo-walkthrough` | Pass | Full story, one-click control panel, HOSUN and JOOBOO scenarios rendered. |
| Portal Operations | Pass | Customer Portal value, recent orders, shipment status, feedback status, and market signal sections rendered. |
| Market Response | Pass | Market signal explanation and operator attention reasons rendered. |
| Orders | Pass | Order list rendered and available for order detail navigation. |
| Featured Order Detail | Pass | Opened from `/demo-walkthrough`; customer-visible production, shipment, resource, and feedback summary rendered. |
| Feedback Tickets | Pass | List, detail drawer, update, resolve, and close controls worked in browser. |
| Quotes | Pass | Quote list rendered. |
| System Health | Pass | Health and Portal readiness view rendered. |

## Interaction Checks

- `/demo-walkthrough` control panel to Portal Operations: pass.
- `/demo-walkthrough` control panel to Market Response: pass.
- `/demo-walkthrough` control panel to Featured Order Detail: pass.
- `/demo-walkthrough` control panel to Feedback Tickets: pass.
- Feedback ticket detail drawer: pass.
- Feedback internal update: pass.
- Feedback mark resolved: pass.
- Feedback close: pass.

## Console And Error State

No fatal browser console errors were observed during the checked pages and interactions. No white screen, route failure, visible fatal API error, or empty-data crash was observed.

## Deferred Items

No blocking demo issues were found. Non-blocking build warnings remain the existing Vite dynamic import and chunk-size warnings; they do not block the live walkthrough.

## Acceptance

D8.6 is suitable for a live partner-facing walkthrough under the current `READY_FOR_STAGING_HANDOFF` boundary. Real `service.intelli-opus.com` staging validation still requires the real staging token/origin and remains outside this demo acceptance.

