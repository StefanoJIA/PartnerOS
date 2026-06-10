# D8.12 Release Candidate Test Report

Status: READY_FOR_STAGING_HANDOFF
Date: 2026-06-10

## Scope

D8.12 validates the local PartnerOS release candidate for Chinese business-team demo and internal trial use. This report covers local backend, frontend, smoke scripts, browser walkthrough, Chinese UI readiness, and customer-visible field safety.

This is not real staging validation. PartnerOS must remain READY_FOR_STAGING_HANDOFF until the real `service.intelli-opus.com` staging integration has the required HTTPS backend origin, `PORTAL_CUSTOMER_API_TOKEN`, allowed origin, and `PUBLIC_BASE_URL`.

## Validation Matrix

Backend checks completed:

- `python -m pytest -q`
- `python scripts/dev_runtime_doctor.py`
- `python scripts/smoke_all_d5.py`
- `python scripts/d7_8_portal_live_integration_check.py`
- `python scripts/d8_5_demo_environment_check.py`
- `python scripts/d8_7_partner_demo_handoff_check.py`
- `python scripts/d8_8_demo_rehearsal_check.py`
- `python scripts/d8_9_partner_onboarding_check.py`
- `python scripts/d8_10_navigation_localization_check.py`
- `python scripts/d8_11_chinese_operating_language_check.py`
- `python scripts/d8_12_release_candidate_check.py`

Frontend checks completed:

- `npm run test -- --run`
- `npm run build`

Observed warnings:

- `dev_runtime_doctor.py` still reports optional local Redis and worker services as disabled.
- `PUBLIC_BASE_URL` is still intentionally unset until real staging handoff values are provided.
- Vite still reports the existing chunk-size and mixed dynamic/static import warnings; production build completes.

## Browser Walkthrough

Local browser walkthrough covered:

- `/`
- `/demo-walkthrough`
- `/portal-operations` redirecting to the Portal Operations view
- `/market-response` redirecting to the Market Response view
- `/orders`
- one Order Detail page
- `/feedback-tickets`
- `/quotes`
- `/quote-catalog`
- `/pricing-preview`
- `/products`
- `/companies`
- `/contacts`
- `/lead-intelligence`
- `/lead-intake`
- `/leads`
- `/partner-onboarding`
- `/system-health`
- demo and support entry points

Result: pages opened without white screen or fatal browser console errors. The demo business loop remains visible: customer development, product fit, quote, order, partner split, production, shipment, Portal, feedback, and market response.

## Fixes Applied During RC Audit

- Added `scripts/d8_12_release_candidate_check.py` to verify navigation, core routes, Chinese label mappings, D8 handoff boundaries, and portal forbidden-field safety.
- Fixed the D8.12 portal operations safety-shape assertion to match the current API response.
- Localized visible quote, quote catalog, pricing preview, product, company, contact, lead, and lead intelligence copy that still exposed large English defaults.
- Added Chinese display mapping for the `converted_to_order` quote status.
- Localized lead completeness statuses, filters, missing fields, recommended research actions, contact research drawer text, empty states, and toast messages.
- Updated affected frontend specs for the Chinese quote and pricing preview copy.

## Release Candidate Boundary

PartnerOS remains the internal source of truth. `service.intelli-opus.com` remains the customer-facing portal. Customer-visible bridge APIs must continue to use field whitelists and must not expose internal cost, margin, pricing breakdowns, supplier private notes, backend paths, or tokens.

No D9 gate, proof record expansion, staging evidence refresh, Go/No-Go wording, real staging token handling, production deployment, or server modification was performed in D8.12.

## Deferred Items

- Real staging credential handoff is still pending: backend HTTPS origin, `PORTAL_CUSTOMER_API_TOKEN`, allowed origin, and `PUBLIC_BASE_URL`.
- Optional local Redis and worker runtime services remain outside the demo-critical path.
- Existing Vite build warnings can be addressed later if they become operationally relevant.

## Conclusion

D8.12 is ready as a local release candidate for demo and staging credential handoff. It is not marked as real staging validated.
