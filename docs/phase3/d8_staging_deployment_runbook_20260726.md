# D8 Staging Deployment Runbook — 2026-07-26

**Status:** `READY_FOR_STAGING_HANDOFF` — document-only; does not deploy infrastructure.  
**Target release pin:** `04ebcb56883eff81cc8c3b953dfef4c3b47ccd72` (`04ebcb5`)  
**Source branch (reference only):** `feat/e2e-supplier-convergence` — **do not deploy a floating branch tip**  
**Alembic head:** `0025_pricing_assumptions`  
**Rollback application SHA:** `ae9a4b6` (prior RC guard commit) or `244d133` (last feature RC before chore-only commits)

## Purpose

This runbook gives the staging deployment operator exact, executable steps to deploy PartnerOS at a **pinned commit**, migrate PostgreSQL to head, configure portal-bridge env flags safely, verify health, and roll back without accidental float deploys.

This document complements:

- `docs/phase3/d8_staging_operator_runbook.md` — evidence and state machine
- `docs/phase3/d8_portal_staging_contract_runbook.md` — portal bridge contract
- `docs/records/migration_provenance_audit_20260726.md` — migration guard rationale

## Hard Boundaries

- **No secrets in repo artifacts** — tokens, `.env`, database URLs, raw response bodies, customer files.
- **No nginx / UnionGPT / `service.intelli-opus.com` changes from this repository.**
- **No real staging network calls from CI or doc-only runs** — use local dry-run commands below.
- **No automatic email, webhook, SMS, carrier API, customer/supplier notification, or order/shipment/payment mutation.**
- **Do not write `STAGING_VALIDATED`** until real strict staging evidence exists per operator runbook.
- Current stage boundary: `READY_FOR_STAGING_HANDOFF` / `WAITING_FOR_REAL_STAGING_EVIDENCE` — local rehearsal does not satisfy strict evidence.

---

## 1. Release Pin and Checkout (prevent float deploy)

### 1.1 Pin definition

| Field | Value |
|---|---|
| Deploy SHA (full) | `04ebcb56883eff81cc8c3b953dfef4c3b47ccd72` |
| Deploy SHA (short) | `04ebcb5` |
| Commit message | `docs(rc): point audit to preflight blocker record path` |
| Alembic head revision | `0025_pricing_assumptions` |
| Prior known-good SHA | `ae9a4b6` (`chore(rc): migration provenance audit…`) |
| Legacy baseline (empty-install unsafe) | `master@c2c2064` — **do not use for empty DB install** |

### 1.2 Exact checkout (operator machine)

```powershell
# From a clean deploy workspace — NOT a floating branch checkout
git fetch origin
git cat-file -t 04ebcb56883eff81cc8c3b953dfef4c3b47ccd72   # must print: commit
git checkout --detach 04ebcb56883eff81cc8c3b953dfef4c3b47ccd72
git rev-parse HEAD                                          # must equal full pin above
git log -1 --oneline                                        # must show 04ebcb5
```

**Reject deploy if:**

- `git rev-parse HEAD` ≠ `04ebcb56883eff81cc8c3b953dfef4c3b47ccd72`
- Operator only checked out `feat/e2e-supplier-convergence` without pinning
- Working tree has uncommitted changes affecting `backend/` or `frontend/`

### 1.3 Deploy SHA verification design

Record the pin at three independent points so a float deploy cannot slip through:

| Checkpoint | Command / action | Pass criterion |
|---|---|---|
| **A — Source tree** | `git rev-parse HEAD` before build | Exact full SHA match |
| **B — Build args** | Pass `DEPLOYED_COMMIT_SHA=04ebcb5` into backend image build (CI or manual `--build-arg`) | Image label / env matches pin |
| **C — Runtime health** | `GET /health` → JSON `version` field | Matches application version baked at build (see §5) |
| **D — Evidence metadata** | `deployed_commit_sha` in strict staging evidence JSON | Short or full SHA equals pin |
| **E — Alembic** | `alembic current` inside backend container | `0025_pricing_assumptions (head)` |

