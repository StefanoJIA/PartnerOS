# D8.28 Redacted Credentials Register

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Register status: pending

No real staging credentials recorded in repository. This register records only redacted status for staging credentials and must never contain raw token values, unredacted endpoints copied from secret storage, screenshots, logs, or `.env` contents.

## Status Values

Allowed status values:

- pending
- received via secure channel
- configured
- verified
- rejected

## Redacted Register

| Item | Owner | Status | Redacted Value Only | Verification Owner | Verification Date | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| backend HTTPS origin | infrastructure / deployment operator | pending | PENDING_REAL_VALUE | security reviewer | pending | Do not invent endpoint |
| service.intelli-opus.com real origin | portal operator | pending | PENDING_REAL_VALUE | security reviewer | pending | Do not invent origin |
| `PORTAL_CUSTOMER_API_ENABLED` | backend operator | pending | PENDING_CONFIGURATION | security reviewer | pending | enabled=true only in staging |
| `PORTAL_CUSTOMER_API_TOKEN` | approved secret owner | pending | PROVIDED_VIA_SECURE_CHANNEL when received | security reviewer | pending | Do not record token value |
| `PORTAL_CUSTOMER_ALLOWED_ORIGINS` | backend operator / portal operator | pending | PENDING_REAL_VALUE | security reviewer | pending | No wildcard |
| `PUBLIC_BASE_URL` | infrastructure / deployment operator | pending | PENDING_REAL_VALUE | security reviewer | pending | Must match approved staging base URL |
| rollback owner | infrastructure / backend operator | pending | PENDING_OWNER | security reviewer | pending | Required before staging UAT |
| security reviewer | security reviewer | pending | PENDING_REVIEWER | business owner | pending | No real security sign-off recorded yet |
| business owner sign-off | business owner | pending | PENDING_SIGNOFF | security reviewer | pending | Required before exposing approved customer-safe data |

## Register Rules

- Do not record real token values.
- Do not record partial token values.
- Do not paste `.env` content.
- Do not paste screenshots containing secrets.
- Do not paste logs containing secrets.
- Do not invent backend HTTPS origin.
- Do not invent service.intelli-opus.com real origin.
- Do not mark pending as approved.
- Do not mark verified until real validation is complete.

## HOSUN Register Note

HOSUN fields remain pending unless business owner sign-off confirms customer-safe wording for lifting systems, desk frames, desk legs, lifting columns, and heavy-duty supply, including load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, and project demand.

## JOOBOO And Future Partner Register Note

JOOBOO and future partner fields remain pending unless sign-off confirms education furniture, school desks/chairs, project furniture, future partner onboarding data, product family, quote logic, delivery requirement, resource taxonomy, and customer-visible fields.

## Boundary

- No real staging credentials recorded in repository.
- No real security sign-off recorded yet.
- No real business owner sign-off recorded yet.
- Pending does not mean approved.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not process or record real token values.
