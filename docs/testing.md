# 测试指南（PartnerOS / intelliOffice）

## 文档定位（必读）

1. **以下**关于 PostgreSQL、Alembic、环境变量与 seed 的说明 **仅适用于开发者与自动化测试（CI）**。  
2. **它们不是** intelliOffice **最终用户**的安装或使用流程。  
3. 在 **产品模式（桌面应用）** 下，数据库初始化、迁移与引导数据将由应用 **内部自动化**（参见 [architecture_desktop_target.md](architecture_desktop_target.md)、[database_lifecycle.md](database_lifecycle.md)）。  
4. **pgAdmin**、psql、Docker 等 **仅为开发或排障工具**，不属于产品对用户的依赖。

---

## 单元与契约测试

在仓库根目录或 `backend` 目录：

```bash
cd backend
pytest -q
```

`backend/tests/test_health.py`、`test_runtime_bootstrap.py`、**`test_intelligence_score.py`**（D5：A 域可解释评分纯函数）、**`test_enrichment_unit.py`**（D5.2：enrichment URL/SSRF/建议互斥/mock 抓取路径，**不**打真实外网）与 **`test_database_lifecycle.py`** 覆盖 **D1/D4 契约**：`APP_RUNTIME_MODE`、`/health` 的 `status` / `runtime_mode` / `bootstrap_status` / `database_status` / **`database_lifecycle_phase`** / **`migration_pending`** / **`alembic_*_revision`** 等。其余默认测试套件**不强制** PostgreSQL（集成测试见下文）。

**D5.2**：集成环境跑 enrichment API 时建议临时设置 `PUBLIC_ENRICHMENT_ENABLED=true` 且仅在可控网络下验证；默认单测依赖 **mock**（`httpx`/`Runner` 层或纯函数），不要求外网。

**环境变量提示（D1）**：`APP_RUNTIME_MODE` 未设置时为 `development`；若在测试中需要切换模式，请在同一进程中以环境变量传入（注意 `get_settings()` 的缓存会沿用首次加载结果，针对该行为的测试请直接构造 `Settings(...)` 或按需 `get_settings.cache_clear()`）。

**本地数据库与 /health（开发）**：跑集成或手工联调前建议在 `backend` 下执行 `python scripts/check_database_config.py`。若未配置 `DATABASE_URL`，默认单元测试仍可通过；`/health` 在 **development** 下应呈现 `database_status: not_configured` 与 **`status` / `bootstrap_status`: degraded**，而不是误导性的「默认口令连接失败」。若已配置 URL 但认证失败，则为 `auth_failed` 且 **`status` / `bootstrap_status`: error**。产品模式（`desktop` / `demo` / `future_cloud`）下缺配置或认证失败均应保持 **error**。`migration_pending: true` 时请先 `alembic upgrade head` 再 expecting `status: ok`。

**人工验收主入口（A 域 + D5.2）**：见 **[manual_a_domain_test_plan.md](manual_a_domain_test_plan.md)**（含 `/health`、工作台、Enrichment、桌面 smoke 步骤及记录模板链接）。

**集成化后端（v1 系统接口）**：见 **[integrated_backend_standards.md](integrated_backend_standards.md)**；契约测试 [`test_api_v1_system.py`](../backend/tests/test_api_v1_system.py)（readiness / doctor / manifest envelope；legacy `/health` 字段不变）。

### D5.2.2 smoke test（内部 MVP）

