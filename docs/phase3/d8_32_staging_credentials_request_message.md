# D8.32 Staging Credentials Request Message

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Message status: template only, not sent

No external message has been sent from this template. Do not paste raw token values in email, chat, Git, docs, screenshots, logs, or issue comments.

## Copyable Message Template

Subject: PartnerOS staging credentials request for service.intelli-opus.com Portal bridge

Hello [Infrastructure / Backend / Portal Operator],

We are ready to request the real staging inputs required for PartnerOS customer Portal bridge validation. PartnerOS remains `READY_FOR_STAGING_HANDOFF`; external staging remains `WAITING_FOR_REAL_STAGING_EVIDENCE` until real credentials are received through secure channels and the smoke tests pass.

Please provide or confirm the following:

1. Backend HTTPS origin for PartnerOS staging.
2. service.intelli-opus.com real origin for the customer-facing Portal.
3. Owner responsible for configuring `PORTAL_CUSTOMER_API_ENABLED`.
4. Secure-channel owner for `PORTAL_CUSTOMER_API_TOKEN`.
5. `PORTAL_CUSTOMER_ALLOWED_ORIGINS` values.
6. `PUBLIC_BASE_URL` for staging.
7. Planned staging window.
8. Rollback owner who can disable Portal API and revoke/rotate token.

Important handling rules:

- Do not paste raw token values in this email/chat/Git/docs/screenshots/logs.
- Use an approved secure channel for `PORTAL_CUSTOMER_API_TOKEN`.
- In repo-visible tracking, record token status only as `PROVIDED_VIA_SECURE_CHANNEL`.
- Do not use wildcard origins.
- Do not mark any credential as verified until the real smoke test is complete.

Reference docs:

- `docs/phase3/d8_28_staging_credentials_intake_playbook.md`
- `docs/phase3/d8_28_redacted_credentials_register.md`
- `docs/phase3/d8_29_real_staging_smoke_test_plan.md`
- `docs/phase3/d8_30_d9_entry_gate.md`

Expected reply:

- owner for each item
- redacted status for each item
- planned staging window
- rollback owner
- secure channel confirmation for token transfer

Thank you.

## HOSUN / JOOBOO / Future Partner Note

Credentials are only one dependency. HOSUN lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply, load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, and project demand still require customer-safe/internal-only sign-off before customer-facing exposure.

JOOBOO education furniture, school desks/chairs, project furniture, and future partner onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, and Market Response metrics also require sign-off before pilot.

## Boundary

- Template only; not sent.
- Do not record real token values.
- Do not fabricate credentials.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
