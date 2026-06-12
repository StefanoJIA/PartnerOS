# D8.28 Staging Go/No-Go Checklist

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Decision status: pending

No real staging credentials recorded in repository. No real security sign-off recorded yet. No real business owner sign-off recorded yet. This Go/No-Go checklist is a future decision template for real staging UAT, not a current approval.

## Go/No-Go Decision Table

| Gate | Required Evidence | Status | Decision Notes |
| --- | --- | --- | --- |
| backend HTTPS origin verified | `/health` succeeds over approved backend HTTPS origin | pending | pending |
| token configured securely | token configured through secure channel without repository exposure | pending | pending |
| CORS allowed origin verified | approved service.intelli-opus.com origin succeeds | pending | pending |
| disallowed origin rejected | non-allowlisted origin fails safely | pending | pending |
| forbidden fields absent | payload audit confirms no forbidden fields | pending | pending |
| security signoff approved | real security reviewer completes signoff | pending | pending |
| business owner signoff approved | real business owner approves customer-safe fields and wording | pending | pending |
| UAT seed data approved | staging-safe seed records approved | pending | pending |
| rollback owner assigned | named owner can disable Portal API and revoke token | pending | pending |
| P0 blockers absent | no unresolved P0 security, data, or staging blocker | pending | pending |
| allow real staging UAT | all required gates pass | pending | pending |
| STAGING_VALIDATED wording | still forbidden until real smoke test passes and is reviewed | pending | pending |

## Decision Outcomes

| Outcome | Meaning | Allowed Action |
| --- | --- | --- |
| No-Go | One or more P0 gates fail or remain pending | Do not start real staging UAT |
| Conditional Go | Minor non-P0 issues remain with owner/date | Run limited staging UAT only if security reviewer and business owner agree |
| Go | All required gates pass with real evidence | Enter real staging UAT; do not write STAGING_VALIDATED until smoke tests fully pass and are reviewed |

## HOSUN Required Sign-Off

Before real staging UAT includes HOSUN, business owner approval must cover lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply:

- load
- stability
- noise
- delivery
- installation
- after-sales
- packaging
- warranty
- test cycle
- certification
- project demand

If any HOSUN field remains pending, it must be excluded from customer-visible staging payloads.

## JOOBOO Required Sign-Off

Before real staging UAT includes JOOBOO, business owner approval must cover:

- education furniture
- school desks/chairs
- project furniture
- school procurement timing
- delivery consistency
- installation
- resource needs
- feedback after use
- project acceptance criteria

If any JOOBOO field remains pending, it must be excluded from customer-visible staging payloads.

## Future Partner Required Sign-Off

Before real staging UAT includes a future partner, business owner approval must cover:

- future partner onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields
- Market Response metrics

If any future partner field remains pending, it must be excluded from customer-visible staging payloads.

## Boundary

- Pending does not mean approved.
- Do not fabricate credentials.
- Do not fabricate sign-off.
- Do not write STAGING_VALIDATED before real smoke test evidence passes and is reviewed.
- Do not enter D9.
- Do not create proof records.
- Do not process or record real token values.
