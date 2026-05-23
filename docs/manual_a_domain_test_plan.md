# A 域人工测试与录入准备（主入口）

本文档是 **手工录入客户**、**验证 Lead Intelligence（D5）** 与 **Public-Source Enrichment（D5.2）** 的正式计划入口。实施前请确保本机数据库与 `backend/.env` 一致（见 [dev_guide.md](dev_guide.md)、`python scripts/check_database_config.py`）。

**可复制扩展表**（测试记录矩阵、客户录入矩阵）：[templates/manual_test_record_template.md](templates/manual_test_record_template.md)

---

## Part A. 当前全局阶段状态

| 阶段 | 状态 | 说明 |
|------|------|------|
| D0 Product Reorientation | **Completed（文档/叙事）** | 桌面优先、伙伴平级、升降主轴等已在愿景与迁移文档中落地。**Needs human UAT**：团队是否一致按此叙事对外与录入。 |
| D1 Runtime / Health | **Completed（代码 + 契约测试）** | `APP_RUNTIME_MODE`、`/health`、bootstrap / database 字段已落地；pytest 覆盖。**Needs human UAT**：多模式下人工看一眼 `/health` JSON 是否与预期一致。 |
| D2 Tauri Shell | **Completed（代码 + 构建链）** | `/desktop-launch`、四态、`tauri build` 仓库内已跑通。**Needs human UAT**：目标用户机器上首次安装与显示。 |
| D3 Sidecar | **Completed（代码 + 构建链）** | PyInstaller sidecar、`APP_RUNTIME_MODE=desktop` 固定、external vs managed 分流。**Needs human UAT**：仅 sidecar 路径下的首启与失败提示。 |
| D4 Database Lifecycle | **Completed（代码 + 契约测试）** | DLM、development 只读检查、产品态自动迁移。**Needs human UAT**：桌面产品态下整链首启（依赖未来 D3 托管 DB 定稿程度）。 |
| D5 Lead Intelligence MVP | **Completed（代码 + 自动化测试）** | 工作台、`/api/a-domain/leads/{id}/workflow`、`touchpoint`、评分与 segments 闭环。**Needs human UAT**：真实线索与公司数据下的业务判断是否与规则一致。 |
| D5.1 Segmentation Refinement | **Completed（代码 + 测试）** | `general_office_furniture_only` 与 `lift_system_signal` 互斥等。**Needs human UAT**：真实公司描述/标签下的误判率。 |
| D5.2 Public-Source Enrichment | **Completed（代码 + 自动化测试）** | 有限抓取、建议、审阅、apply；前后端测试与构建已通过。**Needs human UAT**：外网可达站点上的证据质量与 segment 一致性。 |
| D5.3 Interaction Memory | **Not started** | 不在本仓库路线图中单独立项；见 Part I 进入条件。 |
| D6 Productization | **Not started** | 安装定稿、诊断包等；见路线图。 |

**说明**：「Completed」表示 **仓库实现与自动化测试已落地**；**Needs human UAT** 表示 **尚未用真实客户与真实操作完成验收**，不夸大「已验收」。

---

## Part B. 当前不应该继续做的事情

以下事项 **暂缓**，与 [lead_intelligence_mvp.md](lead_intelligence_mvp.md)、[public_source_enrichment_mvp.md](public_source_enrichment_mvp.md)、[roadmap_desktop_transition.md](roadmap_desktop_transition.md) 一致：

| 暂缓项 | 原因 |
|--------|------|
| 不进入 **D6** 产品化主线 | 当前优先验证 A 域业务价值，而非安装/诊断包定稿。 |
| 不做 **完整 RFQ / quotation / sample / order** 扩展与深度自动化 | 避免分散资源；A 域未验证前扩展 B/C 域闭环性价比低。 |
| 不做 **全自动邮件 Campaign**、**LinkedIn 自动化** | 非 MVP；合规与产品叙事风险高。 |
| 不做 **大规模无边界爬虫**、**搜索引擎收录级采集** | D5.2 已限定同源固定路径；越界增加法律与 SSRF 面。 |
| 不做 **复杂 AI Agent** 自动决策 | 与 evidence-first、人审分层冲突。 |
| **不重构** sidecar / DLM 主链 | 稳定性优先；非本阶段目标。 |
| **不把 HOSUN（或任一厂牌）写成特殊上级 partner** | 产品原则：制造伙伴平级，能力驱动。 |
| **不新增未验证的业务域** | 避免在 A 域人工验收前堆叠新概念。 |