**前提**：backend 已运行。默认 `BACKEND_BASE_URL=http://127.0.0.1:8000`；若使用 **8010**，请先设置：

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"
python scripts/check_backend_runtime.py
```

```powershell
cd backend
python scripts/smoke_demo_ready.py
```

只读检查：`/health`、readiness、manifest、demo 公司/联系人、三条 segment 调参、enrichment run、next action/touchpoint。缺数据时提示 seed/UAT，**默认不写库**（`--seed-demo` 未实现，请用 `python -m app.scripts.seed`）。

### D5.2.3 pilot workflow check

```powershell
cd backend
python scripts/pilot_workflow_check.py
```

验证 education segment、enrichment 审阅、touchpoint 等 pilot 台账能力。见 [records/d5_2_3_internal_pilot_workflow_20260523.md](records/d5_2_3_internal_pilot_workflow_20260523.md)。

### D5.2.4 lead intake & outreach drafts

```powershell
cd backend
python scripts/lead_import_preview.py ../docs/templates/lead_import_template.csv
python scripts/generate_outreach_draft.py --company "Ergo Sit Stand Workspace" --channel linkedin_connect --product-focus hosun_lifting
```

见 [records/d5_2_4_lead_intake_outreach_kit_20260523.md](records/d5_2_4_lead_intake_outreach_kit_20260523.md)。

### D5.2.5 manual outreach queue check

```powershell
cd backend
python scripts/outreach_queue_check.py
```

见 [records/d5_2_5_manual_outreach_queue_20260523.md](records/d5_2_5_manual_outreach_queue_20260523.md)。

### 前端组件测试

```powershell
cd frontend
npm run test -- --run
```

修改 Enrichment / System Status 相关组件后，至少跑对应 spec（如 `CompanyEnrichmentPanel.spec.ts`）。

### 手工 demo check 顺序（D5.2.2）

1. `python scripts/check_database_config.py`
2. `GET /health` → `status: ok`（development + DB ready）
3. 浏览器 `/login` → Dashboard **System Status** 卡片
4. `/companies` → Ergo 详情 → Enrichment Panel
5. `/lead-intelligence` → Ergo / Healthcare / Contract workflow
6. `python scripts/smoke_demo_ready.py` → **Result: PASS**

详细演示见 [records/demo_script_20260523.md](records/demo_script_20260523.md) · [records/d5_2_2_internal_mvp_20260523.md](records/d5_2_2_internal_mvp_20260523.md)。

---

## D2：桌面 shell（Tauri 2）与启动页

### 代码位置

- Tauri 工程：`frontend/src-tauri/`（`npm run tauri:dev` / `npm run tauri:build`）  
- 启动路由：**`/desktop-launch`**（公开路由，不要求登录）  
- Health 逻辑：`frontend/src/desktop/healthGate.ts`（与后端 D1 `/health` 字段语义一致，不自造冲突状态机）  
- 后端地址：`frontend/src/config/backendOrigin.ts`；Vite dev 下 `/api`、`/health` 经 proxy 转发（默认 `127.0.0.1:8000`，可设 `VITE_API_PROXY_TARGET=http://127.0.0.1:8010`）

### 不取代 development 工作流

- **仅浏览器**：照旧 `cd frontend && npm run dev`，默认进入站点根路径；业务路由与此前相同。  
- **仅桌面壳**：需本机安装 **Rust toolchain**（`rustc`、`cargo` 在 PATH 中）。若未安装，`tauri dev` 会失败——属环境阻塞，不是业务回退。  
- **验证 quartet**：先起后端（`uvicorn`，保证 `GET /health` 可用），再 `npm run tauri:dev`：  
  - **loading**：应用刚打开、首次请求进行中  
  - **ready**：`/health` 的 `status === "ok"`，自动跳转登录页进入现有 Vue 应用  
  - **degraded**：`/health` 的 `status === "degraded"`（如 development 下数据库未就绪）；**不**当作 fully ready；仅 `runtime_mode === development` 时提供「仍要继续」  
  - **error**：无法连接、`/health` 非 2xx 或 JSON 不合 D1 契约、或 `status === "error"`；页面含 **retry** 与关键字段展示

### 前端单测（D2）

```bash
cd frontend
npm run test
```

覆盖 health payload 解析、`loading/ready/degraded/error` 映射与连接失败行为（`src/desktop/healthGate.spec.ts`），以及 **D5.2** Enrichment 审阅面板在 mock API 下的发起 run / 加载详情行为（`src/components/enrichment/CompanyEnrichmentPanel.spec.ts`）。

### D2 Verification Gate（真实桌面/Rust 环境验收）

在 **已安装 Rustup** 的机器上完成以下检查，可将 D2 标记为 **fully verified**（与仅代码落地相区别）。

**PowerShell 提示**：Windows PowerShell 5.x **不支持** Bash 式 `cmd1 && cmd2`；请用 **`;` 分隔**或分多行执行。安装 Rust 后若仍提示找不到 `cargo`，请 **新开终端**，或在当前会话预先执行：