Optional CI gate (recommended):

```powershell
$expected = "04ebcb56883eff81cc8c3b953dfef4c3b47ccd72"
$actual = git rev-parse HEAD
if ($actual -ne $expected) { throw "REFUSING DEPLOY: HEAD=$actual expected=$expected" }
```

Do **not** deploy `git pull` / branch tip without re-running this gate.

---

## 2. Pre-deploy Database Backup

Run **before** stopping the current backend or running migrations.

### 2.1 Identify database connection

From operator secret store (never commit):

- Staging `DATABASE_URL` — PostgreSQL, same major version as target (`pg16` per local-server compose reference).

Local rehearsal reference (`docker-compose.local-server.yml`):

- Host port `5435` → container `5432`
- Database / user: `partneros`

### 2.2 Backup command

Replace `<staging-host>`, `<staging-port>`, `<backup-dir>` with operator values.

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = "<backup-dir>/partneros_pre_04ebcb5_$ts.sql.gz"

# Requires pg_dump 16.x client; use Docker if host lacks matching client:
docker run --rm `
  -e PGPASSWORD="<from-secret-store>" `
  postgres:16-alpine `
  pg_dump -h <staging-host> -p <staging-port> -U partneros -d partneros `
  --no-owner --no-acl -F c -f /tmp/backup.dump

# Or plain SQL gzip via local pg_dump:
pg_dump -h <staging-host> -p <staging-port> -U partneros -d partneros `
  --no-owner --no-acl | gzip > $backup
```

### 2.3 Backup verification

```powershell
# Custom format:
pg_restore --list $backup | Select-Object -First 5

# Or SQL gzip:
gzip -t $backup
```

Store backup path in operator log (redacted). **Do not** commit backup files or connection strings.

---

## 3. Alembic Pre-check and Upgrade to Head

Target head: **`0025_pricing_assumptions`**.

### 3.1 Pre-upgrade inspection

Inside backend container or venv with pinned source and `DATABASE_URL` set:

```powershell
cd backend
alembic current -v
alembic heads
alembic history --rev-range :0025_pricing_assumptions | Select-Object -Last 5
```

**Expected before upgrade:**

| State | `alembic current` | Action |
|---|---|---|
| Already at head | `0025_pricing_assumptions (head)` | Skip upgrade; proceed to deploy restart |
| Behind (typical) | `0024_win_loss_capture` or earlier | Run upgrade (§3.2) |
| Unknown / empty | `(empty)` on fresh DB | Run upgrade on empty DB **only with ≥24e234a migration guards** (included in `04ebcb5`) |

**Warning:** Empty-database install with pre-guard migrations (`≤c2c2064`) fails at `0023`. Pin `04ebcb5` specifically avoids this.

### 3.2 Upgrade command

```powershell
cd backend
alembic upgrade head
alembic current -v    # must show: 0025_pricing_assumptions (head)
```

Docker local-server reference — backend startup already runs `alembic upgrade head` before uvicorn (`docker-compose.local-server.yml`). For staging, prefer **explicit operator-run upgrade** before traffic switch so failures are visible.

### 3.3 Post-upgrade schema sanity (optional, non-destructive)

```powershell
cd backend
python -c "from app.core.config import get_settings; from app.core.database_lifecycle import get_migration_revisions; s=get_settings(); c,h,_=get_migration_revisions(s); print(c, h, c==h)"
# Expected: 0025_pricing_assumptions 0025_pricing_assumptions True
```

---

## 4. Environment Flags and CORS

Source of truth: `backend/app/core/config.py`, `docker-compose.local-server.yml`, `backend/.env.example`.

### 4.1 Required staging env vars

