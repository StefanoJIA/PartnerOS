# D5.12 Product Fit & Project Opportunity Planner

## Goal

让系统判断每个 lead 适合什么产品方向、是否具备项目机会、是否 quote-ready。

## Business Focus

- HOSUN lifting systems
- adjustable desk frames
- desk legs
- lifting columns
- JOOBOO education furniture
- medical / lab workspace
- project-based furniture
- OEM / ODM components

## Workflow

1. 打开 `/lead-intelligence`。
2. 选择 lead。
3. 查看 **Product Fit & Project Opportunity** card。
4. 查看 recommended product focus。
5. 查看 quote readiness 与 missing quote info。
6. 复制 discovery questions 或 product brief。
7. 通过人工外联询问客户（系统外发送）。
8. 记录 touchpoint / set follow-up。

## API

- `GET /api/a-domain/leads/{lead_id}/product-fit` — per-lead derived product fit
- `GET /api/a-domain/product-opportunity-board` — all-lead summary rows

## Safety

- no automatic sending
- no price promise
- no inventory promise
- no certification promise
- no quote creation
- human-reviewed sales workflow only

## Acceptance Criteria

- product fit card 可用
- discovery questions 可复制
- quote readiness 可见
- pytest / vitest pass
- no DB migration
