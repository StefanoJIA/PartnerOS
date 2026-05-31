# Manual A-Domain Test Plan

**Status:** current on 2026-05-30.

## Purpose

This plan guides human UAT for the A-domain Lead Intelligence workflow. It complements automated checks and keeps manual customer-entry validation aligned with the current `READY_FOR_STAGING_HANDOFF` state.

Manual A-domain testing is not staging evidence, not permission to use real secrets in docs, and not an authorization to contact customers automatically.

## Scope

The test plan covers:

- manual company and contact entry
- Lead Intelligence scoring review
- public-source enrichment review
- interaction and next-action recording
- evidence quality review
- segment quality review
- handoff signals for later RFQ, quote, order, and market-response work

The canonical record template is [Manual Test Record Template](templates/manual_test_record_template.md).

## Preconditions

Use the current local D7.6+/D8 validation port:

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/dev_runtime_doctor.py
python scripts/lead_intelligence_docs_check.py
python scripts/manual_a_domain_test_plan_check.py
```

Open the frontend with `VITE_API_PROXY_TARGET` pointed at `http://127.0.0.1:8014`, then use `/lead-intelligence`.

Do not paste real tokens, private customer files, raw response bodies, or screenshots with secrets into test records.

## Manual Data Entry Rules

Company minimum fields:

- company name
- website when enrichment is expected
- country or market
- business description or notes
- product interest context

Contact minimum fields:

- name
- title or role when known
- email or phone only when safe and already available to the operator
- source note if the contact came from public research

Interaction minimum fields:

- interaction type
- channel
- subject or summary
- next action
- due date when applicable
- evidence or rationale for lead priority

## Segment Review Matrix

| Scenario | Expected review |
|---|---|
| General office furniture dealer | Usually `general_office_furniture_only`; should not also show `lift_system_signal` without lift evidence |
| Height-adjustable desk seller | `lift_system_signal` expected |
| Desk frame, lifting column, or lifting leg supplier | `lift_system_signal` expected |
| Heavy-duty adjustable product | `heavy_duty_fit` and possibly `lift_system_signal` |
| Education furniture supplier | `education_vertical` expected when evidence supports it |
| Healthcare or lab workstation supplier | `medical_vertical` expected when evidence supports it |
| Contract interiors or installation project firm | `project_based_furniture` when project evidence is present |
| OEM/ODM without lifting context | Do not force `oem_odm_fit` |
| OEM/ODM with lifting context | `oem_odm_fit` may be appropriate |

Record mismatches as `segment_rule` or `scoring_rule` issues, with the exact evidence text that caused the result.

## Public-Source Enrichment UAT

For companies with websites:

1. Run public-source enrichment only when allowed by local config.
2. Confirm evidence URLs stay same-origin and limited to approved paths.
3. Confirm suggestions remain pending until reviewed.
4. Accept or reject suggestions explicitly.
5. Apply only accepted suggestions.
6. Confirm applied changes write activity history.

If `PUBLIC_ENRICHMENT_ENABLED=false`, enrichment run creation should be blocked rather than silently falling back to external access.

## Expected Outcomes

After a successful manual pass:

- Lead Intelligence opens at `/lead-intelligence`.
- Company and contact records can be reviewed without corrupting formal data.
- Scoring explains `lift_system_signal`, `general_office_furniture_only`, `project_based_furniture`, `oem_odm_fit`, and related segment choices.
- Enrichment suggestions are evidence-backed and human-reviewed.
- Interactions and next actions are visible to the operator.
- Test records contain only redacted summaries and issue classifications.

## Issue Types

Use these issue types in manual records:

- `data_entry`
- `frontend_error`
- `backend_error`
- `scoring_rule`
- `segment_rule`
- `enrichment_evidence`
- `documentation`
- `safety_boundary`

## Safety Boundaries

Manual A-domain testing must not:

- send email, LinkedIn messages, campaigns, webhooks, or customer notifications
- notify suppliers
- create RFQs, quotes, orders, shipments, or feedback tickets automatically
- call carrier APIs
- scrape LinkedIn or bypass platform rules
- expose internal cost, margin, pricing breakdowns, supplier private notes, backend paths, storage keys, tokens, or secrets
- commit `.env`, `local_data/`, `backend/storage/`, uploads, generated logs, or private customer files

## Validation

```powershell
cd backend
python scripts/manual_a_domain_test_plan_check.py
python scripts/lead_intelligence_docs_check.py
python scripts/project_execution_chain_gate_check.py
python scripts/project_execution_chain_check.py
python scripts/d8_staging_execution_pack_check.py
python scripts/project_execution_acceptance_audit_check.py
```

## Related Docs

- [Lead Intelligence MVP](lead_intelligence_mvp.md)
- [Public-Source Enrichment MVP](public_source_enrichment_mvp.md)
- [Lead Intelligence Scoring Notes](lead_intelligence_scoring_notes.md)
- [Manual Test Record Template](templates/manual_test_record_template.md)