**原因归纳**：当前最重要的是验证 **A 域能否支撑真实筛客与跟进**；仅当人工测试通过后，再考虑 D5.3、B/C 域深链或自动化扩张。

---

## Part C. 客户信息录入规范

以下规范用于 **团队手工录入** 时的最低信息量与枚举约定。字段名尽量对齐 **当前 ORM**（[`backend/app/models/crm.py`](../backend/app/models/crm.py)）；若规范中有而 **库表无独立列** 的项，用 **约定格式写入 `notes` / `content` / `summary`**，并标注待 **D5.3** 再结构化。

### C.1 Company（公司）

| 规范项 | 映射到数据库 / 约定 |
|--------|---------------------|
| company name | `companies.company_name`（必填） |
| website | `companies.website`（Enrichment 必填；无则无法跑 D5.2） |
| city / state / country | `city` / `state` / `country` |
| business type | 使用 `company_type` 与/或 `industry`；推荐值见下表 **Business Type** |
| business summary | `business_description` |
| source | `source` |
| source URL | **无独立列**：写入 `notes` 首行，格式 `source_url: https://...` |
| initial notes | `notes` |

**Business Type（推荐枚举，写入 `company_type` 或 `industry`）**

`office_furniture_dealer` · `contract_furniture_dealer` · `installer` · `interior_design_firm` · `education_furniture_supplier` · `healthcare_furniture_supplier` · `importer` · `distributor` · `manufacturer` · `unknown`

（可与现有种子数据风格并存；录入时保持同一团队内口径一致。）

### C.2 Contact（联系人）

| 规范项 | 映射到数据库 / 约定 |
|--------|---------------------|
| name | `first_name` + `last_name`（拆分录入） |
| title | `title` |
| email / phone | `email` / `phone` |
| LinkedIn | `linkedin_url` |
| role type | `contact_type`（自由文本或团队枚举） |
| decision power | `decision_maker_level` |
| source | 若 UI 无字段则写入 `notes`：`source: ...` |
| do_not_contact | **无独立布尔列**：`notes` 首行 `do_not_contact: yes` 或 `status` 约定为 `do_not_contact`（团队二选一固定） |

### C.3 Interaction（互动）

**数据库当前列**：`interaction_type`、`channel`、`subject`、`content`、`summary`、`direction`、`interaction_date`、`next_action`、`next_action_due_date`（关联 `related_object_type/id` 为 lead 时由 API 写入）。

| 规范项 | 映射 |
|--------|------|
| interaction type | `interaction_type`（字符串） |
| channel | `channel` |
| occurred at | 默认服务器时间；精细需求可后续产品化 |
| raw content / original note | `content`（工作台当前 **未** 暴露该字段时，可写入 `summary` 前缀 `RAW:`） |
| summary | `summary` |
| product interest / customer need / objection / intent level | **无独立列**：写入 `summary` 或 `content` 的结构化段落（见模板文件 **Interaction 扩展块**） |
| next action（线索级） | 经 `POST .../touchpoint` 映射到 `Lead.next_action`（表单「线索下一步」） |
| next action due date | `Lead.next_action_due_date`（表单日期） |
| 本条互动待办 | `Interaction.next_action`（表单「本条互动的待办」） |

### C.4 与后端枚举 / API 字符串对齐

[`InteractionType` / `InteractionChannel`](../backend/app/models/enums.py) 中枚举值为 **展示用英文**（如 `phone_call` → `"Phone Call"`）。API 接受 **任意非空字符串**。

| 规范推荐（任务书） | 建议 API / 测试用字符串 | 备注 |
|--------------------|-------------------------|------|
| phone_call | `Phone Call` 或 `phone_call` | 与枚举成员名一致亦可 |
| email_sent / email_received | `Email` + `direction` 若后续 API 扩展；当前工作台 **无** `content`/`direction` 字段，可用 `summary` 标明 inbound/outbound |
| meeting | `Meeting` | |
| linkedin_message | `LinkedIn Message` | |
| site_visit | `Field Visit` 或自定义 `site_visit` | 与枚举不完全一致时以团队统一为准并在测试记录中注明 |
| trade_show_conversation | `Trade Show` + summary 说明 | |
| internal_note | `Internal Note` | |

