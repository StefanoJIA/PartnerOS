# D8.21 Security Review Request

## Purpose

Request security review before real service Portal staging is enabled.

Current state: READY_FOR_STAGING_HANDOFF.

External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE.

## Review Scope

Please review the customer-facing Portal bridge between PartnerOS and `service.intelli-opus.com`.

Do not automatically enable any external action during this review.

## Questions for Security Reviewer

### Token Handling

- Where will `PORTAL_CUSTOMER_API_TOKEN` be stored?
- Who can read or rotate the token?
- How will token rotation be performed?
- How will we verify the token is not exposed to browser clients?
- How will we verify the token is not written into logs?
- How will we revoke the token if staging fails?

### CORS and Origin Boundary

- What is the exact real `service.intelli-opus.com` origin?
- Are there separate staging and production origins?
- Will `PORTAL_CUSTOMER_ALLOWED_ORIGINS` avoid wildcards?
- How will disallowed origins be tested?
- How will allowed origins be cleared during rollback?

### Customer-Safe Whitelist

Confirm that the Portal may read only:

- products
- orders
- production milestones
- shipment status
- resources
- feedback status
- customer-safe market signal preview

Confirm that field review covers every Portal bridge response.

### Forbidden Fields

Confirm the Portal does not expose:

- cost
- margin
- pricing breakdown
- supplier private notes
- backend file paths
- storage keys
- token values
- internal-only comments
- private partner notes
- unsafe raw database IDs

### Logs and Secret Exposure

- Do backend logs include token values?
- Do Portal logs include token values?
- Do API errors include internal paths or storage keys?
- Do screenshots or generated files contain secrets?
- Are `.env`, local data, storage, PDFs, and token files excluded from commit?

### External Action Safety

Confirm staging does not enable:

- automatic email
- automatic SMS
- automatic LinkedIn messages
- automatic customer notifications
- automatic supplier notifications
- real Constant Contact API
- real sales CRM / 销售易 API
- real carrier API
- quote status auto-change
- order status auto-change

## Requested Security Sign-Off

Security reviewer should provide:

- Approved / changes required:
- Required fixes before staging:
- Token storage approval:
- CORS approval:
- Forbidden-field review result:
- Logging review result:
- Rollback approval:
- Reviewer:
- Date:

No real staging validation should be claimed until this review and staging smoke test are complete.
