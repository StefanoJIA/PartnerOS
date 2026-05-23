# 从 Web 开发仓到桌面产品（迁移说明）

## 1. 当前仓库定位

本仓库是 **intelliOffice PartnerOS** 的 **唯一主干代码库**：业务逻辑、数据模型、API、Vue UI 均在此演进。  
**交付形态**从「开发者分别启动前后端 + 外部 Postgres」迁移为「**桌面壳 + sidecar 后端 + 托管/引导 Postgres**」——**不**建议另起仓库复制业务代码。

## 2. 可保留的资产（不必重做）

- **FastAPI** 全栈路由、`services`、`schemas`、`models`  
- **Vue 3 + TypeScript + Element Plus** 全部页面与组件（构建产物嵌入桌面）  
- **Alembic** 迁移与 **PostgreSQL + pgvector** 模型  
- **AI / RAG**（`app/services/ai`、`knowledge` 路由与 `ai_kb`）  
- **CRM / Partner / Product / RFQ / Sample / Order** 工作台与比价、Dashboard、Tasks  
- **Status enums**、**Activity logs**、**Demo seed**、**pytest** 与集成测试骨架  
- **伙伴中立规则**（无不合理的 HOSUN 特权 hard-code）

## 3. 需要重构或新增的部分（按阶段）

| 类别 | 说明 |
|------|------|
| **启动与配置** | 引入 `INTELLIOFFICE_RUNTIME_MODE`（或等价）与集中配置；**Bootstrap** 编排迁移与初始账户 |
| **数据库** | **DLM** 抽象与实现；开发期可仍为外部 Postgres |
| **桌面壳** | 新建 Tauri/Electron 工程，引用 `frontend/dist` + 启动 `backend.exe` |
| **健康与诊断** | `/health` 与错误码约定，供 shell 显示「后端未就绪 / 数据库失败」等 |
| **打包管线** | CI 构建前端、后端 sidecar、壳、安装包（D3–D6） |

## 4. 不应重做的事

- **不重写** 核心业务表与已稳定 API 语义（除非桌面约束强制，如路径与安全边界）。  
- **不** 为桌面另起一套微服务拆分（除非规模证明必要）。  
- **不** 在 D4 完成前用 SQLite **替换** Postgres 全量能力（与 pgvector / 现有查询不兼容）。

## 5. 建议迁移步骤（概要）

1. **D0** — 文档与模式共识（本轮）。  
2. **D1** — 后端：runtime mode + bootstrap 设计 + 单命令/单进程验证开发链。  
3. **D2** — Shell MVP：嵌 UI + 拉起 sidecar + 登录 + Dashboard。  
4. **D3** — DLM 原型：空白 Windows 上无 pgAdmin 完成首启建库与迁移。  
5. **D4** — 主业务链全在桌面跑通；demo 模式注入数据。  
6. **D5–D6** — Lead Intelligence 深化与产品化（更新、备份、诊断）。

详见 [roadmap_desktop_transition.md](roadmap_desktop_transition.md)。

## 7. Phase D5 — 业务能力迁移审查与 A 域最小闭环（2026-05）

本节的意图是回答：**哪些 Web 资产进入桌面产品主线、哪些重构、哪些暂缓**，并记录 **A 域（Lead Intelligence）** 的第一条可用工作流，而不是把旧页面「整体搬家」。

### 7.1 目标 A：业务资产迁移审查（正式结论）

以下对照 **桌面产品愿景**（intelliOffice 平台品牌、伙伴平级、A 域优先、升降/人体工学市场信号）与 **当前仓库实现**，结论适用于「是否继续作为桌面主线」而非「代码存在即保留」。

#### （1）保留 — 直接进入桌面主线的模块

- **CRM 核心对象**：`Company`、`Contact`、`Lead`、`Interaction`、`Task` 及现有 REST 工作台路由；对象级 `Object*Panel`（笔记、标签、文件、互动、任务、AI、活动日志）。
- **交易主链（B/C/D 域雏形）**：RFQ、Quotation、Sample、Order 及关联 workspace；Dashboard、Tasks。
- **伙伴与产品目录**：`manufacturing_partners`、`products`、品类与能力字段；**排序与推荐须基于结构化能力信号，不得默认单一工厂为上级实体**。
- **情报与知识**：`market_intelligence`（含按公司关联）、`knowledge` + AI、AI outputs；提示词层已有 **伙伴中立** 约束（如 `SYSTEM_NO_HOSUN_BIAS`）。
- **基础设施（已完成阶段）**：`APP_RUNTIME_MODE`、DLM、`/health`、Tauri 壳、sidecar、`/desktop-launch`。

#### （2）最小重构后保留

