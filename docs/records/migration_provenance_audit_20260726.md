# Migration Provenance Audit — 2026-07-26

Branch: `feat/e2e-supplier-convergence` @ `24e234a`  
Baseline: `master@c2c2064`  
Classification: **first release before migration history correction**

## Modified revisions (c2c2064 → 24e234a)

| Revision | Change type | Downgrade touched? |
|---|---|---|
| `0023_quote_learning_records` | `upgrade()` only: `table_exists` guard before `create_table` | No |
| `0024_win_loss_capture` | `upgrade()` only: `column_exists` / `index_exists` guards before add | No |
| `0025_pricing_assumptions` | `upgrade()` only: `table_exists` guard + skip seed when rows exist | No |

No column types, nullable flags, PK/FK targets, or downgrade paths were altered.

## Why `0001_initial` causes duplicate objects

`0001_initial` executes `Base.metadata.create_all()` against **current** SQLAlchemy models. Later revisions (e.g. `0023`) were authored as incremental `op.create_table` / `op.add_column` steps. On a **fresh** database today, `create_all` already materializes tables/columns that `0023`–`0025` attempt to add again.

This is a pre-existing bootstrap pattern issue, not introduced by the RC feature commits.

## Path results

| Path | Command | Exit | Alembic head | Notes |
|---|---|---|---|---|
| **legacy empty** (`c2c2064` files) | `alembic upgrade head` on empty DB | **FAIL** | — | Fails at `0023` (`DuplicateTable: quote_learning_records`) |
| **fresh RC** (`24e234a` files) | `alembic upgrade head` on empty DB | **PASS** | `0025_pricing_assumptions` | Guards skip duplicate DDL |
| **incremental dev** (existing local DB) | already at head | — | `0025_pricing_assumptions` | Represents historical incremental upgrades |

Legacy empty-path failure is **expected** and pre-dates the guard patch. Shared staging/production empty-install was not observed; local dev DB reached head incrementally.

## Schema equivalence (fresh RC empty vs incremental dev)

Compared via `information_schema` + `pg_constraint` on Docker PostgreSQL 5435:

| Dimension | fresh_rc (`partneros_fresh_rc_path`) | incremental (`partneros`) | Equivalent? |
|---|---|---|---|
| Tables | 74 | 74 | Yes |
| Alembic version | `0025_pricing_assumptions` | `0025_pricing_assumptions` | Yes |
| Columns (name/type/nullable) | match | match | Yes |
| Column defaults | often empty in dump | explicit migration defaults | **Semantically equivalent** |
| Unique on `feedback_tickets.ticket_number` | unique index `ix_feedback_tickets_ticket_number` | unique constraint `uq_feedback_tickets_ticket_number` | **Functionally equivalent** |

No missing tables, types, or FK targets identified. Differences are default literal representation and constraint naming from `create_all` vs incremental migrations.

## Shared-environment risk assessment

| Question | Finding |
|---|---|
| Has staging/production run pre-guard `0023`–`0025` on empty install? | **No evidence**; blocked on credentials anyway |
| Has local dev run incremental migrations? | Yes — schema matches fresh RC at head |
| Do guards change already-applied DBs? | No — guards no-op when objects exist |
| Is `alembic_version` tampering required? | **No** |

## Decision

**Proceed with RC guards retained.** Mark as *first release before migration history correction*. Staging deploy should pin **`24e234a`** (or later chore commit on same branch).

Long-term follow-up (not this PR): replace `0001 create_all` bootstrap with explicit baseline revision or squash before first production cut.

## Rollback

- Application: redeploy prior SHA `244d133` or `master@c2c2064` (portal/site flags off).
- Database: restore pre-deploy backup; do not manually edit `alembic_version`.
- Empty-install regression: use current branch migrations only after this audit.
