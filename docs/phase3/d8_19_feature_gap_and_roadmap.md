# D8.19 Feature Gap Analysis and Product Roadmap

## Status

- Current state: READY_FOR_STAGING_HANDOFF
- Scope: product gap analysis and post-rehearsal roadmap
- Execution boundary: documentation only
- Product boundary: PartnerOS remains the internal source of truth; `service.intelli-opus.com` remains the customer-facing Portal

This document does not add product modules, database changes, external integrations, deployment steps, proof records, or a real external staging claim. It also does not automatically change order status, send customer notifications, or connect external systems. It is intended to help decide what should happen after D8 partner rehearsal and before pilot-scale operation.

## Product Goal

PartnerOS is intelliOffice's internal operating system for serving multiple premium export-brand partners. It is not a HOSUN-only tool and not a single CRM. The target operating loop is:

Customer Development -> Campaign / Growth Operations -> Manual Outreach -> Quote -> Order -> Partner Split -> Supplier Confirmation -> Production -> Shipment -> Customer Portal -> Feedback -> Market Response -> Partner Onboarding.

The customer-facing Portal at `service.intelli-opus.com` should read only customer-safe fields. It must not expose internal cost, margin, pricing breakdown, supplier private notes, backend paths, storage keys, or tokens.

## Current Completed Capability Summary

### Workbench / Daily Operating Map

The workbench is now the daily entry point. It groups business development, delivery operations, and management decision paths, and links to Growth Operations, customer development, quotes, orders, feedback, Market Response, Partner Onboarding, and Demo Walkthrough.

### Customer Development

Companies, contacts, and lead intelligence can be used to understand customer context, product interest, and partner fit before a quote is created.

### Growth Operations / Campaign

Campaign Workspace MVP supports campaign creation, update, reload, partner focus, product focus, target segment, goal, owner, next action, and read-only attribution to quote, order, feedback, shipment risk, and market signal.

### Manual Outreach

Manual outreach tasks support draft generation, follow-up task creation, and status updates. The system is explicit that no email, SMS, LinkedIn message, or customer notification is sent automatically.

### Quote

Quote pages provide a visible commercial step between customer interest and order conversion. Quote work is connected conceptually to campaign and order flow while preserving manual operator control.

### Order Detail

Order Detail exposes customer order summary, partner split, supplier confirmation, production summary, shipment summary, customer-visible status, feedback summary, and Portal-safe context.

### Production / Shipment

Production milestones and shipment plans exist as manually maintained internal records. They support customer-visible summary fields without automatically changing order status or calling carrier APIs.

### Feedback Tickets

Feedback Tickets support list/detail handling, status and priority updates, internal owner, response summary, resolved/closed handling, and no automatic customer reply or SLA promise.

### Market Response

Market Response explains why products or partner directions need attention based on customer demand, order conversion, production friction, shipment risk, feedback, and watchlist/product gaps.

### Partner Onboarding

Partner Onboarding provides a peer-level framework for HOSUN, JOOBOO, Chongqing Huiju, and future partners. It supports readiness, missing items, next action, and multi-brand operating context.

### Demo / Rehearsal Pack

D8.18 provides a 10-15 minute partner-facing rehearsal pack, final demo script, HOSUN/JOOBOO/future partner talk tracks, partner feedback form, pre-demo checklist, and safety/staging boundary.

### READY_FOR_STAGING_HANDOFF Boundary

The system is ready for handoff preparation, but real service Portal staging still needs the actual backend HTTPS origin, Portal customer API token, allowed origin, and public base URL. Local rehearsal does not equal real external staging validation.

## Priority Definitions

- P0: must be resolved before real staging / pilot can be treated as operationally credible.
- P1: should be prioritized after partner rehearsal feedback.
- P2: useful during pilot to improve efficiency and visibility.
- P3: longer-term platform capability after real operating patterns are known.

## Feature Gap Roadmap

