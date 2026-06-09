# Staging Credentials Request Pack

Status: READY_FOR_STAGING_HANDOFF

Purpose: give the `service.intelli-opus.com` integration owner a clear list of private staging values and UAT checks required before PartnerOS can move from local handoff readiness to real staging validation.

## Current State

PartnerOS is ready for staging handoff, but real external staging has not been validated. The external evidence state remains WAITING_FOR_REAL_STAGING_EVIDENCE.

Do not mark the project as externally staging validated until the real `service.intelli-opus.com` staging environment is configured, connected, and tested with the private values below.

## Values Needed From The Staging Owner

1. Backend HTTPS origin
   - Example shape: `https://partneros-staging.example.com`
   - Must be reachable by `service.intelli-opus.com`.
   - Must terminate HTTPS with a valid certificate.

2. `PORTAL_CUSTOMER_API_TOKEN`
   - Private server-to-server token used by the customer-facing Portal to call PartnerOS bridge APIs.
   - Must not be committed to Git.
   - Must not appear in screenshots, logs, docs, or browser-visible frontend code.

3. `PORTAL_CUSTOMER_ALLOWED_ORIGINS`
   - Expected origin for the customer-facing Portal.
   - Initial expected value: `https://service.intelli-opus.com`
   - Add only explicitly approved staging or preview origins.

4. `PUBLIC_BASE_URL`
   - Public backend URL used for safe generated links and runtime self-reporting.
   - Should match the real backend HTTPS origin unless the deployment topology requires a different public URL.

5. Server-to-server token confirmation
   - Confirm whether `service.intelli-opus.com` will send the token through the agreed server-to-server header.
   - Confirm whether token rotation is required before UAT.
   - Confirm who owns token storage and rotation outside Git.

## Suggested Request Message

Please provide the real staging configuration values needed for PartnerOS customer Portal bridge UAT:

- Backend HTTPS origin reachable from `service.intelli-opus.com`.
- `PORTAL_CUSTOMER_API_TOKEN` private server-to-server value.
- `PORTAL_CUSTOMER_ALLOWED_ORIGINS`, expected to include `https://service.intelli-opus.com`.
- `PUBLIC_BASE_URL` for the PartnerOS staging backend.
- Confirmation that `service.intelli-opus.com` will call the PartnerOS bridge API using server-to-server token authentication.

Do not send token values through Git, shared screenshots, public docs, issue comments, or frontend code. Use the approved private secret channel.

## Required PartnerOS Runtime Settings

These are configuration names only; no secret values belong in the repository.

```text
PORTAL_CUSTOMER_API_ENABLED=true
PORTAL_CUSTOMER_API_REQUIRE_TOKEN=true
PORTAL_CUSTOMER_API_TOKEN=<private staging token>
PORTAL_CUSTOMER_ALLOWED_ORIGINS=https://service.intelli-opus.com
PUBLIC_BASE_URL=<real backend HTTPS origin>
```

## UAT Scope After Credentials Are Provided

Validate customer-visible bridge behavior for:

- Products.
- Orders.
- Production.
- Shipment.
- Resources.
- Feedback.

Validate forbidden-field safety for every customer-visible response:

- No internal cost.
- No margin.
- No pricing breakdown.
- No supplier private notes.
- No backend file path.
- No token.
- No internal-only storage path.

## Boundary Before Credentials Exist

Until the real backend HTTPS origin, `PORTAL_CUSTOMER_API_TOKEN`, allowed origin, and `PUBLIC_BASE_URL` are provided and verified, PartnerOS remains at READY_FOR_STAGING_HANDOFF and WAITING_FOR_REAL_STAGING_EVIDENCE.

The phrase `STAGING_VALIDATED` may only be used after real `service.intelli-opus.com` staging UAT has passed with the real private configuration.

Do not:

- Enter D9.
- Add proof records.
- Add Go/No-Go wording gates.
- Claim production coordination readiness.
- Commit `.env`, token values, generated PDFs, `IE Auto.pdf`, `local_data/`, or `backend/storage/`.
- Modify or deploy `service.intelli-opus.com` from this repository.

## Handoff Acceptance Criteria

The integration owner has supplied all private values through an approved private channel.

PartnerOS staging backend is reachable over HTTPS from the Portal runtime.

The Portal can fetch customer-visible products, orders, production, shipment, resources, and feedback.

Forbidden-field checks pass against real staging responses.

The result is documented as real staging evidence only after UAT completes.
