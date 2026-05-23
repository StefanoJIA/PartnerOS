# Database lifecycle（数据库生命周期）

## 1. 目标

在 **产品模式（desktop）** 下，PostgreSQL + **pgvector** 仍是权威数据与向量层（不将全量栈替换为 SQLite）。差别在于：数据库从「用户自行安装的依赖」变为由 **Database Lifecycle Manager**（DLM）与应用协同 **托管或自动初始化** 的本地服务。

**pgAdmin、psql、Docker** 仅作为 **开发与排障工具**，不是最终用户流程的一部分。

## 2. DLM 职责（目标能力清单）

| 能力 | 说明 |
|------|------|
| 检查数据目录 / 集群状态 | 首次启动判断是否需要初始化 |
| 初始化数据库集群（如内嵌或捆绑的 Postgres） | 具体技术选型见 [packaging_strategy.md](packaging_strategy.md) 与 [open_questions_desktop.md](open_questions_desktop.md) |
| 启动 / 停止数据库进程 | 与桌面应用生命周期绑定（安装/退出策略 D3+ 定稿） |
| 创建业务库与用户 | 使用应用生成凭证，**不要求用户设 postgres 密码** |
| 执行扩展 | 至少 `vector`；与当前 Alembic 模型一致 |
| 运行迁移 | 等价于生产环境的 `alembic upgrade head`，由后端在 bootstrap 阶段调用 |
| 备份 / 恢复 | D6 产品化加强；接口先在架构上预留 |
| 健康检查 | 端口、连接、扩展存在性、迁移版本 |
| 故障诊断 | 日志路径、可导出诊断包；**可选**「修复数据库」向导（重建副本等，需谨慎） |

## 3. 开发期 vs 产品期（流程对比）

| 步骤 | 当前开发期（可接受） | 产品期（目标） |
|------|----------------------|----------------|
| 安装数据库 | 开发者安装 Postgres / Docker / 云实例 | **用户不单独安装**；由安装包或应用首次运行完成 |
| 建库建用户 | pgAdmin / psql / 脚本 | **DLM + Bootstrap** |
| 迁移 | 手动 `alembic upgrade head` | **自动**在启动链中执行 |
| 基础数据 | `python -m app.scripts.seed` | **Bootstrap** 创建管理员与角色；demo 数据由 **demo 模式** 或首次运行可选流程触发 |
| 排障 | 开发者查日志、连 pgAdmin | **诊断 UI + 日志导出**；高级用户可选暴露连接信息（D6） |

## 4. 与现有仓库的关系

- 今日 **`alembic/`** 与 **SQLAlchemy 模型** 继续作为 **唯一结构真相**；DLM 调用相同迁移，不平行维护第二套 DDL。
- 集成测试用 **`PARTNEROS_TEST_DATABASE_URL`** 等仍只属于 **development**；见 [testing.md](testing.md)。

## 5. 缺配置 vs 认证失败（development 与产品模式）

- **未设置 `DATABASE_URL`**（无有效连接串）：应用 **不**再使用内嵌默认用户/口令去尝试连接。`/health` 中 **`database_status`** 为 **`not_configured`**，`database_lifecycle_phase` 为 **`not_configured`**，`errors` 提示从 `backend/.env.example` 创建 `backend/.env` 或运行 `python scripts/init_local_env.py`。**development** 下顶层 **`status` / `bootstrap_status`** 多为 **degraded**。
- **已配置 `DATABASE_URL` 但认证失败**：**`database_status`** 为 **`auth_failed`**，错误信息会指向核对 **`backend/.env`** 中的用户与密码。**development** 下顶层 **`status` / `bootstrap_status`** 为 **error**（与「未配置」区分）。
- **数据库不存在** 等：**`database_status: database_missing`**（或连接不可达 **`unavailable`**），详见 `/health` 的 `errors`。
- **`desktop` / `demo` / `future_cloud`**：数据库未配置、认证失败或迁移失败时 **`/health` 保持 error**，语义不因 development 而放宽。
- **pgAdmin** 仍仅为可选开发工具，**不是**产品依赖。

## 6. D4 已落地（仓库事实：PostgreSQL + Alembic）

- **DLM 实现**：`backend/app/core/database_lifecycle.py`；**产品运行态**（`desktop` / `demo` / `future_cloud`，见 `PRODUCT_AUTO_MIGRATE_MODES`）在 **后台线程** 中执行连接检查、迁移比对、按需 **`alembic upgrade head`**；失败时 `/health` 为严格 **error** 语义，**不**伪装为 development **degraded**。  
- **development**：只读检视；**未配置 `DATABASE_URL` 时** `database_status: not_configured`（非误导性默认连接）；**已连接但 schema 落后** 时 `migration_pending: true`、`bootstrap_status: degraded`，需手动 `alembic upgrade head`。  
- **未包含**：Postgres 二进制捆绑、`initdb`、Windows 服务、备份恢复中心 — 仍为后续阶段。  
- **长期决策**：是否在部分 SKU 采用 **SQLite** 或 **PostgreSQL + SQLite 双路径** 须通过明确 ADR；**当前 D4 仅针对本仓库既有 PostgreSQL 栈**。

## 7. 相关文档

- [architecture_desktop_target.md](architecture_desktop_target.md)  
- [runtime_modes.md](runtime_modes.md)  
- [roadmap_desktop_transition.md](roadmap_desktop_transition.md)  
