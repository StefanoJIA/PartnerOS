# intelliOffice PartnerOS — developer guide

> **产品愿景与桌面目标架构**：[product_vision.md](product_vision.md) · [architecture_desktop_target.md](architecture_desktop_target.md) · [project_reorientation_summary.md](project_reorientation_summary.md)  
> 本页描述 **开发模式** 下的本地环境；最终用户流程见 README「Product vision」。

## Product positioning

**intelliOffice** is the U.S.-facing brand and project platform for sales, RFQs, manufacturing partners, samples, and orders.

**HOSUN**, **JOOBOO**, and any future factory are **equal-level** rows in `manufacturing_partners`. The application must **not** hard-code, default, or prioritize any partner by trade name. Business rules use **status fields, capabilities, and structured data** — not supplier brand strings.

## Local setup

### Docker PostgreSQL（Windows 本地开发推荐）

若本机 **5432 已被 WSL/其他 Postgres 占用**，或不想安装 Windows 版 PostgreSQL，使用仓库自带 **pgvector** 容器（**主机端口 5435**）：

```powershell
cd "E:\WORKS\08 2026 Spring\IntelliOpus\IntelliOffice\Project Connecting"
docker compose up -d db
docker compose ps
```

`backend/.env` 中应使用（与 `.env.example` 一致）：

```env
DATABASE_URL=postgresql+psycopg://partneros:partneros@127.0.0.1:5435/partneros
```

然后在 `backend` 目录：

```powershell
python scripts/check_database_config.py
python -m alembic upgrade head
python -m app.scripts.seed
```

说明：

- **宿主机**跑 `uvicorn` → URL 用 `127.0.0.1:5435`。
- **compose 内** `backend` 服务 → 仍用 `db:5432`（容器网络，见 `docker-compose.yml`）。
- 数据卷 `partneros_pgdata` 持久化；`docker compose down` **不**删数据，除非加 `-v`。

#### 迁移到 Ubuntu 服务器

同一套 `docker-compose.yml` 在 Linux 上可直接使用（镜像 `pgvector/pgvector:pg16` 跨平台）。常见部署方式：

| 场景 | 做法 |
|------|------|
| **单机 compose 全栈** | 服务器安装 Docker → `git clone` → 配置 `.env` → `docker compose up -d`；若 5435 无冲突可保持映射，或改为仅内网暴露 `5432` |
| **共享 PostgreSQL（生产推荐）** | 服务器上 **不**起 compose 的 `db`，由运维提供 Postgres；仅设置 `DATABASE_URL=...@<host>:5432/partneros`；见 [integrated_backend_standards.md](integrated_backend_standards.md) |
| **数据迁移** | `pg_dump` / `pg_restore`，或复制命名卷；开发机 `docker compose exec db pg_dump -U partneros partneros > backup.sql` |

Ubuntu 上通常 **无 WSL 抢端口**，可将 `ports` 改回 `"5432:5432"` 或去掉对外端口、只允许 backend 容器访问 `db`。

1. PostgreSQL with **pgvector** (see repo `docker-compose.yml` or your own instance).
2. **Create `backend/.env`**（若不存在）：在 `backend` 目录执行 `python scripts/init_local_env.py`，会从 `.env.example` 复制模板且**不会覆盖**已有文件。随后运行 `python scripts/check_database_config.py`：会打印 **已脱敏**的 `DATABASE_URL`、连接结果、以及（连接成功时）Alembic current/head 与 `migration_pending`。  
   - 手动复制也可：`copy .env.example .env`（Windows）或 `cp .env.example .env`。  
   - 配置项：`DATABASE_URL`（必须）、`SECRET_KEY`（**或** 环境变量 / `.env` 中的 `JWT_SECRET`，二者等价）、可选 `OPENAI_*`、**D1** `APP_RUNTIME_MODE`、**D5.2** `PUBLIC_ENRICHMENT_ENABLED` / `ENRICHMENT_*`（见 `backend/app/core/config.py`）。
3. Backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   python scripts/check_database_config.py
   alembic upgrade head
   python -m app.scripts.seed
   python -m app.scripts.seed_business_flow
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Frontend:
   ```powershell
   # 从仓库根目录进入（不要在 backend 里再 cd frontend）
   cd frontend
   npm install
   npm run dev
   ```
   Vite 默认 **5173**；若端口被占用会自动尝试 **5174**（终端会打印 `Local: http://localhost:5174/`）。UAT 记录请写实际端口。

   Vite proxies `/api` and `/health` to the backend (see `frontend/vite.config.ts`).

### Windows 快速启动（D5.2.2）

在 **PowerShell** 中从仓库根目录操作（路径含空格请加引号）：

