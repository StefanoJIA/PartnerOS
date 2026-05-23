# Project reorientation summary（路线重定向总结）

## 1. 为何从 Web-first 调整为 Desktop-first

近期本机验证暴露 **根本矛盾**：若产品形态依赖用户理解 **PostgreSQL、pgAdmin、Docker、Alembic、连接串、环境变量与多终端启动**，则 **无法** 作为家具行业销售/运营团队的 **默认工作方式**。  

**intelliOffice** 的终局交付物应是：**Windows 安装包 + 双击桌面图标 + 登录即用**；复杂基础设施由 **应用内** Bootstrap、Database Lifecycle 与 sidecar 后端托管。

## 2. 本机验证中的教训（摘要）

- 默认文档 Quick start **过度像「开发者部署手册」**，易被误读为最终用户路径。  
- **pgAdmin / postgres 密码** 不是产品能力，却是当前链路上的 **单点摩擦**。  
- 伙伴中立与业务模块已有积累；**缺口在系统层**（壳、模式、DB 生命周期、打包），而非再堆横向业务。

## 3. 新验收标准（产品视角）

| 维度 | 标准 |
|------|------|
| 首次使用 | **无需**手工建库、迁移、seed（由应用或受控向导完成） |
| 日常打开 | **单入口**；不强制浏览器书签、不强制两条命令行 |
| 数据库 | 用户 **不** 看到 `DATABASE_URL`；**不** 要求安装 pgAdmin |
| 排障 | 提供 **可读错误** 与 **日志/诊断导出**（随 D4–D6 增强） |
| 合规 | 伙伴推荐 **平级**、基于结构化字段；**升降系统/人体工学** 市场信号纳入 A 域长期建设 |

## 4. 仓库审查摘要

| 方面 | 结论 |
|------|------|
| **可保留** | FastAPI + Vue 全栈、模型与迁移、AI/RAG、CRM/Partner/Product/RFQ/Sample/Order、比价、Dashboard、seed、enums、activity、测试 |
| **仍偏 Web/Dev** | 分启前后端、外部 `DATABASE_URL`、手跑 Alembic/seed、无 shell、无 runtime/bootstrap/DLM/packaging |
| **优先设计/实现（阶段见 roadmap）** | P0 文档 ✅ → P1 模式+bootstrap+sidecar → P2 托管 DB 原型 → P3 主链桌面化与情报 |

## 5. 旧路线 vs 新路线

| 维度 | 旧路线 | 新路线 |
|------|--------|--------|
| 产品形态 | 多进程 Web + 手工部署 | **Windows 桌面一体** |
| 数据库 | 用户/文档驱动安装与配置 | **应用托管或自动引导** |
| 工具可见性 | pgAdmin / Docker / CLI 常见 | **仅开发者**；用户不可见 |
| 扩展节奏 | 优先加业务模块 | **先 desktop foundation** 再加 A 域深化等 |
| 打包 | 后补 | **D2 起与壳同步演进** |

## 6. 当前明确暂停（勿与 D0–D1 并行开工产品化实现）

1. Field Visit **Detail workspace**（大功能）  
2. Constant Contact / **Campaign**  
3. 正式 **报价 PDF**  
4. **复杂网页采集**  
5. **本地大模型训练**  
6. **云同步**  
7. **完整 RBAC** 产品化  
8. 任何 **强制最终用户** 操作 **pgAdmin / 手工 PostgreSQL / Docker CLI** 的产品设计  

*调研与架构预留允许；不落地用户可见依赖。*

## 7. Cursor / 协作用「项目总描述」——中文

**intelliOffice PartnerOS** 是面向美国家具与人体工学支撑市场的、**Windows 优先的本地桌面商业操作系统**。当前仓库使用 Vue + FastAPI + PostgreSQL（pgvector）实现业务，**最终交付** 为可安装的桌面应用：由应用自动管理本地 **sidecar 后端**、**数据库生命周期**、**迁移与引导数据**，最终用户无需接触 pgAdmin、Docker、Alembic 或命令行。市场与客户情报（含 **adjustable desk / lifting / sit-stand** 等需求的识别）归属 **A 域**，须与 Leads、Companies、RFQ、平级 **manufacturing partners**（HOSUN、JOOBOO 及未来工厂均为平级行、**禁止厂牌优先**）、样品、订单、海运、AI 与知识库 **同一产品内** 贯通。**开发模式** 下仍可使用外部 Postgres、Docker、pgAdmin、手动 seed；**产品模式** 不得以上述为假设。**当前优先级**：完成 **D0 文档** 与 **D1 后端就绪能力**；在 **D4 桌面主链** 稳定前，**暂缓** Field Visit 详情、Campaign、报价 PDF、重采集、云同步等。

## 8. Project narrative — English (for README / prompts)

intelliOffice PartnerOS is a **Windows-first, local-first desktop business operating system** for the U.S. furniture and ergonomic workstation market (including **adjustable desk frames, lifting columns, sit-stand**, and related categories). This repository implements the product today using a **web-style development stack** (Vue 3, FastAPI, PostgreSQL with pgvector). The **final deliverable is not** a manually deployed web application: it will be a **packaged Windows desktop app** that orchestrates a **local FastAPI sidecar**, **database lifecycle**, **migrations**, and **bootstrap data**—without asking end users to install or administer PostgreSQL, Docker, or CLIs. **Lead intelligence** is part of the **market & customer intelligence domain** and must feed **Companies, Leads, RFQs, and peer-level manufacturing partners**—not a standalone silo. **HOSUN**, **JOOBOO / Chongqing Huiju**, and future factories are **equal peer rows** in `manufacturing_partners`; **no brand-name privilege** in ranking or AI. **Development mode** may use external Postgres, Docker, pgAdmin, and manual seeds; **product (desktop) mode** must not require them. **Current priority**: complete **D0 documentation** and **D1 desktop-ready backend** building blocks. **Deferred** until the desktop foundation is solid: Field Visit detail workspace, Constant Contact campaigns, formal quote PDF, heavy web scraping, local LLM training, cloud sync, and full enterprise RBAC.

## 9. 文档地图

| 文档 | 用途 |
|------|------|
| [product_vision.md](product_vision.md) | 愿景与六域 |
| [architecture_desktop_target.md](architecture_desktop_target.md) | 目标分层与系统模块 |
| [runtime_modes.md](runtime_modes.md) | development / desktop / demo / cloud |
| [database_lifecycle.md](database_lifecycle.md) | DLM 职责 |
| [packaging_strategy.md](packaging_strategy.md) | Tauri vs Electron、sidecar、安装包 |
| [migration_from_web_to_desktop.md](migration_from_web_to_desktop.md) | 保留与重构 |
| [roadmap_desktop_transition.md](roadmap_desktop_transition.md) | D0–D6 与验收 |
| [open_questions_desktop.md](open_questions_desktop.md) | 未决项 |
| [testing.md](testing.md) | **仅开发者/CI** 的数据库与测试步骤 |
| [dev_guide.md](dev_guide.md) | 开发环境实操 |
| [activity_actions.md](activity_actions.md) | Activity 词汇（不变） |

## 10. 是否进入 Phase D1

**建议：是**——在 D0 文档合并并团队短暂评审后，**立即启动 D1**（runtime mode、bootstrap 设计、单命令开发路径、`/health` 契约），避免继续堆积与桌面启动链无关的业务需求。

---

*本文档随阶段更新；重大决策可另建 ADR 并在此处链接。*
