# D8.32 Security Review Request Message

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Message status: template only, not sent

No external message has been sent from this template. This request is for a future manual security review and must not be treated as real security approval.

## Copyable Message Template

Subject: PartnerOS Portal bridge security review request

Hello [Security Reviewer],

PartnerOS is ready for a security review before real service Portal staging validation. Current state remains `READY_FOR_STAGING_HANDOFF`; external staging remains `WAITING_FOR_REAL_STAGING_EVIDENCE`. We are not asking you to approve production or D9 entry in this message.

Please review the following areas:

1. Token storage / rotation / revocation.
2. CORS / allowed origins / no wildcard.
3. Server-to-server Portal bridge boundary.
4. Forbidden field audit.
5. Logs / screenshots / docs secret exposure risk.
6. Browser must not see token values.
7. No automatic external sending: email, SMS, LinkedIn, customer notification, supplier notification, webhook, carrier API.
8. No quote/order auto-change from Portal reads.
9. Rollback / disable Portal API.

Reference docs:

- `docs/phase3/d8_27_security_review_readiness_checklist.md`
- `docs/phase3/d8_27_secret_handling_dry_run.md`
- `docs/phase3/d8_27_forbidden_field_audit_matrix.md`
- `docs/phase3/d8_27_security_signoff_template.md`
- `docs/phase3/d8_29_staging_failure_triage.md`

Expected reply:

- required fixes
- whether token/CORS/log/forbidden-field boundaries are acceptable
- whether rollback procedure is acceptable
- signoff status: pending / approved / changes required

Please do not include raw token values or secret screenshots in the reply.

## HOSUN Security Focus

For HOSUN, please confirm internal-only handling for raw test notes, complaint details, delivery risk analysis, warranty cost exposure, supplier private notes, and internal Market Response scoring. Customer-facing wording for lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply, load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, and project demand must require business sign-off and customer-safe review.

## JOOBOO / Future Partner Security Focus

Please confirm customer-visible boundaries for education furniture, school desks/chairs, project furniture, future partner onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, and Market Response metrics.

## Boundary

- Template only; not sent.
- No real security approval recorded.
- Do not process or record real token values.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
