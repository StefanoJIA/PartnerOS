# Lead Intelligence MVP

**Status:** current on 2026-05-30.

## Purpose

Lead Intelligence is the market and customer intelligence track inside intelliOffice PartnerOS. It is not a separate CRM product and not an automated outreach system.

The current repository has already closed D5 through D7.9 and is in `READY_FOR_STAGING_HANDOFF` for D8. This document preserves the Lead Intelligence operating contract so D9 market-response work can build on the same evidence, scoring, and human-review rules.

## Positioning

Lead Intelligence connects:

- company and contact data
- product interest and website evidence
- market fit segments
- lead scoring
- human-reviewed interactions
- next action planning
- quote, order, feedback, and market-response loops

The core loop is:

```text
Company -> Contact -> Evidence / Tags -> Score -> Interaction -> Next Action
```

The goal is to help operators prioritize real customer development work, especially around lifting systems, sit-stand workstations, desk frames, lifting columns, heavy-duty adjustable products, ergonomic workstations, education, healthcare, and OEM/ODM signals.

## Stable Market Fit Segments

| Segment | Meaning |
|---|---|
| `lift_system_signal` | Explicit lifting, sit-stand, adjustable, desk frame, column, or ergonomic lift signal |
| `general_office_furniture_only` | Office furniture relevance without enough evidence for lifting-system priority |
| `education_vertical` | Education, campus, classroom, or learning-environment context |
| `medical_vertical` | Medical, healthcare, lab, or clinical workstation context |
| `project_based_furniture` | Contract interiors, installation, rollout, or project procurement signal |
| `oem_odm_fit` | OEM, ODM, private-label, or manufacturing partnership fit |
| `heavy_duty_fit` | Heavy-duty, industrial, high-load, or robust adjustable product context |

`general_office_furniture_only` is not a negative label. It means the current evidence is too broad for lifting-system prioritization and should usually be nurtured or enriched before escalation.

## Current Implementation Anchors

- Scoring service: `backend/app/services/a_domain/intelligence_score.py`
- A-domain routes: `backend/app/api/routes/a_domain.py`
- Workbench: `/lead-intelligence`
- Public-source enrichment: [Public-Source Enrichment MVP](public_source_enrichment_mvp.md)
- Market response loop: [D9.3 Market Response Loop](phase3/d9_3_market_response_loop.md)

## Human Review Rules

Lead Intelligence may suggest tags, summaries, and segments. It must not silently overwrite formal CRM facts.

Operators must review suggestions before accepted facts are applied. Rejections should be kept as evidence so the same weak signal is not repeatedly treated as new.

## Safety Boundaries

Lead Intelligence must not:

- scrape LinkedIn or bypass platform rules
- send email, campaigns, webhooks, or automatic outreach
- create RFQs, quotes, orders, shipments, or feedback tickets automatically
- notify customers or suppliers
- change quote or order statuses
- call carrier APIs
- privilege HOSUN, JOOBOO, or any other partner by hard-coded default
- expose internal cost, margin, pricing breakdowns, supplier private notes, backend paths, storage keys, tokens, or secrets

AI-assisted output remains advisory and human-reviewed.

## Validation

```powershell
cd backend
python scripts/lead_intelligence_docs_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
```

## Related Docs

- [Public-Source Enrichment MVP](public_source_enrichment_mvp.md)
- [Lead Intelligence Scoring Notes](lead_intelligence_scoring_notes.md)
- [Migration From Web Development To Desktop Product](migration_from_web_to_desktop.md)
- [Product Vision](product_vision.md)
