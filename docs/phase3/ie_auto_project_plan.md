# IE Auto Project Plan

**Source:** `IE Auto.pdf` in the repository root.
**Date:** 2026-05-29.
**Purpose:** turn the project overview into a staged execution plan for intelliOffice / PartnerOS.

## 1. Product Positioning

The PDF positions the system as two coordinated products:

- **intelliOffice / PartnerOS**: the internal operating system and source of truth for agency operations.
- **service.intelli-opus.com**: the customer-facing portal that reads selected customer-visible data from PartnerOS.

PartnerOS is not only a CRM. It is an operating center for product fit, quoting, orders, partner execution, production, shipment, feedback, and market intelligence.

The priority market remains furniture and ergonomic workstation products, especially:

- adjustable desk frames
- desk legs
- lifting columns
- control boxes
- handsets
- heavy-duty load capacity projects
- low-noise and speed-sensitive lifting products
- BIFMA / certification-sensitive requests
- OEM / ODM project-based bulk orders

HOSUN, JOOBOO, and future factories should be modeled as equal peer partners. The system must not hard-code brand privilege.

## 2. System Architecture Boundary

The intended architecture is:

```text
PartnerOS Internal Backend
  -> Customer Portal API Bridge
  -> service.intelli-opus.com Customer Portal
```

PartnerOS owns the internal data lifecycle. The service portal should consume safe, scoped, customer-visible API responses.

The service portal should read from:

- `product_catalog`
- `customer_orders`
- `order_production_milestones`
- `shipment_plans`
- future `shipment_tracking_events`
- quote / document resources
- `feedback_tickets`

## 3. Operating Lifecycle

The full lifecycle described by the PDF is:

```text
Lead
  -> Product Fit
  -> Manual Outreach
  -> Quote
  -> Customer Confirmation
  -> Order
  -> Partner Split
  -> Supplier Confirmation
  -> Production Milestones
  -> Shipment Tracking
  -> Feedback
  -> Market Intelligence
```

This lifecycle should stay traceable end to end. Each stage should produce structured data for the next stage instead of relying on PDF parsing or unstructured notes.

## 4. Current State Mapping

As of the current repository state:

| Area | State |
|---|---|
| D5 Lead Intelligence | Implemented / closed |
| D6 Quote MVP | Implemented / closed |
| D7.2 Order CRUD | Implemented |
| D7.3 Customer Confirmation | Implemented |
| D7.4 Partner Split + Supplier Confirmation | Implemented |
| D7.5 Production Milestones | Implemented |
| D7.6 Shipment Tracking | Implemented |
| D7.7 Customer Portal Bridge API | Implemented |
| D7.8 Service Portal UAT + Feedback Operations | Implemented |
| D7.9 Resource Center | Implemented |
| D8.1 RBAC / Scoped Access | Implemented |
| D8.2 Runtime Hardening | Implemented |
| D8.3 service.intelli-opus.com Staging Integration | Contract runner implemented |
| D8.4 Multi-Partner Operations Dashboard | Implemented |
| D8.5 Market Response Intelligence | Implemented |
| D8 Integration Hardening | Foundation implemented |
| Strict Staging / Cloud Validation | Evidence workflow added |
| D8 Delivery Stage Goal Matrix | Added |
| D8 Readiness Audit | Added |
| D8 Staging Operator Handoff | Added |
| D8 Staging Execution Pack | Added |
| D8 Staging Records Policy | Added |

## 5. Non-Negotiable Safety Rules

The PDF repeats the same safety posture across AI, quote, order, production, shipment, and portal work:

- No automatic email / LinkedIn / Outlook sending.
- No automatic supplier or customer notification.
- No automatic order creation from PDF parsing.
- No automatic production, shipment, payment, inventory reservation, or delivery promise.
- No internal cost, margin, pricing breakdown, supplier private note, internal activity log, backend path, storage key, or token in customer-facing APIs.
- AI can assist classification, product fit, gap detection, drafting, market signal analysis, feedback analysis, and recommendations, but it must not execute irreversible business actions.

## 6. Segment Goals

### Segment 1 - D7.9 Resource Center / Document Center

**Status:** implemented.

**Why:** the PDF and existing portal mapping both identify customer downloadable resources as the next missing customer portal capability after shipment and feedback.

**Goal:** create a customer-safe document catalog and signed download foundation.

**Deliverables:**

- Resource/document model or extension around existing file attachments.
- Customer-visible resource metadata whitelist.
- Signed or expiring download endpoint for allowed resources.
- Operator UI to attach, classify, and publish resources to an order.
- Portal API bridge endpoint that returns only safe metadata and download capability.
- Smoke script covering no backend path / storage key leakage.

**Out of scope:**

- Public bucket browsing.
- Permanent unauthenticated file URLs.
- Automatic document emailing.
- Real customer notification.

**Acceptance:**

- Operator can mark a resource customer-visible.
- service portal can list and download a permitted resource.
- Forbidden path/token/storage fields are absent from all portal responses.