| Variable | Staging value | Default in code | Notes |
|---|---|---|---|
| `APP_RUNTIME_MODE` | `future_cloud` | `development` | Matches local-server compose |
| `DATABASE_URL` | `postgresql+psycopg://…` | empty | From secret store only |
| `SECRET_KEY` | long random string | dev default | Must not remain dev default on staging |
| `PORTAL_CUSTOMER_API_ENABLED` | `true` when portal bridge active | **`false`** | Set `false` for rollback / bridge-off |
| `PORTAL_CUSTOMER_API_TOKEN` | private token ≥24 chars | empty | Same value as portal consumer; never commit |
| `PORTAL_CUSTOMER_API_REQUIRE_TOKEN` | `true` | `true` | Keep enabled |
| `PORTAL_CUSTOMER_ALLOWED_ORIGINS` | `https://service.intelli-opus.com` | empty | Portal origin allowlist |
| `PUBLIC_BASE_URL` | staging backend HTTPS origin | empty | Used in manifests / links |
| `CUSTOMER_SITE_COMPAT_ENABLED` | **`false`** | **`false`** | Do not enable unless explicitly approved |
| `BACKEND_CORS_ORIGINS` | admin/staging UI origins (comma-separated) | `http://localhost:5173,http://127.0.0.1:5173` | Admin frontend origins |
| `UPLOAD_DIR` | `/app/uploads` | `./uploads` | Persist via volume |
| `LOCAL_STORAGE_PATH` | `/app/storage` | empty | Persist via volume |

### 4.2 CORS composition

Effective CORS list = `BACKEND_CORS_ORIGINS` **plus** `PORTAL_CUSTOMER_ALLOWED_ORIGINS` (deduplicated). See `Settings.cors_origins_list` in `backend/app/core/config.py`.

**Staging example (values illustrative — use real HTTPS origins from operator pack):**

```text
BACKEND_CORS_ORIGINS=https://<admin-staging-origin>
PORTAL_CUSTOMER_ALLOWED_ORIGINS=https://service.intelli-opus.com
```

**Local rehearsal example (docker-compose.local-server.yml):**

```text
BACKEND_CORS_ORIGINS=http://127.0.0.1:8080,http://localhost:8080
PORTAL_CUSTOMER_API_ENABLED=false
CUSTOMER_SITE_COMPAT_ENABLED=false
```

### 4.3 Portal bridge toggle semantics

| Mode | `PORTAL_CUSTOMER_API_ENABLED` | Portal bridge behavior |
|---|---|---|
| Bridge off (default / rollback) | `false` | Customer portal routes return 503 |
| Bridge on (staging UAT) | `true` + valid token + origins | Bridge APIs active; token required |

`CUSTOMER_SITE_COMPAT_ENABLED=false` keeps legacy compat routes unmounted (`backend/app/main.py`).

---

## 5. Build and Deploy Steps (pinned `04ebcb5`)

### 5.1 Local-server stack reference (rehearsal only)

From repo root at pinned SHA:

```powershell
git rev-parse HEAD   # verify 04ebcb5…

docker compose -f docker-compose.local-server.yml build --no-cache
docker compose -f docker-compose.local-server.yml up -d

docker compose -f docker-compose.local-server.yml ps
docker compose -f docker-compose.local-server.yml logs backend --tail 50
```

Images built:

| Service | Dockerfile | Notes |
|---|---|---|
| `backend` | `backend/Dockerfile` | Python 3.12; runs alembic + uvicorn :8000 |
| `frontend` | `frontend/Dockerfile.local-server` | Node 22 build → nginx 1.27; proxies `/api/` and `/health` |
| `db` | `pgvector/pgvector:pg16` | Port `5435:5432` |

**Staging production path:** infrastructure operator deploys equivalent images/env on staging hosts. This repo does **not** push to `service.intelli-opus.com`.

### 5.2 Staging deploy sequence (operator-controlled)

