# D5.2 Internal MVP Release

**Release tag (internal):** D5.2.x · **Date:** 2026-05-23 · **Latest stage:** D5.2.11

## Release Scope

本版本包含：

- CRM 基础客户与联系人管理
- Lead Intelligence scoring（可解释评分）
- `market_fit_segments`（升降系统 / 教育 / 医疗 / 项目 / 通用办公等）
- Public source enrichment（官网有限抓取 + 人工审阅 apply）
- Manual Outreach Queue（人工外联队列）
- Human-reviewed outreach drafts（人工审核草稿）
- Mark as Sent touchpoint recording（系统外发送后记录）
- Daily Follow-up Rhythm（每日跟进节奏与 Summary）
- Real Lead Batch Pilot 验证路径
- Portal Read-only Integration（v1 manifest / summary / a-domain status）
- Portal Consumer Mock（模拟未来统一 Portal 只读消费）
- System Health / Readiness

## Business Focus

重点服务：

- HOSUN lifting systems
- adjustable desk frames
- lifting columns
- desk legs
- JOOBOO education furniture
- medical / lab workspace
- project-based furniture customers
- OEM / ODM opportunities

## What This Release Can Do

1. **导入 lead** — CSV preview / apply（`lead_import_*` 脚本与 UI 路径）
2. **识别客户类型** — segment 与 intelligence score
3. **生成外联草稿** — channel + product focus 模板
4. **人工复制发送** — Copy Draft，在 LinkedIn / Email 客户端粘贴
5. **Mark as Sent** — 记录 touchpoint（`manually_sent=true` 摘要）
6. **记录 touchpoint** — 互动历史与 next action
7. **设置 next action** — Lead Intelligence 工作台
8. **每日查看跟进队列** — `/lead-intelligence` Daily Summary + filters
9. **Portal 只读查看状态** — `/api/v1/portal/*` · `/system-health` · `/portal-consumer-mock`

## What This Release Does Not Do

- **不自动发送邮件**
- **不自动发送 LinkedIn**
- **不抓取 LinkedIn**
- **不接 Outlook API**
- **不做自动化浏览器操作**
- **不做报价 / 订单 / 生产 / 运输闭环**
- **不等于 Phase 2**

## Known Limitations

- **Screenshot archive:** procedure + capture script in D5.2.12; PNG stored locally only (gitignored), not committed — see [d5_2_12 demo proof](../records/d5_2_12_browser_screenshots_demo_proof_20260523.md)
- Follow-up date 仍是文案推断，无结构化 follow-up 日期字段
- Redis / worker 未接入（readiness 中为 optional warning）
- `PUBLIC_BASE_URL` 生产前需配置
- `SECRET_KEY` 生产前需更换（勿使用 dev 默认值）
- Manual Outreach Queue 加载时 per-lead workflow 调用，大规模数据可能有 N+1 API 性能问题
- 真实客户 CSV 仅放 `local_data/`（gitignore），不提交仓库

## Phase 2 Prerequisites（未启动）

进入 Phase 2 前需 **用户明确授权**，并至少满足：

1. D5.2 Internal MVP 在真实客户试运行中稳定使用
2. 生产 `SECRET_KEY` / `PUBLIC_BASE_URL` / HTTPS 就绪
3. Portal 只读集成在目标环境验证通过
4. 明确 Phase 2 范围（如 CRM v1 façade、自动化边界、Redis/worker 等）的书面决策
5. **不**因本 release 自动开启任何自动发送或 LinkedIn/Outlook 集成

## Related Documents

| 文档 | 用途 |
|------|------|
| [operator_guide.md](../operator_guide.md) | 日常操作 |
| [deployment_readiness_checklist.md](../deployment_readiness_checklist.md) | 部署前检查 |
| [testing_summary_d5_2.md](../testing_summary_d5_2.md) | 测试基线 |
| [demo_script_20260523.md](../records/demo_script_20260523.md) | 演示脚本 |

## Verification Commands

```powershell
cd backend
python scripts/config_readiness_check.py
python scripts/portal_consumer_check.py
python scripts/smoke_demo_ready.py
python scripts/daily_outreach_summary.py
python -m pytest -q
```
