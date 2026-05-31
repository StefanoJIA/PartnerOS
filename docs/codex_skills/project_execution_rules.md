# Project Execution Rules

- Inspect current worktree state before editing.
- Prefer existing service/API/UI/smoke patterns over new abstractions.
- Keep changes scoped to the requested D stage and current execution state.
- Update docs and smoke checks with each implemented stage.
- Treat PartnerOS as internal source of truth; public portal work is bridge/API only unless explicitly requested.
- Do not deploy or modify `service.intelli-opus.com`, nginx, cloud upstreams, carrier APIs, webhooks, or notification systems from this repository.
- Preserve `READY_FOR_STAGING_HANDOFF` until real strict staging evidence proves `STAGING_VALIDATED`.
- Treat `WAITING_FOR_REAL_STAGING_EVIDENCE` as a hard stop after local rehearsal evidence is saved where strict staging evidence is expected.
- Run `python scripts/project_execution_chain_gate_check.py`, `python scripts/d8_staging_execution_pack_check.py`, `python scripts/project_execution_acceptance_audit_check.py`, and `python scripts/project_execution_status.py` before claiming the current stage.
- Commit and push only after required acceptance checks pass.