```powershell
# 1. 数据库（Docker，主机端口 5435）
docker compose up -d db

# 2. 后端 — 必须在 backend 目录，不要再 cd backend
cd backend
python scripts/check_database_config.py
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 前端 — 新开终端，从仓库根进入 frontend（不要在 backend 里 cd frontend）
cd frontend
npm run dev
```

- **Docker DB**：`127.0.0.1:5435` → 容器 `5432`（见 `docker-compose.yml`）
- **Backend**：`http://127.0.0.1:8000/health`（默认；见下方 **Changing backend port**）
- **Frontend**：终端打印的 `Local:` URL（5173 被占用时用 5174）
- **系统状态 UI**：登录后 Dashboard 卡片或 `/system-health`

## Changing backend port

1. **默认** backend 端口为 **8000**。
2. 若 **8000 被占用**，可使用备用端口 **8010**（不要强行 kill 未知进程）。
3. **启动 backend（8010 示例）**：

   ```powershell
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
   ```

4. **PowerShell — 对齐脚本与前端 proxy**：

   ```powershell
   $env:BACKEND_BASE_URL="http://127.0.0.1:8010"
   $env:VITE_API_PROXY_TARGET="http://127.0.0.1:8010"
   ```

5. **前端 `frontend/.env.local`**（已 gitignore，勿提交）：

   ```env
   VITE_API_PROXY_TARGET=http://127.0.0.1:8010
   ```

6. **检查**：

   ```powershell
   cd backend
   python scripts/check_backend_runtime.py
   python scripts/smoke_demo_ready.py
   ```

7. **不要**同时运行多个 backend 实例。
8. **不要**在 8000 与 8010 上各跑一个不同代码版本的 uvicorn，否则 segment / route 检查可能不一致。

**环境变量摘要**

| 变量 | 用途 | 默认 |
|------|------|------|
| `BACKEND_BASE_URL` | 后端 smoke / pilot / import 等脚本 | `http://127.0.0.1:8000` |
| `VITE_API_PROXY_TARGET` | Vite dev 将 `/api`、`/health` 代理到此地址 | `http://127.0.0.1:8000` |

   **Windows 常见启动错误**

   | 现象 | 处理 |
   |------|------|
   | `cd backend` 报 `backend\backend` 不存在 | 当前目录已在 `backend` 内，勿重复 `cd backend` |
   | `cd frontend` 报 `backend\frontend` 不存在 | 先 `cd` 到**仓库根目录**再 `cd frontend` |
   | uvicorn `[Errno 10048] 8000` | 8000 已被占用：用 `python scripts/check_backend_runtime.py` 验证是否已有 backend；或改用 **8010**（见 **Changing backend port**） |
   | npm 找不到 `backend\package.json` | 在 `frontend` 目录执行 `npm run dev`，不是 `backend` |
5. **Desktop shell (D2–D3 / Tauri 2, optional)** — install **Rust** (e.g. `winget install Rustlang.Rustup`). For **packaged sidecar** builds, you also need **Python** + **PyInstaller** (`pip install -r backend/requirements-sidecar-build.txt` in a venv that has the app deps). After Rust install, open a **new** terminal or ensure `%USERPROFILE%\.cargo\bin` is on `PATH` (PowerShell: `$env:Path = "$env:USERPROFILE\.cargo\bin;" + $env:Path`). **Do not** use `&&` in Windows PowerShell 5.x; use `;` or separate lines.  
   - **Path A (external backend, typical dev)** — start `uvicorn` on **:8000**, then from `frontend` e.g. `$env:INTELLIOFFICE_EXTERNAL_BACKEND = "1"; npm run tauri:dev`. Debug builds **do not** spawn sidecar by default; `/health` uses the Vite proxy.  
   - **Path B (managed sidecar smoke)** — `cd frontend; npm run sidecar:prepare` once (creates `src-tauri/binaries/intellioffice-backend-*.exe`), then e.g. `$env:INTELLIOFFICE_MANAGE_SIDECAR = "1"; npm run tauri:dev`. Sidecar listens on **`127.0.0.1:17888`** by default (`INTELLIOFFICE_BACKEND_PORT` overrides).  
   - **Release / `npm run tauri:build`** — `beforeBuildCommand` runs `sidecar:prepare` automatically; installer bundles the sidecar.  
   The window loads `/desktop-launch`, waits on **`GET /health`**, then enters the existing Vue app (`/login` when `status === ok`). This does **not** replace browser-first `npm run dev`. See **[testing.md](testing.md)** (`D2 Gate`, **D3 sidecar**).

Default login after `seed`: `admin@example.com` / `admin123`.

### Database connection troubleshooting（本地）

