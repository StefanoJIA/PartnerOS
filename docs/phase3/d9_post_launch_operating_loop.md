# D9 Post-Launch Operating Loop

**Status:** planned on 2026-05-30; starts only after D8 `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, production coordination, and human Go / No-Go handoff.

## Purpose

D9 turns the deployed PartnerOS and existing service portal bridge into a monitored operating loop. It focuses on learning from real order operations, Portal feedback, shipment/production follow-through, and Market response intelligence without introducing automatic business actions.

## Entry Criteria

| Gate | Required evidence |
|---|---|
| D8 staging | `python scripts/d8_readiness_audit.py` reports `STAGING_VALIDATED` |
| D8 real-evidence wait cleared | `python scripts/d8_production_coordination_check.py` does not report `WAITING_FOR_REAL_STAGING_EVIDENCE` |
| D8 production handoff | [D8 Production Coordination Plan](d8_production_coordination_plan.md) Go / No-Go completed |
| D8 evidence review | `python scripts/d8_staging_evidence_review_check.py` reports `READY_FOR_PRODUCTION_COORDINATION_REVIEW` |
| D8 Go / No-Go record | If committed, the redacted decision record uses `docs/records/d8_production_go_no_go_YYYYMMDD.md` |
| Records | Redacted D8 evidence and any gap register are saved under canonical `docs/records/d8_*_YYYYMMDD` names |
| Safety | Portal bridge still hides internal cost, margin, pricing breakdown, supplier private notes, backend paths, storage keys, tokens, and secrets |

## Stage Goals

| Stage | Goal | Primary evidence |
|---|---|---|
| [D9.1 Operating Health Review](d9_1_operating_health_review.md) | Track portal bridge health, readiness, CORS, token rejection, and customer-safe reads after production coordination, evidence review, and human Go / No-Go handoff | recurring redacted evidence summary |
| [D9.2 Order Operations Loop](d9_2_order_operations_loop.md) | Review order confirmation, supplier confirmation, production milestones, shipment plans, resources, and feedback status as one operating queue | operator review record |
| [D9.3 Market Response Loop](d9_3_market_response_loop.md) | Feed Portal feedback, quote outcomes, product gaps, and demand signals into Market response intelligence | advisory recommendation review |
| [D9.4 Improvement Backlog](d9_4_improvement_backlog.md) | Convert repeated operational gaps into scoped implementation briefs for the next sprint | backlog / planning record |

## Operating Signals

- Portal feedback: customer-facing questions, complaints, product requests, resource requests, shipment questions.
- Order operations: missing confirmations, delayed production milestones, ready-to-ship orders without shipment plans, blocked resources.
- Market response intelligence: recurring product parameter gaps, win-loss reasons, category demand, partner capability fit.
- Human review: every recommended follow-up remains advisory until an operator accepts and acts outside automation.

## Acceptance

- Operators can see whether the production bridge is healthy without exposing tokens or raw response bodies.
- Feedback and market signals produce reviewed recommendations, not automatic customer replies.
- Order operations gaps become explicit backlog items with owner, evidence, and next action.
- No D9 artifact requires editing `service.intelli-opus.com`, nginx, or cloud upstreams from this repository.

## Records

D9 begins with [D9 Operating Execution Pack](d9_operating_execution_pack.md) and [D9 Operating Loop Kickoff](d9_operating_loop_kickoff.md), then records follow [D9 Operating Records Policy](d9_operating_records_policy.md).

```powershell
cd backend
python scripts/d9_operating_execution_pack_check.py
python scripts/d9_operating_loop_kickoff_check.py
python scripts/d9_operating_records_check.py
```

Use canonical `docs/records/d9_*_YYYYMMDD.md` names and store redacted summaries only.

## Safety Boundaries

- No automatic customer or supplier notification.
- No email, webhook, carrier API, LinkedIn, Outlook, or external send action.
- No automatic order, shipment, delivery, payment, or partner-selection mutation.
- No internal cost, margin, pricing breakdown, supplier private note, backend path, storage key, database URL, token, or secret in customer-visible payloads or evidence records.
- No nginx or service portal deployment from this repository.
