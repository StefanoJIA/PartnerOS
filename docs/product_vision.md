# intelliOffice 产品愿景

## 1. 项目本质（重新定义）

**intelliOffice PartnerOS** 是面向 **Windows** 的、**本地优先（local-first）**、**AI 辅助**、**供应链贯通**的家具行业 **桌面商业操作系统**——统一承载市场情报、销售执行、产品与伙伴、项目流转、知识与 AI、系统服务六大域。

它不是：

- 单纯的 CRM 或 Web 网站  
- 单纯的供应商数据库或独立 Lead 工具  
- 需要最终用户自行安装 PostgreSQL、使用 pgAdmin、理解 Docker 或命令行的「开发者部署型网站」

最终交付形态见 [architecture_desktop_target.md](architecture_desktop_target.md) 与根目录 [](../README.md) 中 **Product vision** 小节。

## 2. 价值闭环（端到端）

在统一平台内贯通（概念顺序，非独立产品）：

市场需求采集 → 客户情报 → Lead 评分与排序 → LinkedIn / Email 沟通 → 地推安排 → 产品匹配 → **平级**制造伙伴匹配 → RFQ → 报价与比价 → 样品 → 订单 → 生产里程碑 → 海运 → 客户更新 → 售后与复购 → 市场趋势判断。

**Lead Intelligence**（公司发现、网站分析、Segment、评分等）属于 **A 域（市场与客户情报）** 的核心引擎，**不得**做成与 RFQ、伙伴、样品、订单割裂的外部孤岛；数据与动作应可直接流入 B/C/D 域。

## 3. 商业与架构规则

| 规则 | 说明 |
|------|------|
| 品牌主体 | **intelliOffice** 为对美销售与项目品牌。 |
| 伙伴平级 | **HOSUN** 为早期合作制造伙伴之一；**重庆汇聚 / JOOBOO** 等为另一制造伙伴；未来可接入更多中国制造商。**全部为 `manufacturing_partners` 表中的平级行。** |
| 禁止厂牌偏向 | 不得 hard-code HOSUN；不得默认 HOSUN 优先。推荐、排序、AI 比较须基于：product fit、quality、certification、price、MOQ、lead time、sample support、communication、project suitability、U.S. market readiness 等 **结构化字段**，而非厂牌名称。 |
| 市场焦点 | 客户与市场情报须特别关注市场对 **升降与人体工学支撑** 的响应：adjustable desk frames、lifting columns、desk legs、heavy-duty lifting systems、sit-stand workstations、ergonomic height-adjustable solutions 等（与产品/伙伴能力标签、RFQ 需求解析联动）。 |

## 4. 功能六域（防割裂）

| 域 | 主要内容 |
|----|----------|
| **A — 市场与客户情报** | Company finder、网站分析、Lead scoring、联系人发现、市场情报、升降系统需求识别、地推候选、Segment builder；**Lead Intelligence 归属本域** |
| **B — 销售执行** | Leads、Companies、Contacts、Interactions、Tasks、LinkedIn/Email 助手、跟进、Dashboard、Field visit（能力可渐进完善） |
| **C — 产品与制造伙伴** | Products、Manufacturing partners、产品-伙伴链接、认证与质量文档、伙伴风险、**平级匹配逻辑** |
| **D — 项目流转** | RFQ、行项目、候选伙伴、报价、比价、样品、订单、生产里程碑、海运记录 |
| **E — AI 与知识** | AI outputs、提示模板、RAG 知识库、产品与伙伴推荐、客户画像、市场趋势、RFQ/订单相关分析 |
| **F — 系统服务** | 认证、设置、文件、标签、备注、活动日志、备份恢复、Bootstrap、本地 DB 管理、诊断、打包与更新 |

路线图与阶段见 [roadmap_desktop_transition.md](roadmap_desktop_transition.md)。

## 5. 相关文档

- [project_reorientation_summary.md](project_reorientation_summary.md) — 路线调整动机与总述  
- [migration_from_web_to_desktop.md](migration_from_web_to_desktop.md) — 当前仓库与未来桌面产品关系  