| Priority | Feature Gap | Business Value | Current Gap | Needs Partner Feedback | Needs Staging Credentials | Can Start With Docs / Prototype | Suggested Stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | Real service Portal staging validation | Proves customer-safe Portal can read real PartnerOS data from `service.intelli-opus.com`. | Local bridge and checks exist, but real HTTPS origin/token/origin/public URL are not verified. | No, but partner UAT feedback is useful after setup. | Yes. | Yes: credential request and smoke checklist already useful. | D8.x |
| P0 | Customer-safe field whitelist hardening for Portal | Prevents leakage of cost, margin, pricing breakdown, supplier private notes, paths, storage keys, and tokens. | Existing safety checks cover known surfaces; broader real payload audit is still needed against staging data. | Partly: partners can confirm what customers should see. | Yes for final validation. | Yes: maintain API contract and forbidden-field matrix. | D8.x |
| P0 | RBAC / role permissions | Separates sales, operator, manager, partner-facing reviewer, and admin access before pilot use. | Basic internal access exists, but role-specific workflow permissions are not mature enough for real multi-user operation. | Yes: roles differ by partner and team. | Not required for prototype, required for pilot hardening. | Yes: role matrix and route/action permission design. | D8.x |
| P0 | Audit log / operation audit | Creates accountability for quote, order, production, shipment, feedback, and campaign changes. | Some timeline/domain events exist, but there is no unified operator audit view across the whole loop. | Partly: management can define required accountability. | No for design, yes for production-grade retention review. | Yes: audit event taxonomy and UI sketch. | D8.x |
| P0 | Real data import plan for customers, contacts, products, quotes, and orders | Makes PartnerOS useful with real partner/customer data instead of demo data. | Demo and seeded data prove flows, but bulk import mapping, dedupe, validation, and rollback are incomplete. | Yes: source files and field definitions come from partners. | No for local mapping, yes if staging import is tested. | Yes: import templates and data dictionary. | D8.x |
| P0 | Backup, monitoring, and security hardening | Required before pilot data is trusted. | Local readiness is green, but production-grade backup, monitoring, secrets handling, HTTPS, and incident response are not completed in this repo. | No. | Yes for staging/prod validation. | Yes: runbook and checklist. | D8.x |
| P1 | Partner product data and resource center management | Gives partners a maintainable way to expose product documents, specs, and resources to operators and customer Portal. | Resource center exists, but partner-owned product data workflows and review lifecycle need refinement. | Yes: each partner has different product spec and file needs. | Partly for Portal validation. | Yes: resource taxonomy prototype. | Pilot |
| P1 | Customer Portal deepening | Makes customer Portal more valuable beyond basic order visibility. | Current bridge covers key surfaces, but customer-side UX for order snapshots, resources, feedback, and shipment context needs real Portal integration work. | Yes: customers and partners should decide visibility. | Yes. | Yes: customer-safe page wireframes. | Pilot |
| P1 | Task / due date / internal reminder / handoff | Helps operators follow up without relying on memory or chat. | Manual outreach tasks exist, but cross-module due dates, reminders, owner handoff, and overdue queues are limited. | Yes: operating rhythm differs by team. | No. | Yes: task lifecycle and notification-free design. | D8.x |
| P1 | Quote approval / margin review | Adds management control before quotes are released. | Quote flow exists, but approval gates, margin review, and quote exception handling are not complete. | Yes: approval rules depend on partner and product line. | No. | Yes: approval matrix and mock workflow. | Pilot |
| P1 | Payment / PO / PI / contract workflow | Connects commercial documents to order execution. | Orders and quotes exist, but payment milestones, PO, PI, contract references, and document status are not first-class. | Yes: partners use different document processes. | No for prototype; yes for secure document handling. | Yes: document status model and checklist. | Pilot |
| P1 | Supplier / partner collaboration | Improves partner split, supplier confirmation, production updates, and issue escalation. | Internal records exist, but there is no mature partner/supplier collaboration workspace or permission boundary. | Yes. | Possibly for external access. | Yes: collaboration boundaries and manual workflow. | Pilot |
| P1 | Feedback to Market Response metrics | Turns repeated feedback into measurable product and partner signals. | Feedback can be reviewed, but signal scoring, trend metrics, and closed-loop dashboards are early-stage. | Yes: partners must define what signals matter. | No. | Yes: metric definitions and sample dashboard. | D8.x |
| P1 | HOSUN lifting systems market response metrics | Lets HOSUN evaluate load, stability, noise, delivery, installation, and after-sales patterns. | HOSUN scenario terms exist, but structured product-performance fields and signal scoring are not complete. | Yes. | No. | Yes: HOSUN metric dictionary. | D8.x |
| P1 | JOOBOO project furniture metrics | Helps JOOBOO evaluate project timing, school procurement, delivery consistency, and feedback after use. | JOOBOO scenario terms exist, but project-specific milestones and feedback categories are not complete. | Yes. | No. | Yes: JOOBOO metric dictionary. | D8.x |
| P2 | Shipment tracking / carrier integration roadmap | Reduces manual logistics updates once volume grows. | Shipment plans are manually maintained; no carrier API, webhook, or automatic status transition exists by design. | Yes: carrier needs differ by lane/partner. | Yes before any real integration. | Yes: carrier-agnostic status model. | Later |
| P2 | Analytics dashboard | Gives management conversion, delivery, feedback, and partner performance visibility. | Workbench and Market Response provide operating views, but management analytics are not yet deep. | Yes: leadership should define KPIs. | No. | Yes: KPI catalog and dashboard mock. | Pilot |
| P2 | Future partner onboarding data model | Lets new partners join with their own product fields, quote logic, delivery requirements, and market metrics. | Partner Onboarding exists, but partner-specific schema extension strategy is not finalized. | Yes. | No. | Yes: partner capability profile design. | Pilot |
| P2 | Batch import governance | Makes data onboarding repeatable and auditable. | Real import path, validation rules, duplicate detection, operator review, and rollback are not complete. | Yes: depends on source quality. | Partly for staging rehearsal. | Yes: CSV templates and validation report format. | Pilot |
| P2 | Internal reminder without external notification | Improves follow-up consistency while respecting no-auto-send safety. | Manual tasks exist, but reminder surfaces are basic. | Yes: teams should define cadence. | No. | Yes: reminder UX and due-date rules. | D8.x |
| P3 | External integrations roadmap: Constant Contact, sales CRM, email, carrier, accounting | Reduces duplicate data entry after core workflow is validated. | No real external integrations are connected, by design. | Yes. | Yes for any real integration. | Yes: integration architecture and safety gates. | Later |
| P3 | Accounting and finance workflow | Connects orders to invoice, payment, reconciliation, and management reporting. | Quote/order flow exists, but accounting is outside current D8 scope. | Yes: finance process varies. | Yes for production integration. | Yes: finance data boundary doc. | Later |
| P3 | Partner self-service Portal | Could let partners update product data, production, or shipment progress directly. | PartnerOS is currently internal operator controlled. External partner access requires RBAC, audit, and data boundary maturity. | Yes. | Yes. | Yes: access model and risk review. | Later |
| P3 | Advanced forecasting and recommendation engine | Helps predict demand, risk, and partner opportunities. | Market Response is explainable and advisory, not predictive automation. | Yes: need real outcome data. | No for prototype, yes for production telemetry. | Yes: KPI and model-readiness notes. | Later |