### Segment 2 - D8.1 RBAC and Scoped Access

**Status:** implemented.

**Goal:** move from broad internal authentication toward role and scope aware access.

**Deliverables:**

- Role definitions for internal Operator/Admin/Viewer style users.
- Permission helper and role preset fallback for existing roles.
- Route-level permission matrix for internal feedback, orders, resources, and portal readiness.
- Tests proving restricted users cannot access unsafe internal routes.

**Acceptance:**

- Internal users have explicit capabilities.
- Portal bridge access remains token-scoped and cannot read internal-only fields or operational APIs.

### Segment 3 - D8.2 Runtime Hardening

**Status:** implemented.

**Goal:** make local and staging runtime safer and easier to verify.

**Deliverables:**

- Runtime readiness checks for DB, migrations, backend, frontend proxy target, portal config, and storage.
- Clear staging vs local environment docs.
- Token and secret check scripts.
- Safer startup / doctor output for desktop and development modes.

**Acceptance:**

- A single documented command set can prove a staging-like environment is ready.
- Misconfigured token/CORS/storage states fail loudly before integration testing.

### Segment 4 - D8.3 service.intelli-opus.com Staging Integration

**Status:** contract runner implemented.

**Goal:** connect the existing customer portal to PartnerOS staging APIs without replacing the portal.

**Deliverables:**

- Staging integration checklist executed with the portal team.
- Contract tests against the real service portal consumer.
- CORS, token, HTTPS, and error handling verified.
- Field whitelist inspection in browser/network responses.

**Acceptance:**

- service.intelli-opus.com can display products, orders, production, shipment, resources, and feedback status from PartnerOS staging.
- No internal fields appear in portal-visible payloads.

### Segment 5 - D8.4 Multi-Partner Operations Dashboard

**Status:** implemented.

**Goal:** turn partner execution data into an operating view across HOSUN, JOOBOO, and future partners.

**Deliverables:**

- Partner workload and status dashboard.
- Supplier confirmation coverage.
- Production milestone delay / bottleneck board.
- Shipment readiness by partner.
- Neutral partner ranking signals based on capability, fit, price, lead time, certification, MOQ, and project match.

**Acceptance:**

- Operators can compare partner execution health without hard-coded brand preference.
- Delays and missing confirmations are visible before they become customer issues.

### Segment 6 - D8.5 Market Response Intelligence

**Goal:** close the loop from feedback and market signals back into product fit, quote strategy, partner selection, and outreach.

**Deliverables:**

- Feedback tagging and summary extraction.
- Quote / order win-loss signal capture.
- Market demand signal board for adjustable frame categories.
- Product parameter gap analysis.
- AI-assisted recommendations with human review.

**Acceptance:**

- Feedback and market signals can influence product fit, quote prep, and partner selection.
- AI suggestions remain advisory and auditable.

## 7. Recommended Execution Order

The recommended order is:

```text
D7.9 Resource Center (done)
  -> D8.1 RBAC / scoped access (done)
  -> D8.2 Runtime hardening (done)
  -> D8.3 service portal staging integration (contract runner done)
  -> D8.4 Multi-partner operations dashboard (done)
  -> D8.5 Market response intelligence (done)
  -> D8 Integration hardening (foundation done)
  -> Strict staging/cloud validation (evidence workflow added)
  -> D8 delivery stage goal matrix (added)
  -> D8 readiness audit (added)
  -> D8 staging operator handoff (added)
  -> D8 staging execution pack (added)
  -> D8 staging records policy (added)
```

This keeps the customer portal capability complete before broadening into security hardening, deployment hardening, operations analytics, and intelligence loops.

## 8. Immediate Next Brief

The next implementation brief should be:

```text
Strict staging evidence run
```

Minimum target:

- Run `scripts/d8_strict_staging_evidence_check.py` against the real staging URL.
- Preserve the PASS/FAIL output as staging evidence.
- Fix any failed HTTPS, token, CORS, readiness, or field-filtering gaps.
- Coordinate service portal bridge calls without changing nginx from this repo.

D8 integration hardening now provides a local/staging contract gate across D7.7-D8.5, and strict staging/cloud validation has a repeatable evidence collector. The next product value is running it against real cloud environment values and closing any staging gaps it exposes.

See [D8 Delivery Stage Goal Matrix](d8_delivery_stage_goal_matrix.md) for the current stage-by-stage artifact, verification, and next-gap map.
Use [D8 Readiness Audit](d8_readiness_audit.md) to classify the repo as `READY_FOR_STAGING`, `STAGING_GAPS_OPEN`, or `STAGING_VALIDATED` based on saved evidence.
Use [D8 Staging Operator Handoff](d8_staging_operator_handoff.md) to generate the command sheet for whoever has the real staging backend URL and portal token.
Use [D8 Staging Execution Pack](d8_staging_execution_pack.md) to verify the local handoff chain before sharing it.
Use [D8 Staging Records Policy](d8_staging_records_policy.md) to keep saved staging evidence canonical, redacted, and commit-safe.
