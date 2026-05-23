# Lead Intelligence MVP（A 域）说明

## 定位

**Lead Intelligence** 是 intelliOffice **A 域（市场与客户情报）** 的核心能力，**不是**「另一套通用 CRM 列表」。它强调：

- **升降系统**（桌架、桌腿、升降柱、重载可调方案、人体工学办公等）相关的**市场响应**；
- **证据与可解释性**（规则评分、segment 标签、后续 D5.2 的公开来源证据）；
- **伙伴平级**：intelliOffice 为平台品牌；制造伙伴均为数据中的平级实体，系统结构**不得**优待任一工厂名称。

## 当前首版闭环（D5）

数据流（人工维护与规则侧）：

```text
Company → Contact → Intelligence Tags → Lead Score → Interaction → Next Action
```

- **Company / Contact**：CRM 主数据；`product_interest_tags`、`business_description` 等承载可读情报。
- **Intelligence Tags**：正式标签通过 `Tag` + `ObjectTag`（`object_type=company` 等）挂载，**非** enrichment 自动建议的同义字段。
- **Lead Score / segments**：[`backend/app/services/a_domain/intelligence_score.py`](../backend/app/services/a_domain/intelligence_score.py) 提供 **可解释** 的 `IntelligenceScoreResult` 与 **`market_fit_segments`**；[`/lead-intelligence`](../frontend/src/pages/leads/LeadIntelligenceWorkbenchPage.vue) 工作台聚合线索侧工作流。

## 当前 `market_fit_segments`（稳定 slug）

| Segment | 含义（简述） |
|---------|----------------|
| `lift_system_signal` | 已命中明确升降/可调类产品语义（强信号） |
| `oem_odm_fit` | OEM/ODM 与升降/桌架等上下文共同出现 |
| `medical_vertical` | 医疗/医护家具场景 |
| `education_vertical` | 教育场景 |
| `heavy_duty_fit` | 重载/工业级升降相关 |
| `general_office_furniture_only` | **弱适配**：办公家具行业相关，但**尚无**足够明确升降系统意向（D5.1） |

### `general_office_furniture_only` 特别说明

- **不是负面标签**、不是「差客户」；表示 **当前证据不足以支撑升降核心业务的** 优先排序。
- 与 **`lift_system_signal` 互斥**（不会同时出现）。
- 适合：**低频 nurture**、等待 **Public-source enrichment** 或人工补充后再判断是否升入强信号池。

## 为什么升降系统响应是 A 域主轴

与产品愿景一致：当前最值得结构化的信号是客户对 **height adjustable / sit-stand / desk frame / lifting column / leg / heavy-duty / ergonomic / medical / education / OEM-ODM lifting** 等的真实响应——这与通用 CRM 的「联系人+阶段」叙事不同，是 intelliOffice **差异化** 的基础。

## 当前明确不做什么（D5 范围内）

- 不把 **自动建议** 当作正式事实静默写库（见 D5.2 enrichment 的人审分层）。
- **大规模爬虫**、**搜索引擎收录**、**LinkedIn/邮件自动化**、**RFQ/报价/订单全链** 不作为 MVP 必选依赖。
- **D6** 级产品化（安装包定稿、诊断包等）不在 D5 主线内。

## 后续演进方向（与路线图一致）

- **Public-source enrichment**（D5.2）：公司官网等**有限**公开页 → 证据 → 建议 → **人工审核** → 可选写回正式画像。
- **Evidence-based tag suggestions**：每条建议绑定 URL、摘录、匹配短语。
- **Human review**：pending / accepted / rejected（拒绝记录保留，避免重复误判无迹可循）。
- **Campaign / outreach**：在高质量事实沉淀之后，再由产品阶段推进。
- **RFQ linkage**：高分线索/强信号与公司 → RFQ/样品等 B/C 域对象深链。
- **Partner capability matching**：按 **品类与能力**，而非按单一伙伴名称，做匹配与推荐。

## 相关代码与文档

- 评分与 segments：[`backend/app/services/a_domain/intelligence_score.py`](../backend/app/services/a_domain/intelligence_score.py)
- A 域 API：[`backend/app/api/routes/a_domain.py`](../backend/app/api/routes/a_domain.py)
- 工作台：`/lead-intelligence`
- 迁移与路线：[migration_from_web_to_desktop.md](migration_from_web_to_desktop.md)、[roadmap_desktop_transition.md](roadmap_desktop_transition.md)
- 公开来源 enrichment（D5.2）：[public_source_enrichment_mvp.md](public_source_enrichment_mvp.md)