**工作台 UI 实际字段**（[`LeadIntelligenceWorkbenchPage.vue`](../frontend/src/pages/leads/LeadIntelligenceWorkbenchPage.vue)）：`interaction_type`、`channel`、`subject`、`summary`、`next_action`、`next_action_due_date`、`interaction_next_action`。**无** `content`、`direction` 输入框——复杂场景可用 **API** 或 **Lead/Company notes** 补充，并在测试记录中标注 `Issue Type: documentation` 若需产品补齐。

### C.5 Intent Level（录入在 summary 中，直至结构化）

推荐：`cold` · `low` · `medium` · `high` · `urgent`  

示例行：`intent_level: medium`

### C.6 Product Interest（录入在 Lead 或 summary）

推荐：`desk_frame` · `lifting_column` · `lifting_leg` · `height_adjustable_desk` · `heavy_duty_system` · `ergonomic_solution` · `education_furniture` · `healthcare_furniture` · `oem_odm` · `unknown`  

线索级可写入 `leads.product_interest`（自由文本，影响评分输入）。

---

## Part D. 测试客户数据集设计

**不填写真实公司结论**；以下为 **待团队填入** 的矩阵模板。每类建议 1–3 家公司。

### D.1 十类客户与 segment 验证侧重点

| 类别 | 主要验证 segment | 应避免的错误组合 |
|------|------------------|------------------|
| 一般办公家具 dealer | `general_office_furniture_only`（弱信号） | 与 `lift_system_signal` 同时出现（规则互斥） |
| Contract furniture dealer | 同上或弱升降词 | 同上 |
| 明确销售 height adjustable desk | `lift_system_signal` | — |
| desk frame / lifting column / leg | `lift_system_signal` | — |
| heavy-duty / industrial adjustable | `heavy_duty_fit`（及可能 `lift_system_signal`） | 按真实文案记录 |
| education furniture supplier | `education_vertical` | — |
| healthcare / medical workstation | `medical_vertical` | — |
| importer / distributor | 视文案是否含 OEM/升降 | `oem_odm_fit` 需 **OEM 与升降上下文** |
| OEM/ODM 无升降上下文 | **不应**单独触发 `oem_odm_fit` | 记录若误触发则报 `scoring_rule` |
| OEM/ODM + 升降上下文 | `oem_odm_fit` | — |
| installer / relocation / project service | 视文案 | 以实际 `market_fit_segments` 为准 |
| interior / workplace planning | 常为弱信号或 `general_office_furniture_only` | — |

### D.2 单条测试客户模板（复制使用）

| 字段 | 内容 |
|------|------|
| Test Case ID | TC-D5-XXX |
| Company Name | （待填） |
| Website | （待填） |
| Expected Segment(s) | （待填，slug 列表） |
| Expected Non-Segment(s) | （待填，不应出现的 slug） |
| Expected Priority / Score band | （定性即可，非强制数值） |
| Notes | 录入日期、录入人、官网语言等 |

---

## Part E. A 域基础功能测试流程

每项：**操作** → **（可选）命令** → **预期** → **失败时记录**（使用 Part H 表；`Issue Type` 见模板）。

### E1. Backend health

