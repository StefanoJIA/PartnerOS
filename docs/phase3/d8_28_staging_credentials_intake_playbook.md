# D8.28 Staging Credentials Intake Playbook

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Credentials intake status: pending

No real staging credentials recorded in repository. This playbook defines how intelliOffice should safely receive, record, validate, and roll back real staging credentials after the responsible operators provide them through secure channels. It does not handle real token values, does not connect to real staging, and does not write STAGING_VALIDATED.

## Required Credential Owners

Who provides/configures each required staging value:

- Who provides backend HTTPS origin: infrastructure / deployment operator.
- Who provides service.intelli-opus.com real origin: service.intelli-opus.com portal operator.
- Who configures `PORTAL_CUSTOMER_API_ENABLED`: intelliOffice backend operator.
- Who configures `PORTAL_CUSTOMER_API_TOKEN`: intelliOffice backend operator after secure-channel delivery from approved secret owner.
- Who configures `PORTAL_CUSTOMER_ALLOWED_ORIGINS`: intelliOffice backend operator using values approved by portal operator and security reviewer.
- Who configures `PUBLIC_BASE_URL`: intelliOffice backend operator using value from infrastructure / deployment operator.

| Item | Provider | Configuration Owner | Verification Owner | Status |
| --- | --- | --- | --- | --- |
| backend HTTPS origin | infrastructure / deployment operator | intelliOffice backend operator | security reviewer | pending |
| service.intelli-opus.com real origin | service.intelli-opus.com portal operator | portal operator | security reviewer | pending |
| `PORTAL_CUSTOMER_API_ENABLED` | intelliOffice backend operator | intelliOffice backend operator | security reviewer | pending |
| `PORTAL_CUSTOMER_API_TOKEN` | security reviewer or approved secret owner | intelliOffice backend operator through secure channel | security reviewer | pending |
| `PORTAL_CUSTOMER_ALLOWED_ORIGINS` | portal operator and security reviewer | intelliOffice backend operator | security reviewer | pending |
| `PUBLIC_BASE_URL` | infrastructure / deployment operator | intelliOffice backend operator | security reviewer | pending |

## Secure Channel Requirement

`PORTAL_CUSTOMER_API_TOKEN` and any other secret must be delivered only through an approved secure channel.

Do not write token values into:

- Git
- repository docs
- screenshots
- logs
- chat records
- issue comments
- pull requests
- frontend bundles
- exported PDFs

## Redacted Recording Rules

Credential records in this repository may only use redacted state values.

Allowed redacted examples:

- `token: PROVIDED_VIA_SECURE_CHANNEL`
- `backend HTTPS origin: PENDING_REAL_VALUE`
- `allowed origin: PENDING_REAL_VALUE`
- `PUBLIC_BASE_URL: PENDING_REAL_VALUE`

Forbidden examples:

- real token value
- partial token value
- copied `.env` content
- real secret screenshot
- unredacted internal endpoint pasted from secure storage

## Intake Steps

1. Business owner confirms that staging UAT is needed.
2. Security reviewer confirms credential intake owner.
3. Infrastructure / deployment operator provides backend HTTPS origin through the approved project channel.
4. Portal operator provides service.intelli-opus.com real origin through the approved project channel.
5. Backend operator configures `PORTAL_CUSTOMER_API_ENABLED` only in staging.
6. Secret owner provides `PORTAL_CUSTOMER_API_TOKEN` through secure channel only.
7. Backend operator configures `PORTAL_CUSTOMER_ALLOWED_ORIGINS` with explicit origin values; no wildcard.
8. Backend operator configures `PUBLIC_BASE_URL` for staging.
9. Redacted register is updated with status only, not raw secret values.
10. Secure validation plan is executed.
11. If validation fails, execute rollback / disable plan.

## Pending Rule

If any real value is not available, mark the item `pending`. Do not invent endpoint, token, origin, PUBLIC_BASE_URL, reviewer, date, or sign-off.

## Rollback / Disable Procedure

1. Set `PORTAL_CUSTOMER_API_ENABLED=false`.
2. Revoke or rotate `PORTAL_CUSTOMER_API_TOKEN`.
3. Clear or restrict `PORTAL_CUSTOMER_ALLOWED_ORIGINS`.
4. Confirm missing/wrong token fails safely.
5. Confirm service Portal receives safe disabled state.
6. Keep PartnerOS internal source of truth available.
7. Record only redacted rollback status in repository docs.

## HOSUN Pre-Staging Condition

Before HOSUN staging data is exposed, the business owner must approve customer-safe wording for lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply, including:

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

## JOOBOO And Future Partner Pre-Staging Condition

Before JOOBOO or future partner staging data is exposed, business owner sign-off must cover:

- education furniture
- school desks/chairs
- project furniture
- future partner onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields

## Boundary

- No real staging credentials recorded in repository.
- No real security sign-off recorded yet.
- No real business owner sign-off recorded yet.
- Pending does not mean approved.
- Do not enter D9.
- Do not create proof records.
- Do not write STAGING_VALIDATED.
- Do not fabricate credentials.
- Do not fabricate sign-off.
- Do not process or record real token values.
