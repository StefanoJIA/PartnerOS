# Runtime modes（运行模式）

Backend / 桌面壳在实现阶段应通过 **Runtime Mode Manager** 读取单一配置源（环境变量、配置文件或注册表），统一分支行为。以下为 **目标约定**（D1+ 落地）。

## 1. 模式列表

| 模式 | 用途 |
|------|------|
| **development** | 开发者本机：可连接任意 `DATABASE_URL`、手动 Alembic/seed、Vite dev server、详细日志、可挂载热重载 |
| **desktop** | **默认产品模式**：本地托管或应用引导的 Postgres、固定应用数据目录、自动迁移与 bootstrap、无最终用户 CLI |
| **demo** | 演示/展会：可选预置 demo 数据、受限写入或只读开关、缩短 AI 超时等（具体策略 D4+ 细化） |
| **future_cloud** | 预留：未来托管 API / 同步账号 / 多设备（不阻塞当前桌面路线） |

## 2. 行为矩阵（目标）

| 行为 | development | desktop | demo | future_cloud |
|------|-------------|---------|------|--------------|
| `DATABASE_URL` 来源 | `.env` / 环境变量 | 应用生成或内嵌默认 | 同 desktop 或隔离目录 | 远程配置 |
| 文件存储根目录 | 可配置 | `%AppData%` 或安装目录下受控路径 | 同 desktop 或临时目录 | TBD |
| 手动 Alembic | 允许 | **不需要用户执行** | **不需要** | TBD |
| 手动 `seed` / `seed_business_flow` | 允许 | **由 bootstrap 或「演示模式」触发** | 可自动注入 demo | TBD |
| 外部 Postgres（非托管） | 允许 | 可选高级/排障路径，**非主流程** | 一般不允许 | 不适用 |
| 开发调试 API/日志 | 可开 | 默认关或脱敏 | 限制 | TBD |
| Vite / 源码映射 | 是 | 否（仅构建产物） | 否 | TBD |

## 3. 配置入口（设计意图）

- **后端（D1 已落地）**：环境变量 **`APP_RUNTIME_MODE`**，合法值仅为 `development` | `desktop` | `demo` | `future_cloud`；未设置时默认为 **`development`**。非法值在加载 **`Settings`** 时触发校验错误（应用不应静默退回默认模式）。  
- **桌面 sidecar（D3 已落地，Windows）**：由 Tauri 拉起 PyInstaller 产物时，**壳与子进程均将运行态设为 `desktop`**（Rust `spawn` 注入 + `sidecar_entry.py` 内强制赋值）；不得为该捷径把桌面错误语义改写成 `development`。  
- **`/health`（D4）**：除 `database_status` 外，响应中含 **`database_lifecycle_phase`**、**`migration_pending`**、**`alembic_current_revision` / `alembic_head_revision`**（及可选 **`database_lifecycle_detail`**），用于桌面启动页展示 **checking / initializing / migrating** 等阶段；产品运行态下迁移失败保持 **`error`**，不得降级为 development **degraded**。  
- **桌面安装版**：首次启动写入 `config.json` 或等价存储；模式默认为 `desktop`（由壳 / 引导层设置 `APP_RUNTIME_MODE` 或后续统一的运行时配置源）。  
- **演示模式**：可通过安装选项、命令行参数（**供实施人员**，非普通用户）或应用内隐藏开关启用 `demo`。

## 4. 相关文档

- [database_lifecycle.md](database_lifecycle.md)  
- [architecture_desktop_target.md](architecture_desktop_target.md)  
- [roadmap_desktop_transition.md](roadmap_desktop_transition.md)  