| 步骤 | 操作 |
|------|------|
| 应用 | 无 |
| 命令（PowerShell，`cd backend`） | `python scripts/check_database_config.py` → 应 **Database connection: OK**；`python -m alembic upgrade head` → 成功；`python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| 验证 | `Invoke-RestMethod "http://127.0.0.1:8000/health" \| ConvertTo-Json -Depth 10` |
| 预期 | `database_status` 为 `ready`；`migration_pending` 为 `false`；`runtime_mode` 为 `development`（未设环境变量时）；根路径 `/` 返回 Not Found **为预期**，健康检查只用 `/health` |
| 失败记录 | `database_status` 为 `not_configured` / `auth_failed` 等时，先按 [dev_guide.md](dev_guide.md) 修 `.env` 与 PostgreSQL，勿强行测 A 域 |

### E2. Frontend dev

| 步骤 | 操作 |
|------|------|
| 命令 | `cd frontend` → `npm install` → `npm run dev` |
| 应用 | 浏览器登录；打开 **`/lead-intelligence`** |
| 预期 | 可登录；工作台可打开；选择线索后可加载工作流（依赖 E1） |
| 失败 | `frontend_error` 或 `backend_error`，附控制台与网络请求 |

### E3. Company CRUD

| 步骤 | 操作 |
|------|------|
| 应用 | 从导航进入 Companies：新建、编辑、列表、进入 **Company 详情**（含 D5.2 面板若已部署） |
| 预期 | 保存成功；`website`、`business_description` 等展示正确 |
| 失败 | `data_entry` / `frontend_error` |

### E4. Contact CRUD

| 步骤 | 操作 |
|------|------|
| 应用 | 在公司下新增/编辑联系人；从详情进入 Contact |
| 预期 | `company_id` 归属正确 |
| 失败 | `data_entry` |

### E5. Manual tags / intelligence（正式标签）

| 步骤 | 操作 |
|------|------|
| 应用 | 若 UI 支持对公司挂 **Tag / ObjectTag**：添加与查看；否则用 `product_interest_tags` 与 `business_description` 模拟情报输入 |
| 预期 | 与工作流中「意向标签」「业务描述」一致反映到 **评分输入** |
| 失败 | `documentation`（若找不到入口）或 `frontend_error` |

### E6. Lead Score（规则侧）

| 步骤 | 操作 |
|------|------|
| 应用 | 准备多家公司/线索：普通办公、升降桌、桌架/柱、重载、医疗、教育、仅 OEM、OEM+升降 |
| 预期 | 同一工作流中 **`lift_system_signal` 与 `general_office_furniture_only` 不同时出现**；单独 OEM 无升降上下文 **不应** 出现 `oem_odm_fit`；OEM+升降上下文 **应** 可出现 `oem_odm_fit` |
| 参考 | [intelligence_score.py](../backend/app/services/a_domain/intelligence_score.py)、[lead_intelligence_mvp.md](lead_intelligence_mvp.md) |
| 失败 | `scoring_rule` 或 `segment_rule`，附 `business_description` / tags 原文 |

### E7. Interaction / Next Action（工作台子集）

| 步骤 | 操作 |
|------|------|
| 应用 | 在 `/lead-intelligence` 选线索；在「记录触达」中分别试：`interaction_type` + `channel` 组合（如电话/邮件类文案）、更新 **线索下一步** 与 **日期**、**本条互动待办**；保存后刷新 |
| 预期 | 成功提示；再次加载工作流后 **Lead.next_action** 与日期与界面一致；互动列表若在 **Lead 详情** 可见则一致 |
| 限制 | 工作台 **无** `content`、`direction`、`interaction_next_action_due_date` 输入；深度场景见 Part C.3 |
| 失败 | `frontend_error` / `backend_error` |

---

## Part F. D5.2 Public-Source Enrichment 测试流程

参考：[public_source_enrichment_mvp.md](public_source_enrichment_mvp.md)；UI：[CompanyEnrichmentPanel.vue](../frontend/src/components/enrichment/CompanyEnrichmentPanel.vue)。

### F1. Enrichment 开关

| 步骤 | 操作 |
|------|------|
| 配置 | 在 `backend/.env` 设 `PUBLIC_ENRICHMENT_ENABLED=false`，重启后端 |
| 应用 | 打开公司详情，点击 **运行 enrichment** |
| 预期 | **API** `POST /api/companies/{id}/enrichment/runs` 返回 **403**；前端可能仍显示按钮但请求失败——记为 **实际行为**（`documentation` 或 `review_ui` 改进需求，非本轮开发） |
| 恢复 | 设回 `true` 并重启 |

### F2. Run enrichment

| 步骤 | 操作 |
|------|------|
| 应用 | 公司 **website** 合法可访问；点击运行；观察最近 run 状态 |
| 预期 | 状态 `pending` → `running` → `completed` 或 `failed`；**不应**无限 loading（面板有轮询上限） |
| 失败 | `enrichment_fetch` / `backend_error`，附 `error_message` |

### F3. Source evidence

| 步骤 | 操作 |
|------|------|
| 应用 | 打开审阅抽屉，查看来源表 |
| 预期 | URL、page_type、fetch_status、标题可见 |
| 失败 | `evidence_quality` / `enrichment_fetch` |

### F4. Suggestions

| 步骤 | 操作 |
|------|------|
| 应用 | 查看 business_summary、tag、market_segment、score_hint 及 evidence 摘录 |
| 预期 | 建议层与正式标签分层理解；**score_hint 非正式评分**（见 MVP 文档） |
| 失败 | `scoring_rule` / `evidence_quality` |

### F5. Accept / Reject / Apply

| 步骤 | 操作 |
|------|------|
| 应用 | 单条 accept/reject；批量 accept/reject；对 **已 accept** 执行 **写入正式画像** |
| 预期 | reject **保留行**；accept+apply 后 Company / Tag / Note 按类型更新（见 MVP） |
| 失败 | `review_ui` / `backend_error` |

### F6. Segment correctness via enrichment

| 步骤 | 操作 |
|------|------|
| 数据 | 选用 Part D 中各类官网（外网环境需合规） |
| 预期 | `market_segment` 建议与业务判断大体一致；记录系统与人工差异 |
| 失败 | 集中误判时 **不要** 进入 D5.3（见 Part I） |

---

## Part G. Desktop / Sidecar / Packaged Smoke Test

（PowerShell 使用 **`;`** 分隔命令，勿用 `&&`。）

### G1. sidecar prepare

```powershell
cd frontend
npm run sidecar:prepare
```

预期：生成 `src-tauri/binaries/intellioffice-backend-*.exe`（路径以控制台为准）。

### G2. tauri dev（managed sidecar）

```powershell
cd frontend
$env:INTELLIOFFICE_EXTERNAL_BACKEND = ""
$env:INTELLIOFFICE_MANAGE_SIDECAR = "1"
npm run tauri:dev
```

预期：Tauri 打开；`/desktop-launch` 健康检查；可进入登录与业务页（依赖本机 DB）。

### G3. Desktop 中跑 enrichment

在公司详情执行与 Web dev **相同** 的 enrichment / 审阅 / accept / reject；记录与浏览器差异。

### G4. Packaged build

```powershell
cd frontend
npm run tauri:build
```

预期：构建成功；在 `src-tauri\target\release\bundle\` 下找到 MSI/NSIS 或等价产物；最短路径打开应用并到达登录或 `/health` 就绪态。

---

## Part H. 测试记录模板（精简版）

完整列与 **Issue Type** 枚举见 [templates/manual_test_record_template.md](templates/manual_test_record_template.md)。

| Test ID | Module | Scenario | Company | Expected | Actual | Pass/Fail | Issue Type | Notes |
|---------|--------|----------|---------|----------|--------|-----------|------------|-------|
| E1-001 | Health | DB OK | — | ready | | | | |

**Issue Type 枚举**：`data_entry` · `scoring_rule` · `segment_rule` · `enrichment_fetch` · `evidence_quality` · `review_ui` · `backend_error` · `frontend_error` · `desktop_sidecar` · `documentation` · `business_judgment`

---

## Part I. 人工录入后的复盘标准与 D5.3 门槛

### I.1 可以进入 D5.3（Interaction Memory）讨论/立项的条件（建议）

至少满足：

- 已录入 **30–50 家真实客户**（或等价体量线索+公司）；
- Enrichment **主链稳定**（失败率可接受且有记录）；
- **accepted / rejected** 审核路径可用，团队愿意按此工作；
- **`general_office_furniture_only` 与 `lift_system_signal`** 区分大体符合业务预期；
- 用户愿意 **基于系统输出** 决定下一步跟进；
- 已记录 **第一批真实 interactions**（含自由文本中的 intent/需求摘要）；
- 主要痛点集中在 **互动沉淀与 follow-up**，而非 A 域基础能力整体失效。

### I.2 不应进入 D5.3 的情况

若出现以下情况，优先 **D5.2.1 Enrichment Quality Fix** 或 **D5.2.2 Review UX Refinement**（命名性阶段，非本仓库已命名里程碑）：

- enrichment **大量失败**；evidence **不可用**；segment **严重误判**；
- accept/reject/apply **逻辑混乱**；Company/Contact **基础录入不稳定**；
- Desktop sidecar 路径 **不稳定**。

### I.3 与路线图关系

路线图见 [roadmap_desktop_transition.md](roadmap_desktop_transition.md)（D5.3 未必已单独成行）。**以本文 Part I 为进入 D5.3 产品讨论的前置检查清单**，需经产品/技术评审后再排期，**不在本阶段直接开发 D5.3**。

---

## 相关链接

- Lead Intelligence 概念：[lead_intelligence_mvp.md](lead_intelligence_mvp.md)  
- Enrichment：[public_source_enrichment_mvp.md](public_source_enrichment_mvp.md)  
- 开发与诊断：[dev_guide.md](dev_guide.md) · [testing.md](testing.md)