1. **Pin SHA** (§1.2) and record in deploy log.
2. **Backup DB** (§2).
3. **Build images** from pinned tree; tag with `04ebcb5` (not `latest` alone).
4. **Run alembic upgrade head** (§3) against staging DB.
5. **Inject env** from secret store (§4); keep `CUSTOMER_SITE_COMPAT_ENABLED=false` unless approved.
6. **Start backend** → wait for health (§5.3).
7. **Start frontend** (if applicable) → wait for health.
8. **Run dry-run / preflight** (§7) before strict evidence.
9. **Enable portal bridge** (`PORTAL_CUSTOMER_API_ENABLED=true`) only when credentials review complete.
10. Record `DEPLOYED_COMMIT: 04ebcb5` in redacted operator response intake.

### 5.3 Health check URLs and expected responses

#### Backend — `GET /health`

| Context | URL |
|---|---|
| Local docker compose | `http://127.0.0.1:8014/health` |
| Staging | `https://<partneros-staging-backend-origin>/health` |

**Expected HTTP 200 JSON (healthy staging):**

```json
{
  "status": "ok",
  "version": "<app-version-string>",
  "runtime_mode": "future_cloud",
  "bootstrap_status": "ready",
  "database_status": "ready",
  "database_lifecycle_phase": "ready",
  "alembic_current_revision": "0025_pricing_assumptions",
  "alembic_head_revision": "0025_pricing_assumptions",
  "migration_pending": false
}
```

**Acceptable degraded cases (investigate before portal UAT):**

- `status`: `degraded` — optional deps missing (e.g. Redis not configured)
- `migration_pending`: `true` — run `alembic upgrade head`
- `database_status`: `not_configured` — `DATABASE_URL` missing/wrong

**Failure — do not promote:**

- HTTP non-200
- `status`: `error`
- `alembic_current_revision` ≠ `0025_pricing_assumptions` when at head

PowerShell probe (local rehearsal):

```powershell
Invoke-RestMethod http://127.0.0.1:8014/health | ConvertTo-Json -Depth 5
```

#### Backend — `GET /api/v1/system/readiness`

Admin-authenticated or as documented for staging operator tooling.

**Expected when healthy:**

- `ok`: `true`
- `database.ready`: `true`
- `database.at_head`: `true`
- `database.current_revision`: `0025_pricing_assumptions`
- Warnings may include Redis/worker not configured (non-blocking for MVP)

#### Portal bridge — `GET /api/v1/portal/customer/readiness`

Requires admin auth (`PERM_PORTAL_READINESS`). Returns envelope with:

- `enabled`: matches `PORTAL_CUSTOMER_API_ENABLED`
- `require_token`: `true`
- `token_configured`: `true` when bridge on
- `allowed_origins_configured`: `true` when portal origin set
- `cors_origins`: list includes portal origin
- `safety.token_exposed`: `false`

When `PORTAL_CUSTOMER_API_ENABLED=false`, customer bridge routes return **503** (not a health-check substitute).

#### Frontend — nginx health (local-server)

| URL | Expected |
|---|---|
| `http://127.0.0.1:8080/health` | HTTP 200 — proxied backend health JSON |
| `http://127.0.0.1:8080/` | HTTP 200 — customer site shell |

Docker healthchecks (from compose / Dockerfile):

- Backend container: Python urllib to `http://127.0.0.1:8000/health`
- Frontend container: `wget -qO- http://127.0.0.1/health`

#### Database

```powershell
docker compose -f docker-compose.local-server.yml exec db pg_isready -U partneros -d partneros
# Expected: accepting connections
```

---

## 6. Rollback Procedure

### 6.1 When to rollback

- Health check fails after deploy
- Alembic upgrade fails or schema mismatch detected
- Portal bridge exposes forbidden fields or auth failure
- Operator marks preflight `INPUTS_UNSAFE` or evidence `FAIL`

### 6.2 Application rollback

1. **Stop promotion** — do not update evidence to `STAGING_VALIDATED`.
2. **Disable portal bridge immediately:**
   - Set `PORTAL_CUSTOMER_API_ENABLED=false`, **or**
   - Invalidate / rotate `PORTAL_CUSTOMER_API_TOKEN` (update consumer privately).