- **Lead Intelligence（A 域）**：从「仅线索详情页字段展示」提升为 **`/lead-intelligence` 工作台** + `GET/POST /api/a-domain/leads/...`；评分与 **`market_fit_segments`**（升降信号、`general_office_furniture_only` 弱行业分层、OEM/ODM、医疗/教育/重载等）为 **可解释规则**，后续可换模型但契约保持。
- **市场情报列表**：支持 **`related_company_id`**，与 CRM 公司并排使用。
- **通用列表页**：Companies/Leads 等仍保留，但作为「数据入口」；**差异化叙事落在 A 域工作台与 segments**，而非改版所有表格。

#### （3）暂缓 — 不纳入 D5 交付、不阻塞桌面主线

- 见 [roadmap_desktop_transition.md](roadmap_desktop_transition.md) **暂缓** 列表：Field Visit 大型 detail workspace、Constant Contact/Campaign、正式报价 PDF、复杂采集、本地大模型训练、云同步、完整 RBAC 产品化、要求用户操作 pgAdmin/Docker CLI 的设计等。
- **自动发现网页 → 自动建 Company/Lead**：可在 A 域后续迭代实现，**不属于 D5 MVP 闭环阻塞项**。

#### （4）不应因「已开发」直接进入桌面产品的旧思路

- 以 **某一个制造伙伴名称** 为默认排序、默认报价方、或 UI 上的「主厂」叙事。
- 将 **报价/订单完备度** 伪装成 D5 首要价值（当前窗口期优先 **情报→评分→行动**）。
- 任何 **隐式绑定** 最终数据库形态（Postgres 以外选项仅记录在 `open_questions_desktop.md`）。

#### （5）旧 Web 资产与桌面愿景的主要差异

| 维度 | 旧 Web 习惯 | 桌面产品意图 |
|------|-------------|----------------|
| 入口 | 平铺模块菜单 | **A 域工作台**承载「情报→动作」闭环，壳 + `/desktop-launch` 承担就绪体验 |
| 价值叙事 | 功能清单 / CRM 全能 | **升降系统市场响应**、segments、与通用家具客户的区分 |
| 伙伴 | 易在话术/演示中突出单一工厂 | **平级 partner + 能力/品类匹配** |
| 运维 | 开发者跑命令与种子 | DLM + 产品内迁移与健康字段（D4 已闭合） |

#### （6）D5 之后的推荐推进顺序

1. **A 域深化**：更多结构化情报字段、跟进模板、与 Task 的自动化边界。  
2. **与 B/C/D 域深链**：高分线索一键创建 RFQ/样品、状态回写（仍不改为微服务拆分）。  
3. **D6 产品化**：安装更新、备份恢复、诊断包、权限与配置 UI。

**上述（1）–（6）为「目标 A」正式文档化表述**；与 §7.2、§7.3 及路线图 D5 验收项一并维护。

### 7.1bis 摘要表（与上表互补）

| 类别 | 处理策略 | 一句话 |
|------|----------|--------|
| **保留** | 桌面主线 | CRM + 交易链 + 伙伴/产品 + 情报/知识 + 已交付基础设施。 |
| **重构** | 最小演进 | A 域工作台 + `a-domain` API + 公司与市场情报联动 + segments。 |
| **暂缓** | 不阻塞 D5 | 路线图暂缓项 + 自动爬虫发现客户（后续）。 |
| **不宜直入** | 否定 | 单伙伴特权、把 D5 当成「搬家 Web」、用户侧 DB 手工运维。 |

### 7.2 目标 B：D5 已落地的最小闭环（实现锚点）

数据流：**Company → Contact → Intelligence / Tags（意向标签 + 关联市场情报计数）→ Lead Score（规则可解释）→ Interaction → Next Action**。

- 后端：`GET /api/a-domain/leads/{lead_id}/workflow`、`POST /api/a-domain/leads/{lead_id}/touchpoint`；评分逻辑 `app/services/a_domain/intelligence_score.py`（**升降/人体工学/重载** 等关键词加权；**场景标签** `market_fit_segments`：如 `lift_system_signal`、**`general_office_furniture_only`（D5.1：办公家具行业相关但暂无明确升降意向）**、`oem_odm_fit`、`medical_vertical`、`education_vertical`、`heavy_duty_fit`；**无**伙伴名称偏置）。
- 前端：`/lead-intelligence` 工作台、线索详情页快捷入口；`GET /api/market-intelligence?related_company_id=` 与工作台跳转联动。
- 验证：`backend/tests/test_intelligence_score.py`（纯函数）。

### 7.3 D5 之后的模块优先级（建议）

1. **A 域深化**：更丰富的情报来源字段、跟进模板与任务自动生成边界。  
2. **B/C/D 域衔接**：高分线索与 RFQ/样品/报价状态机联动（在现有对象上扩展，不另起孤岛服务）。  
3. **产品化与运维**：D6 打包、备份、诊断；数据库载体（Postgres 以外）仅在 `open_questions_desktop.md` 决策后动代码。

## 8. 相关文档

- [architecture_desktop_target.md](architecture_desktop_target.md)  
- [packaging_strategy.md](packaging_strategy.md)  
- [project_reorientation_summary.md](project_reorientation_summary.md)  
