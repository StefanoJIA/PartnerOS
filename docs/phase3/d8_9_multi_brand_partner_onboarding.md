# D8.9 Multi-Brand Partner Onboarding MVP

Status: READY_FOR_STAGING_HANDOFF

D8.9 adds an internal partner onboarding workflow so PartnerOS can support more premium export brands beyond the HOSUN and JOOBOO demo references.

## Boundary

- PartnerOS remains the internal source of truth.
- `service.intelli-opus.com` remains the customer-facing Portal.
- The project does not enter D9.
- No proof records are created.
- No Go/No-Go gate is added.
- No staging validation is claimed.
- No customer notification, supplier notification, email, webhook, carrier API call, deployment, or order status mutation is performed.

## Workflow

Operators can open `/partner-onboarding` to review each manufacturing partner as a peer partner in the same onboarding ladder:

1. `discovery`
2. `product_mapping`
3. `quote_ready`
4. `portal_ready`
5. `demo_ready`
6. `active_partner`
7. `paused`

The page is read-only for D8.9. It aggregates current partner, product catalog, quote readiness, order split, production milestone, shipment, Portal visibility, and market response evidence from existing PartnerOS data.

## Checklist

Each partner is evaluated against:

- Brand profile completed.
- Product categories mapped.
- Pricing basis available.
- Quote flow ready.
- Order flow ready.
- Production/shipment flow mapped.
- Portal visibility reviewed.
- Market response focus defined.
- Demo narrative prepared.

## Reference Partners

HOSUN and JOOBOO are reference samples, not privileged primary brands. All partner records are peer-level operating records.

HOSUN should demonstrate lifting systems, desk frames, desk legs, lifting columns, and heavy-duty/project supply.

JOOBOO should demonstrate education furniture, school desks/chairs, and project furniture.

Future partners, including Chongqing Huiju or other premium export brands, should enter through the same onboarding checklist. Placeholder content must not be treated as real commercial data.

## API And UI

- API: `GET /api/v1/partner-onboarding`
- Frontend: `/partner-onboarding`
- Data source: existing manufacturing partner, product catalog, product-partner links, order partner splits, production milestones, and shipment plans.
- Commit scope: no schema migration; no staging token handling; no proof record generation.

## Readiness Meaning

`quote_ready` means the partner has enough mapped product and pricing basis for internal quote preparation.

`portal_ready` means the partner has mapped product, order, production, and shipment data suitable for customer-visible review through existing field whitelist boundaries.

`demo_ready` means the partner has enough profile, product focus, market focus, and demo narrative to support a partner-facing walkthrough.

`active_partner` means all onboarding checks are complete and the partner can be used as an active operating reference.

## Safety

The D8.9 onboarding workflow is read-only. It does not:

- Validate staging.
- Enter D9.
- Create proof records.
- Notify customers.
- Notify suppliers.
- Call carriers.
- Store or expose tokens.
- Expose internal cost, margin, pricing breakdowns, supplier private notes, backend paths, or storage paths.
