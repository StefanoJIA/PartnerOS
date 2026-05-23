# intelliOffice Operator Guide

**Audience:** 内部运营 / 客户开发 / 演示人员  
**Release:** D5.2 Internal MVP · **Not Phase 2**

## Daily Startup

### Backend — port 8000 (default)

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Backend — port 8010 (when 8000 is busy)

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Align scripts and frontend proxy (PowerShell):

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8010"
```

Or set `frontend/.env.local` (gitignored):

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:8010
```

### Frontend

```powershell
cd frontend
npm run dev
```

Open the URL printed by Vite (often `http://127.0.0.1:5173` or `5174`).

### Quick health check

```powershell
cd backend
python scripts/check_backend_runtime.py
```

## Daily Workflow

1. 登录 `/login`（seed 凭据见 README，**勿在记录中写密码**）
2. **（新 lead）** 打开 `/lead-intake` → 粘贴或上传 CSV → **Preview** → 检查 missing / duplicate / segment → **Confirm Import**
3. 打开 `/lead-intelligence` → 查看 **Lead Completeness** → 筛选 **Needs Contact Research** → 点击 **Research / Edit** 在 drawer 中补资料（D5.5）
4. 选择 lead → 查看 **Outreach History** timeline 与 follow-up hint（D5.6）
5. 打开 `/lead-intelligence` → Manual Outreach Queue
6. 查看 **Daily Summary** cards
7. 筛选 **High Priority** → 优先处理
8. 筛选 **Needs First Outreach** → 首次外联
9. 筛选 **Waiting for Reply** → 跟进已发送未回复
10. 选择 lead → **Generate Draft**
11. **Copy Draft** → 在 LinkedIn / Email **系统外**粘贴发送
12. 回到系统 → **Mark as Sent**（仅记录，不自动发送）
13. 确认 **Outreach History** timeline 已更新
14. 在 **Follow-up Scheduler** 设置下次跟进日期（D5.7）
15. 使用 **Due queue filters** 查看 Overdue / Due Today / Due Soon
16. 确认 **next action** 已更新
17. 每日结束（可选 CLI）：

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"   # if using 8010
python scripts/daily_outreach_summary.py
python scripts/daily_follow_up_summary.py
```

## Useful URLs

| URL | Purpose |
|-----|---------|
| `/login` | 登录 |
| `/lead-intake` | CSV lead 导入与批量预检（D5.3） |
| `/lead-intelligence` | 每日跟进工作台 |
| `/system-health` | 系统与 Portal readiness |
| `/portal-consumer-mock` | 模拟外部 Portal 只读消费 |
| `/companies` | CRM 公司列表 |
| `/contacts` | 联系人 |

## Useful Scripts

| Script | Purpose |
|--------|---------|
| `check_backend_runtime.py` | 后端是否可达 |
| `check_database_config.py` | 数据库与迁移 |
| `config_readiness_check.py` | 部署前配置一致性 |
| `smoke_demo_ready.py` | Demo 数据 smoke |
| `pilot_workflow_check.py` | Pilot 工作流 |
| `outreach_queue_check.py` | 外联队列 |
| `real_lead_batch_check.py` | 真实批次 pilot |
| `daily_outreach_summary.py` | 每日只读摘要 |
| `portal_readiness_check.py` | Portal v1 端点 |
| `portal_consumer_check.py` | 外部 Portal 契约 |

## Safety Rules

- 所有草稿 **人工审核** 后再发送
- **不自动发送** 任何消息
- **不抓 LinkedIn**、不绕过平台限制
- **不提交** `local_data/` 私有 CSV
- **不提交** `.env` / token / secret
- **不提交** 未打码截图

## Troubleshooting

| 问题 | 处理 |
|------|------|
| 前端 API 404 / 502 | 确认 backend 运行；`BACKEND_BASE_URL` 与 `VITE_API_PROXY_TARGET` 端口一致 |
| 8000 被占用 | 改用 8010，见 [dev_guide.md](dev_guide.md) § Changing backend port |
| migration pending | `cd backend && alembic upgrade head` |
| Portal summary 空 | 确认 DB 有 leads；backend 为新代码实例 |

## Further Reading

- [D5.2 Release Note](releases/d5_2_internal_mvp_release_20260523.md)
- [Deployment Readiness Checklist](deployment_readiness_checklist.md)
- [D5.2.12 Screenshot Demo Proof](records/d5_2_12_browser_screenshots_demo_proof_20260523.md)
- [Manual A-Domain Test Plan](manual_a_domain_test_plan.md)