## P0: Before Real Staging / Pilot

The P0 group should be treated as the minimum credible pre-pilot backlog:

1. Real service Portal staging validation.
2. Portal forbidden-field whitelist hardening against real payloads.
3. RBAC / role permissions for internal users.
4. Unified audit log / operation audit.
5. Real data import plan and templates.
6. Backup, monitoring, and security hardening.

These items are not optional if real customers, partner data, or external Portal users are involved.

## P1: After Partner Rehearsal Feedback

The P1 group should be prioritized after HOSUN, JOOBOO, Chongqing Huiju, or future partner feedback:

1. Partner product data and resource lifecycle.
2. Customer Portal deepening.
3. Task, due date, internal reminder, and handoff.
4. Quote approval and margin review.
5. Payment / PO / PI / contract workflow.
6. Supplier / partner collaboration boundaries.
7. Feedback-to-Market-Response metrics.
8. HOSUN and JOOBOO product-specific signal dictionaries.

These should be shaped by real operating feedback rather than assumed from demo data.

## P2: Pilot Enhancements

P2 items improve operating scale during pilot:

1. Shipment tracking and future carrier integration roadmap.
2. Analytics dashboard.
3. Future partner onboarding data model.
4. Batch import governance.
5. Internal reminder and due-date surfaces.

