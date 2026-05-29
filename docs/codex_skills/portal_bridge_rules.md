# Portal Bridge Rules

- `service.intelli-opus.com` remains customer-facing.
- PartnerOS exposes bridge APIs under `/api/v1/portal/customer`.
- Default customer portal bridge setting is disabled.
- Use server-to-server token auth for MVP; real token lives only in `.env`.
- Responses must use explicit customer-facing field whitelists.
- Feedback intake creates PartnerOS feedback tickets only; no auto-reply, no customer notification, no resolution-time promise.
- Resources expose customer-safe metadata only, never storage keys or backend file paths.
