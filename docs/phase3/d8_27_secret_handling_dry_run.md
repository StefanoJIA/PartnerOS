# D8.27 Secret Handling Dry-Run

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Dry-run status: local documentation dry-run only

No real security sign-off recorded yet. This dry-run records the expected local handling rules for secrets and forbidden fields without using real token values and without validating real staging.

## Dry-Run Scope

This dry-run checks local documentation boundaries:

- no real token is used
- wrong/missing token should fail safely in real staging smoke
- disabled state should fail safely
- token values must not be written into docs
- token values must not appear in log examples
- `.env`, `local_data/`, `backend/storage/`, generated PDFs, and `IE Auto.pdf` must not be committed
- current result is dry-run only, not real security approval

## No Real Token Used

This D8.27 task does not read, request, paste, generate, store, rotate, or revoke a real token. Placeholder names such as `PORTAL_CUSTOMER_API_TOKEN` are configuration keys, not secret values.

## Wrong/Missing Token Safe Failure

Expected future staging behavior:

| Case | Expected Result | Status |
| --- | --- | --- |
| missing token | request rejected safely | pending real staging smoke |
| wrong token | request rejected safely | pending real staging smoke |
| expired token | request rejected safely | pending real staging smoke |
| revoked token | request rejected safely | pending real staging smoke |

This document does not claim the above has been validated on service.intelli-opus.com.

## Disabled State Safe Failure

Expected future staging behavior:

| Case | Expected Result | Status |
| --- | --- | --- |
| `PORTAL_CUSTOMER_API_ENABLED=false` | customer Portal bridge unavailable or returns safe disabled response | pending real staging smoke |
| allowed origins cleared | browser origin rejected | pending real staging smoke |
| token revoked | server-to-server request rejected | pending real staging smoke |

## Token Not Written Into Docs

Dry-run rule:

- Do write configuration key names such as `PORTAL_CUSTOMER_API_TOKEN`.
- Do not write any real token value.
- Do not write partial token values.
- Do not write screenshots containing token values.
- Do not write token values into sign-off templates.

## Token Not Written Into Log Examples

Allowed log example:

```text
portal_bridge_auth=failed reason=missing_token request_id=<request-id>
```

Blocked log example:

```text
portal_bridge_auth=failed token=<real-token-value>
```

Logs must use request IDs, status, and failure reason without secret values.

## Files Not To Commit

The following must not be committed:

- `.env`
- `frontend/.env.local`
- `local_data/`
- `backend/storage/`
- generated logs containing sensitive data
- generated PDFs
- `IE Auto.pdf`
- token files
- screenshots containing secret values

## Local Dry-Run Result

| Check | Result | Notes |
| --- | --- | --- |
| no real token used | pending reviewer confirmation | This document uses config key names only |
| docs contain no token values | pending reviewer confirmation | Search required before real handoff |
| log examples contain no token values | pending reviewer confirmation | Examples use placeholders |
| forbidden local files excluded from commit | pending reviewer confirmation | Confirm with explicit staging and git status |
| real staging evidence | not claimed | Must remain WAITING_FOR_REAL_STAGING_EVIDENCE |
| security approval | pending | No real security approval recorded |

## Boundary

- Current result is dry-run only.
- This is not real security approval.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not process real token values.
- Do not fabricate real security approval.