```powershell
$env:Path = "$env:USERPROFILE\.cargo\bin;" + $env:Path
```

**工具链（示例，验收机实测）**

- `rustc --version` → `rustc 1.95.0`（随 rustup 默认 stable 略有浮动属正常）  
- `cargo --version` → `cargo 1.95.0`

**构建级**

- `cd frontend\src-tauri; cargo check` → 应 **成功**（首次拉 crate 较慢）  
- `cd frontend; npm run tauri:build` → 应 **成功**（会先 `npm run build`，再编 Rust；本仓库验收中已生成 `app.exe`，以及 **MSI / NSIS** 安装包，路径见 Tauri 输出中的 `src-tauri\target\release\bundle\`）  
- **`frontend/src-tauri/Cargo.lock`**：由 Cargo 生成，**应提交入库**，以便 CI/他机复现相同依赖解析。

**`npm run tauri:dev`**

- 应出现：`VITE … ready`、`Finished dev … target(s)`、`Running target\debug\app.exe`（首次 debug 编译约数十秒）。  
- 若 **未启动后端**，日志中可能出现 Vite `http proxy error: /health`（ECONNREFUSED）— 属预期；`/desktop-launch` 会走 **error** 态并显示重试。

**首屏与 `/desktop-launch`**

- `tauri.conf.json` 主窗口 `url` 为 **`/desktop-launch`**，即 Dev 下加载 `http://localhost:5173/desktop-launch`。

**与 D1 `/health` 一致的三态（人工 + 契约测试交叉验证）**

| 目标态 | 后端条件（示例） | `/health`（D1） | 启动页（DesktopLaunchPage + healthGate） |
|--------|------------------|-----------------|------------------------------------------|
| **ready** | 后端运行，`development` + DB `SELECT 1` 成功 | `status: ok` | 自动跳转 **login** |
| **degraded** | 后端运行，`development` + DB 不可用或未配置 | `status: degraded` | **degraded** 文案；仅 `runtime_mode === development` 时显示「仍要继续」 |
| **error** | 后端未运行（fetch 失败）；或 `desktop`/`demo`/`future_cloud` + DB 非 ready 等 | 连接失败 **或** `status: error` | **error** + 重试；展示已拿到的 `runtime_mode`、`database_status`、`errors`（若有） |

契约层面参见 `backend/tests/test_runtime_bootstrap.py`、`frontend/src/desktop/healthGate.spec.ts`。

## D3：Windows 后端 sidecar（PyInstaller + Tauri `externalBin`）

### 产物与命令

- **入口**：`backend/sidecar_entry.py`（将进程内 `APP_RUNTIME_MODE` **固定为 `desktop`**，再 `uvicorn.run("app.main:app", …)`）。  
- **构建 spec**：`backend/intellioffice-backend.spec`；构建依赖见 `backend/requirements-sidecar-build.txt`（建议在 **干净 venv** 中安装后端 `requirements.txt` 与 PyInstaller，避免 conda 把巨大可选栈扫进 analysis）。  
- **复制到 Tauri**：`cd frontend && npm run sidecar:prepare`（调用 `scripts/prepare-sidecar.mjs`：每次使用唯一 `--distpath` / `--workpath`，避免 Windows 下覆盖已锁定的旧 `dist\intellioffice-backend.exe`）。产物：`frontend/src-tauri/binaries/intellioffice-backend-<rustc-host-triple>.exe`（**不提交**；见 `src-tauri/.gitignore`）。  
- **正式打包**：`tauri.conf.json` 的 `beforeBuildCommand` 含 `npm run sidecar:prepare`，故 `npm run tauri:build` 前会先冻结后端再编 Rust。  
- **首次在本机跑 `cargo check` / `tauri dev` 前**：至少执行一次 `npm run sidecar:prepare`，否则 `externalBin` 资源路径缺失会导致构建失败。

### 端口与分流（显式环境变量）

