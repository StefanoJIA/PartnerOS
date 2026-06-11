# D8.16 Operating Map + Daily Workbench Alignment

## 状态边界

- 当前阶段：READY_FOR_STAGING_HANDOFF
- 真实 staging：WAITING_FOR_REAL_STAGING_EVIDENCE
- D9：未进入
- proof records：未新增
- 外部动作：不自动发送邮件、短信、LinkedIn、webhook 或客户通知

D8.16 的目标不是新增大模块，而是把 PartnerOS 现有能力整理成中文业务团队每天可以使用的操作地图。PartnerOS 仍是内部 source of truth；`service.intelli-opus.com` 仍是 customer-facing portal，真实 staging 需要私密 token、allowed origin、HTTPS backend origin 和 `PUBLIC_BASE_URL` 后才能验证。

## 每天从哪里开始

业务员、运营人员和管理者每天从工作台开始。工作台顶部的“每日操作地图”把核心动作分成三类视角：

- 业务开发：客户开发、Campaign / 营销活动、人工外联、报价机会。
- 运营交付：订单、生产、物流、客户反馈、Portal 可见状态。
- 管理决策：Partner 表现、产品方向、市场响应、风险判断。

工作台不是单纯概览页，而是每日入口。每个卡片都必须能跳到具体处理页面：

- 客户开发：`/lead-intelligence`
- 营销触达：`/growth-operations`
- 报价单：`/quotes`
- RFQ：`/rfqs`
- 订单：`/orders`
- 交付协同：`/partner-operations`
- 客户反馈：`/feedback-tickets`
- 市场响应：`/market-response`
- Partner 接入：`/partner-onboarding`
- 演示流程：`/demo-walkthrough`

## 业务开发怎么用

业务开发人员先看“客户开发与 Campaign 下一步”：

1. 进入客户开发，复核今日待跟进客户、可触达客户和高优先级线索。
2. 进入 Growth Operations，选择或创建 Campaign / 营销活动。
3. 按照“规划活动 → 选择分群 → 创建外联任务 → 更新状态 → 查看报价/订单/反馈/市场响应”的顺序推进。
4. 对 HOSUN lifting systems、desk frames、desk legs、lifting columns、heavy-duty supply 和 JOOBOO education furniture / project furniture 使用同一套流程。
5. 外联任务只生成草稿和人工状态记录，不自动发送外部消息。

## 报价与订单怎么串起来

报价机会来自客户兴趣、Campaign 触达、RFQ 和产品适配。

1. 在工作台查看待处理报价 / RFQ。
2. 进入 `/quotes` 或 `/rfqs` 复核报价上下文。
3. 报价确认后进入订单流程。
4. 订单详情继续承载 partner split、supplier confirmation、production milestone、shipment plan、feedback summary 和 customer-visible summary。

这条链路让业务人员能回答：这个 Campaign 是否带来了 quote？quote 是否转成 order？订单交付和反馈是否支持继续推进该产品方向？

在系统演示中，这条链路可表述为 Campaign → Quote → Order → Feedback → Market Response。

## 运营交付怎么用

运营人员先看“订单交付与物流风险”和“客户 Feedback 处理”：

1. 进入 `/orders` 查看订单状态、生产摘要、物流摘要和客户可见状态。
2. 进入 `/partner-operations` 查看 partner split、供应商确认和交付协同。
3. 进入 `/feedback-tickets` 处理客户反馈，补充内部 response summary。
4. 反馈处理只记录内部动作，不自动回复客户、不承诺 SLA。
5. 如果 feedback、shipment risk 或 production delay 影响客户信心，再回到 Market Response 判断是否调整产品或 partner focus。

## 管理者怎么用

管理者先看“Market Response 推荐”和“Partner Onboarding 缺口”：

1. Market Response 解释为什么某个产品线值得关注，例如订单需求、物流风险、生产延迟、客户反馈和 watchlist。
2. Partner Onboarding 显示 HOSUN、JOOBOO 和未来 partner 的接入准备度、缺口和下一步。
3. 管理者用这些信息判断资源投入、产品方向、partner 优先级和演示准备度。

## 多 Partner 平级原则

HOSUN 和 JOOBOO 都是 PartnerOS 中的 partner 方向，不存在唯一主品牌。

- HOSUN：升降桌架、桌腿、升降柱、重载升降系统。
- JOOBOO：教育家具、项目制家具、学校空间采购。
- Future Partner：未来优质外贸品牌按同一流程进入。

PartnerOS 的价值在于把多个优质外贸品牌的客户开发、报价、订单、交付、反馈和市场响应放到同一个代理操作系统中，而不是做单一 CRM 或单品牌工具。

## 安全与 staging 边界

D8.16 不改变 D8 边界：

- 不进入 D9。
- 不新增 proof records。
- 不写真实 staging validated 状态。
- 不自动发送客户或供应商通知。
- 不调用真实 Constant Contact、销售易、承运商或 webhook。
- 不提交 `.env`、token、PDF、`local_data/`、`backend/storage/` 或 `IE Auto.pdf`。