| 现象 | 含义 / 处理 |
|------|-------------|
| `backend/.env` 不存在 | 运行 `python scripts/init_local_env.py`，再编辑 `DATABASE_URL`。 |
| `/health` 中 `database_status: not_configured` | 未设置 `DATABASE_URL`（或为空）。按上表创建 `.env`。development 下整体多为 **degraded**。 |
| `database_status: auth_failed` | 已配置 URL，但 **密码或用户** 与 PostgreSQL 不一致；错误信息会提示用户名。用 **psql** 或迁移脚本核对角色密码（不必使用 pgAdmin）。 |
| `database_status: database_missing` | 服务器上不存在 URL 中的数据库名；`CREATE DATABASE ...`。 |
| `migration_pending: true` | 执行 `alembic upgrade head`；详见 [database_lifecycle.md](database_lifecycle.md)。 |

**API 根路径**：`GET /` 返回 `404 Not Found` 或 `{"detail":"Not Found"}` 为正常现象；健康检查请用 **`GET /health`**。

### Windows：不要在 PowerShell 里直接粘贴 SQL

PowerShell 会把 `--` 当成运算符，**不要**在终端里粘贴 `CREATE USER ...` 整段脚本。

任选其一：

1. **pgAdmin**：连接到本地服务器 → Query Tool → 打开并执行 `backend/scripts/init_partneros_db.sql`  
2. **psql**：`cd backend` 后执行  
   `psql -U postgres -h 127.0.0.1 -d postgres -f scripts/init_partneros_db.sql`  
   （将 `postgres` 换成你本机的超级用户；若需密码可先设置 `$env:PGPASSWORD`）  
3. ** helper**：`$env:PGPASSWORD = '你的postgres密码'; .\scripts\run_init_partneros_db.ps1`

建库成功后，确保 `backend/.env` 中 `DATABASE_URL` 与账号一致（可参考 `backend/.env.example`）。

## Migrations

```bash
cd backend
alembic upgrade head
```

若 `DATABASE_URL` 未配置或 PostgreSQL **拒绝口令** / **库不存在**，`alembic upgrade head` 会在 **连接前** 失败并提示运行 `python scripts/check_database_config.py`，而不再仅抛长段 SQLAlchemy 追溯（仍须先在本机把角色/密码/`partneros` 库对齐 `.env`）。

## Seed data

| Script | Purpose |
|--------|---------|
| `python -m app.scripts.seed` | Roles, admin user, small neutral partner/product stub data |
| `python -m app.scripts.seed_business_flow` | **Idempotent** Jefferson Group demo: CRM → RFQ (full quote fields) → sample → order → milestones → shipping → tasks → interactions → AI rows. Run: `python -m app.scripts.seed_business_flow` |

Re-running `seed_business_flow` refreshes demo links, quotations, sample/order markers, and stable tasks — it does **not** duplicate RFQ `RFQ-DEMO-JEFFERSON` / sample `SMP-DEMO-JEFFERSON` / order `ORD-DEMO-JEFFERSON`.

## Backend tests

```bash
cd backend
pytest
```

- **Manual A-domain / Lead Intelligence / Enrichment UAT**：录入规范、测试步骤与进入 D5.3 条件见 **[manual_a_domain_test_plan.md](manual_a_domain_test_plan.md)**（建议 DB 就绪后按文档执行）。
- **Integrated backend（双轨 API / v1）**：见 **[integrated_backend_standards.md](integrated_backend_standards.md)**；Phase 1 系统接口 `GET /api/v1/system/readiness|doctor`、`GET /api/v1/portal/manifest`。

- Default tests: mostly fixtures (see `tests/conftest.py`); **D4** `test_database_lifecycle.py` mocks Alembic (no live DB required for that file).
- **Integration**: see [testing.md](testing.md) for `PARTNEROS_TEST_DATABASE_URL`, test DB naming rule (`test` / `testing` in database name), Alembic, and cleanup.

## Frontend build

```bash
cd frontend
npm run build
```

## Business closed-loop smoke test (manual)

1. Log in as admin.
2. Open **Dashboard** — verify tasks, RFQ/sample/order hints and **推荐下一步** links navigate.
3. Open **Leads** → Jefferson demo lead (if seeded) or create a lead; open **RFQ** workspace; add item, candidates, quotations; open **比价**.
4. Convert **RFQ → Sample**; update shipping; record feedback; **Sample → Order**; generate milestones; complete one; mark one delayed; add shipping record.
5. Confirm **Activity** panels on RFQ / sample / order show actions listed in [activity_actions.md](activity_actions.md).

## AI (OpenAI-compatible)

- Configure API key / base URL in backend settings. See `README.md` for env names.
- **Without a key**, `/api/ai/*` routes return a short **placeholder** completion where implemented (check `app/services/ai/client.py`); the UI should show an error only on transport/HTTP failures, not on “empty model” if the backend substitutes text.

## Activity vocabulary

Canonical `action` strings: [activity_actions.md](activity_actions.md).