These features become more valuable once real campaign, quote, order, feedback, and delivery data accumulates.

## P3: Long-Term Platform Capabilities

P3 items should wait until the core workflow has real usage patterns:

1. Constant Contact, sales CRM, email, carrier, and accounting integrations.
2. Partner self-service Portal.
3. Accounting/finance workflow.
4. Advanced forecasting or recommendation engine.

The reason to defer them is risk control. External integrations and predictive automation should follow validated operating processes, not precede them.

## HOSUN Lifting Systems Gap Analysis

HOSUN requires richer structured fields and signal metrics than a generic furniture workflow because lifting systems depend on technical performance and project delivery quality.

### Product Fields Needed

- Product family: lifting systems, desk frames, desk legs, lifting columns, heavy-duty lifting.
- Load capacity range.
- Stability requirement.
- Noise level target.
- Stroke / height range.
- Motor / controller configuration.
- Duty cycle or usage intensity.
- Surface treatment / finish.
- Packaging method.
- Installation requirement.
- Certification or compliance requirement.
- MOQ and project lead time.
- Spare parts / after-sales requirement.

### Market Response Metrics Needed

- Load-related feedback frequency.
- Stability-related feedback frequency.
- Noise-related feedback frequency.
- Delivery delay frequency.
- Installation issue frequency.
- After-sales issue frequency.
- Quote-to-order conversion by product family.
- Repeat demand by customer segment.
- Heavy-duty supply opportunity score.
- Shipment damage or packaging issue rate.

### Project-Style Capabilities Needed

- Project requirement intake for technical specs.
- Quote approval when load/stability/noise requirements create margin or risk exceptions.
- Sample / prototype tracking.
- Production milestone templates by lifting system type.
- Shipment risk tags for heavy or oversized components.
- Feedback categorization by performance, installation, delivery, and after-sales.

### Dependency

These fields and metrics should be drafted now as a D8.x prototype, then refined with HOSUN's real product team feedback before pilot. They do not require real staging credentials to design, but real staging is required before customer-facing Portal validation.

## JOOBOO Project Furniture Gap Analysis

JOOBOO requires project-oriented data because education furniture often depends on institutional procurement, delivery windows, classroom consistency, and feedback after use.

### Fields and Metrics Needed

- Product family: education furniture, school desks/chairs, project furniture.
- School / institution type.
- Classroom or campus quantity.
- Procurement timeline.
- Delivery window.
- Installation or assembly requirement.
- Color/material consistency.
- Project acceptance criteria.
- Feedback after use.
- Delivery consistency score.
- Project timing risk.

### Dependency

These should be shaped through partner rehearsal feedback. The first step can be a D8.x metric dictionary and prototype, followed by pilot use once real project records exist.

## Multi-Partner Expansion Analysis

HOSUN, JOOBOO, Chongqing Huiju, and future partners should share the same operating loop:

