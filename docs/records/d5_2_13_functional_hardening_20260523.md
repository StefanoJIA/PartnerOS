# D5.2.13 Functional Hardening & Error-Free Sprint

## Goal

确保 D5.2 Internal MVP 的所有核心功能可以连续运行，不出现 P0/P1 报错。

## Checked Areas

- DB（Docker compose `db`，5435，Alembic head `0005_company_enrichment`）
- Backend health / readiness（8010）
- Frontend login / token / logout 错误提示
- Lead Intelligence（Daily Summary、队列、workflow、空状态）
- Outreach Draft（Generate / Copy / Mark as Sent / safety notice）
- Manual Outreach Queue
- Mark as Sent / touchpoint / next action 持久化（脚本验证）
- Enrichment（公司详情 panel，accept/reject）
- System Health（DB ready、optional redis/worker warning）
- Portal Consumer Mock / portal read-only API
- Scripts（smoke、pilot、outreach queue、real lead batch、daily summary、portal checks）
- pytest / vitest

## Fixes

| 问题 | 修复 |
|---|---|
| DB 未就绪时 `/api/v1/portal/summary` 可能 500 | `build_portal_summary_degraded()`：DB 不可用时返回 200 envelope，计数为 0，warnings 含 DB 提示 |
| DB 短暂不可用后 `/health` 长期 `status=error` | `merge_snapshot_with_live_db()`：DB 恢复后重新 `inspect_lifecycle_dev()`，清除 stale error 快照 |
| 前端登录/外联/系统页面对 500 提示混乱 | 新增 `frontend/src/api/errors.ts`（`formatApiError`、`DB_HINT`、`BACKEND_HINT`） |
| Lead Intelligence 队列加载失败无 inline 提示 | `LeadIntelligenceWorkbenchPage.vue` 增加 warning banner + 友好错误文案 |
| Portal Consumer Mock 错误信息不具体 | `PortalConsumerMockPage.vue` 使用 `formatApiError` |
| `portal_consumer_check.py` 非 JSON 响应崩溃 | 增加 `_safe_json()` 容错 |
| `check_database_config.py` DB 不可用提示不清 | 增加 Docker Desktop / `docker compose up -d db` 指引 |
| `portal_readiness_check.py` health 仅接受 `ok` | 同时接受 `degraded`（migration pending 场景） |
| A-domain stage / test baseline 过期 | 更新为 `D5.2.13`，pytest 97 / vitest 47 |
| 端口 8010 多进程冲突导致误报 | 文档与报告：清理 stale uvicorn 后重跑 `check_backend_runtime.py` |

## Remaining Warnings

| 问题 | 级别 | 阻塞 |
|---|---|---|
| `APP_RUNTIME_MODE=development` — rotate secrets before production | P3 | 否 |
| `PUBLIC_BASE_URL` 未设置 — manifest URL 默认 8000 | P3 | 否 |
| `redis_ready=false` / `worker_ready=false` | P3 | 否（optional） |
| 浏览器手工 UI 截图未纳入本轮完成条件 | P3 | 否 |

## Verification (2026-05-23)

Backend（`BACKEND_BASE_URL=http://127.0.0.1:8010`）：

- `check_database_config.py` — OK，migration pending: False
- `check_backend_runtime.py` — OK，status=ok
- `config_readiness_check.py` — PASS（2 warnings）
- `smoke_demo_ready.py` — PASS
- `pilot_workflow_check.py` — PASS
- `outreach_queue_check.py` — PASS
- `real_lead_batch_check.py` — PASS
- `daily_outreach_summary.py` — OK
- `portal_readiness_check.py` — PASS
- `portal_consumer_check.py` — PASS
- `python -m pytest -q` — **97 passed, 1 skipped**

Frontend：

- `npm run test -- --run` — **47 passed**

Safety：

- automatic sending disabled（portal a-domain + draft checks）
- 不自动发送、不抓 LinkedIn、不接 Outlook