3. **Redeploy prior image** pinned to rollback SHA:

| Rollback target | SHA | When to use |
|---|---|---|
| Prior RC guard | `ae9a4b6` | Default rollback from `04ebcb5` |
| Feature RC | `244d133` | If chore commits suspect; portal hardening still present |
| Legacy | `master@c2c2064` | Emergency only; empty-install migrations unsafe |

```powershell
git checkout --detach ae9a4b6
git rev-parse HEAD   # verify ae9a4b6…
# Rebuild / redeploy images from this SHA; tag ae9a4b6
```

4. **Verify health** at rollback SHA — `GET /health` → `status: ok`, DB reachable.
5. **Confirm portal consumer** no longer calls bad backend (operator-side on `service.intelli-opus.com` — not from this repo).

### 6.3 Database restore

Use when migration left schema in bad state or data corruption observed.

```powershell
# 1. Stop backend traffic / scale backend to 0

# 2. Restore from pre-deploy backup (§2)
pg_restore -h <staging-host> -p <staging-port> -U partneros -d partneros `
  --clean --if-exists --no-owner --no-acl `
  <backup-dir>/partneros_pre_04ebcb5_YYYYMMDD_HHMMSS.dump

# 3. Verify alembic version matches backup epoch
cd backend
alembic current -v

# 4. Only if rollback app requires down-migration AND ops approved:
# alembic downgrade <revision>   # prefer restore over downgrade when possible
```

**Rules:**

- **Do not manually edit `alembic_version`** unless DBA procedure explicitly requires it.
- Prefer **restore pre-deploy backup** over partial downgrade.
- After restore + app rollback, rerun health checks (§5.3).

### 6.4 Post-rollback verification

```powershell
cd backend
python -m pytest tests/test_portal_staging_security_contract.py tests/test_release_candidate_contracts.py -q
python scripts/d8_staging_input_preflight_check.py
python scripts/project_execution_status.py
```

---

## 7. Dry-run / Preflight Commands (no real staging)

Run from pinned source on operator workstation. **Do not** pass real staging tokens into committed logs.

### 7.1 Local documentation and pack gates

```powershell
cd backend
python scripts/project_execution_status.py
python scripts/project_execution_chain_gate_check.py
python scripts/staging_evidence_boundary_check.py
python scripts/d8_staging_execution_pack_check.py
python scripts/d8_staging_operator_runbook_check.py
python scripts/d8_0_staging_build_readiness_check.py
python scripts/e2e_supplier_convergence_check.py
python scripts/release_candidate_check.py
```

### 7.2 Input preflight (secrets stay local)

Without real values — expect `WAITING_FOR_PRIVATE_VALUES`:

```powershell
cd backend
Remove-Item Env:BACKEND_BASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:SERVICE_PORTAL_PARTNEROS_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:SERVICE_PORTAL_ORIGIN -ErrorAction SilentlyContinue
python scripts/d8_staging_input_preflight_check.py
# Expected: Input State: WAITING_FOR_PRIVATE_VALUES
```