Customer Development -> Campaign -> Manual Outreach -> Quote -> Order -> Partner Split -> Supplier Confirmation -> Production -> Shipment -> Portal -> Feedback -> Market Response -> Partner Onboarding.

They should not share every product field or operating metric. The correct model is shared workflow plus partner-specific configuration.

### Shared Across Partners

- Customer and contact records.
- Lead and segment context.
- Campaign planning.
- Manual outreach task lifecycle.
- Quote and order linkage.
- Partner split / supplier confirmation.
- Production and shipment status concepts.
- Feedback ticket lifecycle.
- Market Response advisory workflow.
- Portal-safe field whitelist.
- Audit, RBAC, and safety boundaries.

### Partner-Specific

- Product attributes.
- Customer segmentation rules.
- Quote logic and approval thresholds.
- Delivery milestones.
- Shipment risk tags.
- Feedback categories.
- Market Response metrics.
- Resource center taxonomy.
- Portal-visible copy and product documentation.

### Roadmap Implication

The next architecture decision should avoid hardcoding HOSUN or JOOBOO-specific fields into the shared core. Instead, PartnerOS should define a partner capability profile:

- Product families.
- Required product fields.
- Quote rules.
- Production milestone templates.
- Shipment risk taxonomy.
- Feedback taxonomy.
- Market Response metrics.
- Portal-safe display rules.

This can start as documentation and prototype configuration in D8.x, become pilot data during real partner operation, and later become a platform-level configuration model.

## External Integrations Roadmap

External integrations should not be connected until manual workflows are validated.

### Integration Candidates

- Constant Contact: campaign audience sync and email activity import.
- Sales CRM / 销售易: lead, account, opportunity, and follow-up synchronization.
- Email: manual draft handoff or activity logging.
- Carrier APIs: shipment status ingestion after manual status model is stable.
- Accounting: invoice, payment, PO, PI, and reconciliation.

### Required Gates Before Integration

- Clear owner and rollback plan.
- RBAC and audit events.
- Field mapping and forbidden-field review.
- Token storage and rotation policy.
- Sandbox credentials.
- No automatic customer/supplier action without explicit operator approval.

Suggested stage: Later, except for documentation and field mapping that can begin in D8.x.

## Production Deployment, Backup, Monitoring, and Security Hardening

Before pilot or production coordination, PartnerOS needs:

- Environment-specific configuration checklist.
- HTTPS and allowed-origin verification.
- Secret storage policy.
- Database backup and restore rehearsal.
- Migration rollback strategy.
- Runtime monitoring.
- Error logging and alerting.
- Access review.
- API rate limits where appropriate.
- File storage retention policy.
- Incident response runbook.

These are P0 for real pilot credibility, even if feature development is otherwise ready.

## Recommended Next Sequence

1. D8.x: collect real partner rehearsal feedback using the D8.18 feedback form.
2. D8.x: prepare P0 staging credential checklist, Portal forbidden-field audit matrix, RBAC role matrix, audit taxonomy, and real data import templates.
3. D8.x: draft HOSUN and JOOBOO metric dictionaries.
4. D8.x: refine customer Portal surfaces from real partner feedback.
5. Pilot: import real partner/customer/product/order data into a controlled environment.
6. Pilot: run real campaign, quote, order, feedback, and Market Response loops with human operators.
7. Later: connect external integrations only after manual workflows and data boundaries are proven.

## Decision Summary

D8.19 identifies the next work as product planning and controlled readiness, not broad new automation. The strongest near-term focus is:

- Real staging and Portal safety.
- RBAC and audit.
- Real data import.
- Partner-specific metrics for HOSUN and JOOBOO.
- Task/handoff and quote approval workflows.
- Pilot-ready backup, monitoring, and security hardening.

The system should remain READY_FOR_STAGING_HANDOFF until real service Portal credentials and origin are verified.