- **托管 sidecar 监听**：默认 **`127.0.0.1:17888`**（与 Vite dev 代理的 **8000** 错开）。统一由环境变量 **`INTELLIOFFICE_BACKEND_PORT`**（及子进程 **`PORT`**）控制；D3 **不**做自动换端口。  
- **路径 A（开发）**：设 **`INTELLIOFFICE_EXTERNAL_BACKEND=1`** 或不设 `INTELLIOFFICE_MANAGE_SIDECAR` 且在 **debug** 构建下 → 壳 **不**派生 sidecar；`/health` 经 Vite 代理到本机 **`8000`**（手动 `uvicorn`）。  
- **路径 B（产品链）**：**release** 构建默认 **`should_manage_sidecar=true`**（除非 `INTELLIOFFICE_EXTERNAL_BACKEND=1`）。**debug** 下若要验证 sidecar：设 **`INTELLIOFFICE_MANAGE_SIDECAR=1`**，并先 `npm run sidecar:prepare`。  
- 可选：`INTELLIOFFICE_DEV_BACKEND_ORIGIN` — 非托管时覆盖前端认为的 API/health 基址（见 `desktop_runtime.rs`）。

### 单测与契约

- `backend/tests/test_sidecar_entry.py`：sidecar 入口与 uvicorn 参数（mock `app.main`）。  
- `backend/tests/test_runtime_bootstrap.py`：`desktop` + 空 `DATABASE_URL` 时 `/health` 语义仍为 **error**（不降级为 development）。  
- `frontend/src/config/backendOrigin.spec.ts`：`get_desktop_config` 与回退行为；`healthGate.spec.ts` 仍校验四态。

### 构建级验收（Windows）

```powershell
cd backend
pytest -q

cd ..\frontend
npm run test
npm run build
npm run tauri:build
```

`npm run tauri:build` 会再次执行 PyInstaller（耗时数分钟属正常）；日常仅改 Rust/前端时可先用已存在的 `binaries\*.exe` 跑 `cargo check`。

## D4：Database Lifecycle Manager（PostgreSQL + Alembic）

### 实现要点（仓库事实）

- **唯一入口**：`backend/app/core/database_lifecycle.py`（`run_desktop_lifecycle`、`inspect_lifecycle_dev`、`PRODUCT_AUTO_MIGRATE_MODES`）。  
- **自动迁移范围**：`APP_RUNTIME_MODE` 为 **`desktop` / `demo` / `future_cloud`** 时，应用启动在后台线程中执行 DLM：**连接检查 → Alembic 版本对比 → 需要时 `alembic upgrade head`**。 **`development` 不自动迁移**（仍用手动 `alembic upgrade head`）；若 schema 落后，`/health` 为 **degraded** + `database_lifecycle_phase: initializing` + `migration_pending: true`。  
- **不落地的范围（本阶段）**：不捆绑 `initdb`、不随安装包分发 PostgreSQL 二进制、不做 Windows 服务托管 — 见 [database_lifecycle.md](database_lifecycle.md)。  
- **最终桌面 DB 载体**（继续 PostgreSQL / SQLite / 双路径）为 **开放架构决策**，非 D4 代码隐式结论；见 [open_questions_desktop.md](open_questions_desktop.md)。  
- **/health 扩展字段**：`database_lifecycle_phase`（`not_configured` \| `checking` \| `initializing` \| `migrating` \| `ready` \| `error`）、`migration_pending`、`alembic_current_revision`、`alembic_head_revision`、可选 `database_lifecycle_detail`。  
- **单测**：`backend/tests/test_database_lifecycle.py`（mock Alembic）；前端在 **`checking`/`initializing`/`migrating`** 且产品运行态下保持启动页 **loading** 并展示阶段文案（`healthGate.ts` / `DesktopLaunchPage.vue`）。

### 手工冒烟（可选）

在有可达 Postgres 且 `DATABASE_URL` 正确、`APP_RUNTIME_MODE=desktop` 的 sidecar 或本机 `uvicorn` 上：首次启动应能将库迁移至 head；`/health` 在迁移过程中可出现 `database_lifecycle_phase: migrating`。

## 完整业务流集成测试（PostgreSQL）

文件：`backend/tests/test_business_flow_integration.py`。

### 为何会被跳过？

