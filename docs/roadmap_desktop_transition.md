# Desktop transition roadmap（桌面化路线）

## 总原则

- **最终产品** = Windows 桌面一体化应用；**当前 Web 联调** = 开发模式。  
- **先夯实桌面基础（D1–D4）**，再扩展 A 域情报深化与横向功能。  
- 伙伴 **平级**、**升降系统/人体工学** 市场焦点、Lead Intelligence **归属 A 域且不孤岛** —— 见 [product_vision.md](product_vision.md)。

## Phase D0 — Project reorientation（已完成）

**目标**：文档与愿景统一为 desktop-first；团队不再将「pgAdmin / 手工建库」视为产品假设。

**验收**：

- [ ] README 明确 Product vision vs Development mode  
- [ ] `docs/product_vision.md`、`architecture_desktop_target.md`、`runtime_modes.md`、`database_lifecycle.md`、`packaging_strategy.md`、`migration_from_web_to_desktop.md`、`open_questions_desktop.md`、`project_reorientation_summary.md` 可用且交叉链接  
- [ ] `docs/testing.md` 标明「仅开发者/CI」  

**依赖**：无。

---

## Phase D1 — Desktop-ready backend

**目标**：Runtime mode 抽象；App Bootstrap Manager 设计与最小实现；迁移与 seed 在 **开发模式** 下可 **单命令** 达成；健康检查可被未来 shell 消费；bootstrap seed 与 demo seed 职责分离设计。

**验收**：

- [ ] `development` / `desktop`（可选桩）模式在配置层可区分  
- [ ] 单一入口（CLI 或 API）可：**检测 DB → 迁移 → 确保管理员存在**（开发环境可打通）  
- [ ] `/health`（或等价）返回结构化就绪信息（字段在实现时冻结文档）  
- [ ] 不在此阶段要求最终用户手工 Alembic/seed  

**依赖**：D0。

---

## Phase D2 — Desktop shell MVP

**目标**：Tauri（或备选 Electron）壳：**加载构建后的前端**、**启动 FastAPI sidecar**、Splash、基础错误 UI；登录后可达 Dashboard。

**验收**：

- [ ] 双击应用进入 UI，**无需**用户手动 `uvicorn` / `npm run dev`  
- [ ] 后端异常时有可读错误（非空白页）  
- [ ] **开发模式** 仍可浏览器 + 手工后端（并行不破坏）  

**依赖**：D1（至少 health + 稳定本机 API 端口策略）。

---

## Phase D3 — Managed local database prototype

**目标**：Database Lifecycle Manager **原型**：在**无 pgAdmin** 的干净 Windows 上完成：首次运行 → 数据目录 → 初始化/连接数据库 → 扩展 → 迁移 → 健康。

**验收**：

- [ ] 普通用户无需输入 PostgreSQL 超级用户密码即可完成首启（或等价「一键修复」）  
- [ ] 应用能判定 DB 健康/不健康并记录日志  

**依赖**：D2（壳要能展示长时间启动与失败）。

---

## Phase D4 — Desktop beta（现有主链）

**目标**：Dashboard → Lead → RFQ → Sample → Order 全链路在 **桌面产品模式** 下可跑；demo 数据由 **demo 模式** 或首次向导触发，**非** 用户运行 `seed_business_flow` 脚本。

**验收**：

- [ ] 安装后即可完成当前主流程（与开发模式功能对等）  
- [ ] 无命令行依赖；无 pgAdmin 依赖  

**依赖**：D3。

---

## Phase D5 — Lead intelligence integration（进行中 → 最小闭环已落地）

**目标**：A 域能力（**升降系统 / 人体工学** 相关信号、可解释 Lead score、公司与市场情报关联）与 `Company` / `Lead` / `Interaction` **数据流贯通**；工作台形态区别于「仅 Web 列表页」。

**验收（D5 本仓库当前增量）**：

- [x] **Lead Intelligence 工作台**：`/lead-intelligence`，聚合公司与主联系人、市场情报计数、评分与建议，并支持记录 `Interaction` + 更新 `Lead.next_action`。  
- [x] **API**：`GET /api/a-domain/leads/{id}/workflow`、`POST /api/a-domain/leads/{id}/touchpoint`；`GET /api/market-intelligence?related_company_id=`。  
- [x] **市场匹配维度**：`market_fit_segments`（升降信号、**D5.1** `general_office_furniture_only` 弱分层、OEM/ODM、医疗/教育/重载等可解释标签）与关键词集对齐产品愿景。  
- [x] **迁移审查文档**：`migration_from_web_to_desktop.md` §7.1 覆盖保留 / 重构 / 暂缓 / 不宜直入 / 差异 / 推进顺序六项。  
- [ ] **推荐动作与 B/C/D 域对象一键关联**（可在后续用深链/快捷创建承接）。

**依赖**：D4。

---

## Phase D5.2 — Public-source enrichment MVP（已完成）

**目标**：在公司详情链路上增加 **官网等有限公开页 → 证据落库 → 规则建议 → 人工审阅 → 显式 apply** 的最小闭环，复用 D5 `infer_market_fit_segments` / `compute_intelligence_score`，**不**静默写正式评分或标签。

**验收**：

- [x] 三张表 `CompanyEnrichmentRun` / `CompanyEnrichmentSource` / `CompanyEnrichmentSuggestion` + Alembic 迁移。
- [x] 抓取：同源主机 + SSRF 防护、固定路径 MVP、超时与体积上限、hash 去重。
- [x] API：`POST/GET .../enrichment/runs`、run 详情、单条与批量 review、仅 `accepted` 的 `apply` + activity。
- [x] 前端：公司详情 **Enrichment** 面板；可启动 run、审阅来源与建议、接受/拒绝/批量、对已接受项写入画像。
- [x] 文档：[public_source_enrichment_mvp.md](public_source_enrichment_mvp.md)、[lead_intelligence_mvp.md](lead_intelligence_mvp.md)。
- [x] 单测：后端 `test_enrichment_unit.py`；前端 `CompanyEnrichmentPanel.spec.ts`（mock API）。
- [x] **可选关断**：`PUBLIC_ENRICHMENT_ENABLED=false` 禁止创建外网 run（CI/无网环境）。

**依赖**：D5（规则与 Lead Intelligence 语义对齐）。

---

## Phase D6 — Productization

**目标**：安装包定稿、自动更新、备份/恢复、诊断包、导入导出、崩溃日志、配置 UI、权限增强。

**验收**：

- [ ] 可分发、可恢复、可支撑客服诊断  

**依赖**：D4–D5 按需并行。

---

## 暂缓（explicit defer）

在 **D4 桌面 foundation 未完成前**，默认 **不启动** 以下产品级深度实现：

- Field Visit **Detail workspace**（大规模）  
- Constant Contact / **Campaign**  
- 正式 **报价 PDF**  
- **复杂网页采集**  
- **本地大模型训练**  
- **云同步**  
- **完整 RBAC** 产品化  
- **任何**要求最终用户手动操作 **pgAdmin / PostgreSQL 安装 / Docker CLI** 的设计  

（调查研究可在设计文档中准备，但不落地为面向用户的依赖。）

## 相关文档

- [project_reorientation_summary.md](project_reorientation_summary.md)  
- [open_questions_desktop.md](open_questions_desktop.md)  
