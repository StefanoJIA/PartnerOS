# Product Vision

**Status:** current on 2026-05-30. This document describes the product direction for intelliOffice PartnerOS. It is a product framing document, not a staging proof, production deploy runbook, or final-user installation guide.

## Product Definition

intelliOffice PartnerOS is a local-first, AI-assisted operations system for U.S.-facing furniture and workspace supply-chain work. It keeps market intelligence, sales execution, partner/product matching, quote/order execution, production/shipment tracking, customer-visible bridge data, and operating records in one internal source of truth.

The public customer-facing portal remains `service.intelli-opus.com`. PartnerOS must not deploy or modify that service from this repository; it provides internal workflows and carefully whitelisted bridge APIs.

PartnerOS is not:

- a generic CRM-only website
- a supplier database detached from orders and market response
- a customer portal replacement
- a system that requires final users to run PostgreSQL, pgAdmin, Docker, Alembic, or raw SQL
- an automation layer that sends email, webhooks, carrier API calls, supplier notifications, or customer notifications without an explicit future safety design

## Current Execution State

D5 Lead Intelligence is closed. D6 Quote MVP is closed. D7 is closed through D7.9, covering order lifecycle, confirmations, partner/supplier execution, production milestones, shipment plans, customer portal bridge APIs, feedback intake, and resource center foundations.

D8 is currently `READY_FOR_STAGING_HANDOFF`: local docs, gates, and handoff runbooks agree, but real strict staging evidence still requires private staging values. D9 operating loops remain planned behind `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, production coordination, and the human Go / No-Go handoff.

Local handoff claims must be backed by `python scripts/d8_staging_execution_pack_check.py`, `python scripts/d9_operating_execution_pack_check.py`, and `python scripts/project_execution_acceptance_audit_check.py`. These checks prove internal alignment only; they do not replace strict staging evidence.

## Value Loop

The product value loop is:

Market demand signals -> customer intelligence -> lead scoring and segmentation -> human-reviewed outreach -> product fit -> peer manufacturing partner matching -> RFQ -> quote -> customer decision -> order -> production milestones -> shipment plans -> customer-visible portal summaries -> feedback -> operating review -> market response and improvement backlog.

Lead Intelligence belongs inside this loop. It must not become an isolated lead database or standalone scraping tool; its outputs should feed quote preparation, order readiness, partner matching, and operating review.

## Operating Domains

| Domain | Purpose |
|---|---|
| Market and Customer Intelligence | Company discovery, lead scoring, segmentation, market signals, and response intelligence |
| Sales Execution | Leads, companies, contacts, interactions, tasks, follow-up rhythm, and human-reviewed outreach |
| Product and Manufacturing Partners | Products, manufacturing partners, capabilities, certificates, quality signals, and peer partner matching |
| Quote and Order Execution | RFQs, quote records, quote versions, quote PDFs, manual delivery tracking, order readiness, orders, confirmations, production milestones, shipment plans, and feedback intake |
| AI and Knowledge | Advisory AI outputs, prompts, knowledge records, product/partner suggestions, and market trend analysis |
| System Services | Authentication, runtime health, readiness, files, activity logs, diagnostics, staging handoff, records hygiene, and packaging support |

## Business Rules

The intelliOffice brand is the U.S.-facing sales and project platform. HOSUN, JOOBOO, and any future factories are peer manufacturing partner rows in `manufacturing_partners`.

Do not hard-code, default, or prioritize any partner by trade name. Matching and ranking must use structured signals such as product fit, quality, certification, price, MOQ, lead time, sample support, communication, project suitability, and U.S. market readiness.

AI is advisory. It may draft, summarize, classify, or recommend, but human operators own outreach, customer commitments, supplier coordination, production status, shipment status, and feedback responses.

## Customer Portal Boundary

Customer-visible data must be explicitly whitelisted. Bridge APIs may expose customer-safe summaries for orders, confirmations, production, shipment plans, resources, and feedback intake.

Bridge APIs must not expose internal cost, margin, pricing breakdowns, cost snapshots, supplier private notes, backend storage paths, storage keys, raw response bodies, tokens, or internal operator-only comments.

Feedback intake creates internal review work only. It must not auto-reply, notify customers, upload attachments, or promise resolution times.

## Manual-Only Safety

The following remain manual operator records unless a future stage explicitly changes the rule and adds safety gates:

- customer confirmations
- partner splits
- supplier confirmations
- production milestones
- shipment plans and shipment status summaries
- feedback handling records

Shipment plans do not call carriers, send webhooks or email, notify suppliers/customers, or automatically change an order to shipped/delivered.

## Current Roadmap Direction

The current path is:

1. Preserve D5-D7 closed behavior.
2. Complete D8 staging handoff with real private staging evidence.
3. Use production coordination only after `STAGING_VALIDATED` and `READY_FOR_PRODUCTION_COORDINATION_REVIEW`.
4. Start D9 operating loops after production coordination and the human Go / No-Go handoff; if committed, use `docs/records/d8_production_go_no_go_YYYYMMDD.md`.
5. Keep future desktop packaging and local-first polish aligned with the current runtime and data lifecycle docs.

## Related Documents

- [Project Reorientation Summary](project_reorientation_summary.md)
- [Desktop Target Architecture](architecture_desktop_target.md)
- [Desktop Transition Roadmap](roadmap_desktop_transition.md)
- [Developer Guide](dev_guide.md)
- [Operator Guide](operator_guide.md)
- [Testing Guide](testing.md)
- [Integrated Backend Standards](integrated_backend_standards.md)
- [Phase 3 Roadmap](phase3/phase3_roadmap.md)