若未设置环境变量 `PARTNEROS_TEST_DATABASE_URL`，该文件中的测试会 **skip**（避免误连你的开发库）。

### 安全规则

若 **已设置** `PARTNEROS_TEST_DATABASE_URL`，启动 pytest 时会检查：数据库名（URL 路径中的库名）**必须**包含子串 `test` 或 `testing`（大小写不敏感），例如：

- `partneros_test` ✓  
- `intellioffice_partneros_testing` ✓  
- `myapp` ✗（将拒绝并退出整个 pytest，防止误连生产或非测试库）

### 1. 创建测试库

在本机 PostgreSQL 上（示例库名）：

```bash
createdb partneros_test
```

若使用 Docker Compose 中的 Postgres，可在容器内执行 `createdb`，或使用 GUI / `psql` 创建同名数据库。

### 2. 设置环境变量

**Windows (PowerShell)：**

```powershell
$env:PARTNEROS_TEST_DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/partneros_test"
```

**Linux / macOS：**

```bash
export PARTNEROS_TEST_DATABASE_URL="postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/partneros_test"
```

将 `USER`、`PASSWORD`、`主机`、`端口` 换成你的实例。

### 3. 对测试库执行 Alembic 迁移（推荐）

集成测试在模块级 fixture 中也会 `create_all`，为与生产结构一致，建议在首次跑集成测试前对**同一 URL** 执行迁移：

```bash
cd backend
# 临时覆盖 DATABASE_URL，仅用于本次命令
$env:DATABASE_URL = $env:PARTNEROS_TEST_DATABASE_URL   # PowerShell
alembic upgrade head
```

（Bash 可用 `DATABASE_URL="$PARTNEROS_TEST_DATABASE_URL" alembic upgrade head`。）

### 4. 仅跑集成测试

```bash
cd backend
pytest tests/test_business_flow_integration.py -q
```

### 5. 清理测试库

集成测试会在每个模块开始时 **drop_all 再 create_all**，同一次 pytest 进程内数据会被重建。若需彻底清空：

- 删掉并重建数据库；或  
- 对测试库执行 `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`（谨慎，仅用于专用测试库）。

**不要**对开发库或生产库设置 `PARTNEROS_TEST_DATABASE_URL`。

### 6. 不配置集成库时

此时 `pytest -q` 中集成测试会显示 **skipped**，原因：`PARTNEROS_TEST_DATABASE_URL` 未设置（README 中亦说明）。属预期行为。

## P6.5 实环境验证要点

### 驱动与 URL

后端 `requirements.txt` 使用 **psycopg 3**（`psycopg[binary]`），请使用：

`postgresql+psycopg://USER:PASSWORD@HOST:5432/partneros_test`

不要使用 `postgresql+psycopg2://`，除非你另行安装并配置 `psycopg2`。

### 使用仓库自带 Docker Postgres 时

1. 启动 Docker Desktop 后：`docker compose up -d db`（仓库根目录）。  
2. 创建测试库（一次性）：

```bash
docker compose exec db psql -U partneros -d partneros -c "CREATE DATABASE partneros_test;"
```

3. 测试库 URL 示例：

`postgresql+psycopg://partneros:partneros@127.0.0.1:5432/partneros_test`

4. 对**测试库**跑迁移（PowerShell）：

```powershell
cd backend
$env:PARTNEROS_TEST_DATABASE_URL = "postgresql+psycopg://partneros:partneros@127.0.0.1:5432/partneros_test"
$env:DATABASE_URL = $env:PARTNEROS_TEST_DATABASE_URL
alembic upgrade head
pytest tests/test_business_flow_integration.py -q
```

5. **Demo seed**（应跑在**开发库**，勿用 `PARTNEROS_TEST_DATABASE_URL`）：

```powershell
$env:DATABASE_URL = "postgresql+psycopg://partneros:partneros@127.0.0.1:5432/partneros"
python -m app.scripts.seed
python -m app.scripts.seed_business_flow
Remove-Item Env:PARTNEROS_TEST_DATABASE_URL -ErrorAction SilentlyContinue  # 避免误用测试 URL
```

集成测试会 `drop_all` / `create_all` 测试库结构；开发库与测试库**必须分离**。
