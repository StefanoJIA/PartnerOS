# Portal Bridge Rules

- `service.intelli-opus.com` remains customer-facing.
- PartnerOS exposes bridge APIs under `/api/v1/portal/customer`.
- Default customer portal bridge setting is disabled.
- Use server-to-server token auth; real token values stay in deployment secrets or local `.env` only.
- Responses must use explicit customer-facing field whitelists.
- Feedback intake creates PartnerOS feedback tickets only; no auto-reply, no customer notification, no resolution-time promise.
- Resources expose customer-safe metadata only, never storage keys or backend file paths.
- D7.8 local/live integration checks use `scripts/d7_8_portal_live_integration_check.py`; D8 strict staging evidence uses `scripts/d8_strict_staging_evidence_check.py`.
- Staging tokens must be entered only as masked local page state, environment variables, or deployment secrets; do not persist, screenshot, or print them.
- UAT feedback must be marked `TEST` until production customer data is explicitly approved.
- Feedback operations happen in `/feedback-tickets`; status, priority, owner, and response summaries are internal handling records only.
- Feedback operations must not send email, notify customers, upload attachments, or promise an SLA.
- Do not edit nginx, cloud upstreams, or the live service portal from this repository.
