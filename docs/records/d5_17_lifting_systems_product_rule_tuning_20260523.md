# D5.17 Lifting Systems & Product Rule Tuning

## Goal

根据 D5.16 UAT 调优产品方向、机会评分、报价前缺失信息和 discovery 问题长度。

## Tuned Areas

- education vs cross-sell（JOOBOO 弱提及不再 primary）
- HOSUN lifting systems 与 adjustable desk frames / desk legs / lifting columns 细分
- heavy-duty lifting systems 加权
- OEM / ODM lifting components 优先
- project_supply 优先于 education cross-sell
- missing_quote_info 按 quote_readiness 上限（not_ready ≤4，almost_ready ≤6）
- discovery questions 默认 ≤4（LinkedIn ≤2）

## Before / After

| Case | Before | After |
|---|---|---|
| Jefferson + JOOBOO mention | jooboo + project 混排 | project_supply first，无 jooboo primary |
| SWC dealer + JOOBOO catalog | education_vertical 误触发 | 仅 HOSUN / frames focus |
| Campus / school lead | jooboo primary | jooboo primary（强教育信号保留） |
| missing_quote_info | 常 6–10 项 | not_ready ≤4，almost_ready ≤6 |
| SWC opportunity score | 偏 conservative | 更易达 promising（live ~75） |

## Safety

- no quote creation
- no pricing
- no inventory promise
- no certification promise
- no lead-time promise
- no automatic sending

## Acceptance Criteria

- D5.17 rule check passes
- D5.16 UAT check still passes
- product-aware draft check passes
- pytest passes
- no DB migration