Local HTTP rehearsal (explicit opt-in only):

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
$env:SERVICE_PORTAL_PARTNEROS_TOKEN="<local-non-default-token-min-24-chars>"
$env:SERVICE_PORTAL_ORIGIN="https://service.intelli-opus.com"
$env:D8_STRICT_ALLOW_LOCAL_HTTP="true"
python scripts/d8_staging_input_preflight_check.py
# Expected: LOCAL_REHEARSAL_READY — not STAGING_VALIDATED
```

### 7.3 Local docker rehearsal stack

```powershell
# At pin 04ebcb5
docker compose -f docker-compose.local-server.yml up -d --build
Invoke-RestMethod http://127.0.0.1:8014/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8014"
python scripts/dev_runtime_doctor.py
python scripts/d8_2_runtime_hardening_check.py
```

### 7.4 Contract tests (no network)

```powershell
cd backend
python -m pytest tests/test_portal_staging_security_contract.py tests/test_portal_customer_bridge.py tests/test_release_candidate_contracts.py tests/test_customer_site_compat_gate.py -q
```

### 7.5 Strict evidence (only after real staging values)

Not a dry-run — requires HTTPS staging backend. See `docs/phase3/d8_staging_operator_runbook.md`. Local rehearsal output must stay **outside** `docs/records`.

---

## 8. Risk Points (operator summary)

| # | Risk | Mitigation |
|---|---|---|
| R1 | **Float deploy** — branch tip ≠ `04ebcb5` | §1 SHA gate at checkout, build, health, evidence |
| R2 | **Empty DB migration failure** on legacy revisions | Pin ≥`24e234a`; never empty-install with `c2c2064` migrations |
| R3 | **Skipping backup** before upgrade | §2 mandatory; store path in operator log |
| R4 | **`PORTAL_CUSTOMER_API_ENABLED=true` without token/origin** | Preflight + `/portal/customer/readiness`; default off until creds reviewed |
| R5 | **`CUSTOMER_SITE_COMPAT_ENABLED=true` by mistake** | Default `false`; verify in env injection checklist |
| R6 | **CORS misconfiguration** | Include `https://service.intelli-opus.com` in `PORTAL_CUSTOMER_ALLOWED_ORIGINS`; verify preflight |
| R7 | **Secret leakage in evidence** | Redaction policy; never commit `.env` or tokens |
| R8 | **False `STAGING_VALIDATED`** from local rehearsal | Rehearsal ≠ strict evidence; boundary check scripts |
| R9 | **Manual `alembic_version` edit** | Restore from backup instead |
| R10 | **nginx / portal repo changes** | Out of scope; coordinate separately with portal operator |

---

## 9. Orchestrator Handoff (中文摘要)

**交付物路径：** `docs/phase3/d8_staging_deployment_runbook_20260726.md`

**部署锚点：** 必须部署 commit `04ebcb5`（完整 SHA `04ebcb56883eff81cc8c3b953dfef4c3b47ccd72`），禁止直接跟踪浮动分支 tip。

**数据库：** 部署前 `pg_dump` 备份 → `alembic current` → `alembic upgrade head` 至 `0025_pricing_assumptions`。

**关键环境变量：** `PORTAL_CUSTOMER_API_ENABLED` Staging UAT 时置 `true`，默认/回滚时 `false`；`CUSTOMER_SITE_COMPAT_ENABLED` 保持默认 `false`；CORS 通过 `BACKEND_CORS_ORIGINS` + `PORTAL_CUSTOMER_ALLOWED_ORIGINS` 配置。

**健康检查：** `GET /health` 返回 `status: ok` 且 `alembic_current_revision` = `0025_pricing_assumptions`；本地栈另查 `8080/health` 与 `pg_isready`。

**回滚：** 应用回退至 `ae9a4b6`（或 `244d133`）+ 恢复部署前 DB 备份；立即设 `PORTAL_CUSTOMER_API_ENABLED=false` 或轮换 token。

**SHA 防漂移：** checkout / build-arg / health version / evidence 四处校验同一 SHA。

**预检（无真实 Staging）：** `d8_staging_input_preflight_check.py`、`d8_staging_execution_pack_check.py`、`release_candidate_check.py`、本地 docker compose 排练。

**主要风险：** 浮动部署、空库旧迁移失败、未备份升级、Portal 桥未配 token/CORS、 rehearsal 误标 STAGING_VALIDATED。

---

## Related Artifacts

- `docker-compose.local-server.yml` — local-server service topology
- `frontend/Dockerfile.local-server` — frontend build + nginx health
- `backend/Dockerfile` — backend image
- `backend/alembic/versions/0025_pricing_assumptions.py` — head migration
- `docs/records/migration_provenance_audit_20260726.md` — migration audit
- `docs/phase3/d8_staging_operator_runbook.md` — evidence workflow
- `docs/phase3/d8_portal_staging_contract_runbook.md` — portal contract + rollback checklist
