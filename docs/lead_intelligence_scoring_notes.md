# Lead Intelligence Scoring Notes

**Status:** current on 2026-05-30.

## Purpose

Lead Intelligence scoring is deterministic, explainable, and advisory. It helps operators prioritize outreach and market-response review, but it does not automate outreach, quote creation, order creation, partner selection, or customer commitments.

Implementation anchor: `backend/app/services/a_domain/intelligence_score.py`.

## Score Inputs

The score may use:

- primary contact presence
- market intelligence count
- company tags and business description
- lead product interest text
- priority and strategic level
- evidence-backed segment matches

## Segment Slugs

| Slug | Typical signal |
|---|---|
| `lift_system_signal` | sit-stand, lifting column, desk frame, ergonomic workstation, adjustable frame |
| `general_office_furniture_only` | office or contract furniture without clear lift keywords |
| `education_vertical` | campus, classroom, school, education furniture |
| `medical_vertical` | medical, healthcare, lab, clinical workstation |
| `project_based_furniture` | contract interiors, installation, rollout, procurement project |
| `oem_odm_fit` | OEM, ODM, private label, manufacturing partnership |
| `heavy_duty_fit` | heavy-duty, industrial, high-load adjustable use case |

Use `oem_odm_fit`; do not introduce a duplicate `oem_odm_signal` slug without an explicit migration plan.

## Operator Interpretation

High scores indicate prioritization candidates, not promises. Operators should verify business fit, timing, quantity, compliance, and relationship context before creating RFQs, quotes, orders, or partner actions.

Low or broad scores are not rejection decisions. They may mean the company needs more evidence, manual research, or lower-frequency nurture.

## Safety Boundaries

Scoring must not:

- automatically send LinkedIn, email, campaigns, webhooks, or notifications
- automatically create RFQs, quotes, orders, shipments, feedback tickets, or partner recommendations
- change quote or order statuses
- expose internal cost, margin, pricing breakdowns, supplier private notes, backend paths, storage keys, tokens, or secrets
- privilege any manufacturing partner by hard-coded default

## Validation

```powershell
cd backend
python scripts/lead_intelligence_docs_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
```
