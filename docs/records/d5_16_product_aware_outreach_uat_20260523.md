# D5.16 Product-Aware Outreach UAT & Real Lead Pilot

## Goal

用真实客户批次验证 intelliOffice 是否适合每日产品导向客户开发（Lead Intake → Completeness → Product Fit → Pre-Quote → Product-Aware Draft → Mark as Sent → Follow-up → End-of-Day Summary）。

## UAT Batch

本地文件（**不提交 git**）：`local_data/real_leads_d5_16_uat.private.csv`（12 行，含 education / medical 补充样本）

| Company | Lead Type | Expected Product Focus | Notes |
|---|---|---|---|
| SWC Office Furniture | Dealer / lift | HOSUN lifting systems | 升降桌架经销商，多产品线备注 |
| Jefferson Group | Project / FF&E | project_supply | 内装项目客户，notes 含 JOOBOO 交叉提及 |
| Yony's Office Furniture | Project / lift | project_supply | 项目 + 升降信号 |
| Commercial Furniture Resource | General office | adjustable desk frames | 一般办公家具经销商 |
| Human Active Technology | Lift / OEM | hosun_lifting + OEM | 组件/OEM 潜力 |
| OCI Office Concepts Inc. | Dealer / lift | hosun_lifting systems | 经销商升降兴趣 |
| LABERS Furniture | General office | adjustable desk frames | 区域经销商 |
| Overnight Office | General office | adjustable desk frames | 待 enrichment |
| Dancker | Project / FF&E | project_supply | 商业内装项目 |
| Transfer Enterprises | General / research | adjustable desk frames | 缺联系人，需 research |
| Campus Learning Furniture | Education | jooboo_education_furniture | 教育家具 RFP 场景 |
| Metro Lab Workspace Co | Medical / lab | medical_workspace | 医疗/实验室工作站 |

## Workflow Coverage

| Workflow | Result | Notes |
|---|---|---|
| Lead Intake | Pass | CSV preview 12/12 readable；11 duplicate（已存在 pilot 数据）；1 WARN（Transfer 缺联系人） |
| Completeness | Pass | 30 leads；15 complete / 6 ready / 9 needs research |
| Contact Research | Pass | Transfer Enterprises 正确标记需 research |
| Product Fit | Pass (tuned) | 多 segment 时 project 优先于 education（Jefferson 已校准） |
| Product Opportunity Board | Pass | 30 rows；high/promising 分布合理 |
| Pre-Quote Prep | Pass | missing info 与 quote_readiness 可用；部分 lead 项偏多 → D5.17 |
| Product-Aware Draft | Pass | 11/11 pilot lead 可生成 email draft；LinkedIn ≤300 chars |
| Mark as Sent | Pass | 已有 touchpoint / waiting_reply=3（历史 D5.x 操作） |
| Follow-up | Pass | due_soon=6；follow-up queue API 200 |
| End-of-Day Summary | Pass | daily-work-summary copyable_summary 可用 |

## Rule Feedback

| Area | Feedback | Severity | Suggested Next |
|---|---|---|---|
| lifting systems | SWC / HAT / Yony's 升降 focus 合理 | — | 保持 |
| project supply | Jefferson / Dancker project focus 合理 | — | 保持 |
| education furniture | notes 含 JOOBOO 时易触发 education_vertical | P2 | D5.17：education 仅在 primary 场景排前 |
| OEM / ODM | HAT component focus 合理 | — | 保持 |
| quote readiness | 多数 pilot 为 almost_ready / not_ready，符合直觉 | — | 保持 |
| missing quote info | 常含 color/cert/delivery 等 6–10 项，偏泛 | P2 | D5.17：按 segment 精简 checklist |
| draft style | product_discovery 邮件结构清晰，可人工修改后发送 | — | 保持 |
| opportunity score | 部分 lift dealer 为 promising 而非 high | P3 | D5.17 微调 scoring |
| general office dealers | 默认带 adjustable frame intro，合理 | — | 保持 |

## Safety

- no automatic sending
- no quote creation
- no pricing
- no inventory promise
- no certification promise
- no lead-time promise
- real CSV not committed（`local_data/` gitignored）

## Acceptance Criteria

- [x] 10+ leads tested（11 pilot + seed leads = 30 active）
- [x] 3+ product focus categories（lift / project / general / education / medical / OEM）
- [x] product-aware draft for 5+ leads（11/11 pilot）
- [x] 3+ leads with touchpoint / simulated sent（existing interactions）
- [x] follow-up queue populated（due_soon=6）
- [x] UAT feedback recorded
- [x] tests pass

## Code Change (D5.16)

- `product_fit.py`：当同时存在 `project_based_furniture` 与 `education_vertical` 时，`project_supply` 排在 `jooboo_education_furniture` 之前
- `d5_16_real_lead_uat_check.py`：只读 UAT API 覆盖检查
