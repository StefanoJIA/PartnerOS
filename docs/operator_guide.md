# intelliOffice Operator Guide

**Audience:** 内部运营 / 客户开发 / 演示人员  
**Release:** D5.2 Internal MVP · **Not Phase 2**

## Daily Startup

### Recommended — port 8010 (D5.11 default)

```powershell
# Optional: set env in one shot
.\scripts\dev_env_8010.ps1

cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Or use helper (does not auto-kill stale processes):

```powershell
.\scripts\start_backend_8010.ps1
```

Align scripts and frontend proxy:

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8010"
```

Or set `frontend/.env.local` (gitignored):

```env
VITE_API_PROXY_TARGET=http://127.0.0.1:8010
```

**Do not run multiple uvicorn instances with different code versions.** If 8010 is occupied but `/health` fails, see [Runtime Startup Routine](#runtime-startup-routine).

### Legacy — port 8000

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
$env:BACKEND_BASE_URL="http://127.0.0.1:8000"
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
python scripts/dev_runtime_doctor.py
```

## Runtime Startup Routine

1. 启动 Docker DB：`docker compose up -d db`
2. 设置环境：`.\scripts\dev_env_8010.ps1`（或手动 `BACKEND_BASE_URL` / `VITE_API_PROXY_TARGET`）
3. 启动 backend **8010**（单一实例，最新代码）
4. 启动 frontend：`cd frontend; npm run dev`
5. 运行 `python scripts/dev_runtime_doctor.py`
6. 运行 `python scripts/smoke_all_d5.py`

**Stale port 8010**（占用但 `/health` 失败）：

```powershell
netstat -ano | findstr :8010
tasklist /FI "PID eq <PID>"
Stop-Process -Id <PID> -Force
```

Fallback：`$env:BACKEND_BASE_URL="http://127.0.0.1:8013"` 与相同 `VITE_API_PROXY_TARGET`。

## Daily Workflow

0. 登录后打开 **Dashboard `/`** → **Daily Operations Command Center**（D5.8 / D5.9）：summary cards、Today Focus、Recent Manual Outreach、Recent Contact Research、Quick Actions
1. 登录 `/login`（seed 凭据见 README，**勿在记录中写密码**）
2. **（新 lead）** 打开 `/lead-intake` → 粘贴或上传 CSV → **Preview** → 检查 missing / duplicate / segment → **Confirm Import**
3. 打开 `/lead-intelligence` → 查看 **Lead Completeness** → 筛选 **Needs Contact Research** → 点击 **Research / Edit** 在 drawer 中补资料（D5.5）
4. 选择 lead → 查看 **Product Fit & Project Opportunity** card（D5.12）：产品方向、quote readiness、discovery questions
5. 查看 **Product Opportunity Board**（D5.13）→ 筛选 High Opportunity / Quote Ready / Lifting Systems
6. 选择 lead → 查看 **Outreach History** timeline 与 follow-up hint（D5.6）
7. 打开 `/lead-intelligence` → Manual Outreach Queue
8. 查看 **Daily Summary** cards
9. 筛选 **High Priority** → 优先处理
10. 筛选 **Needs First Outreach** → 首次外联
11. 筛选 **Waiting for Reply** → 跟进已发送未回复
12. 选择 lead → **Generate Draft**
13. **Copy Draft** → 在 LinkedIn / Email **系统外**粘贴发送
14. 回到系统 → **Mark as Sent**（仅记录，不自动发送）
15. 确认 **Outreach History** timeline 已更新
16. 在 **Follow-up Scheduler** 设置下次跟进日期（D5.7）
17. 使用 **Due queue filters** 查看 Overdue / Due Today / Due Soon
18. 确认 **next action** 已更新
19. 收工时 Dashboard **End-of-Day Summary** → **Copy Summary**（D5.10）
20. 每日结束（可选 CLI）：

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"   # if using 8010
python scripts/daily_outreach_summary.py
python scripts/daily_follow_up_summary.py
python scripts/daily_work_summary.py
```

## Useful URLs

| URL | Purpose |
|-----|---------|
| `/` | Dashboard · Daily Operations Command Center（D5.8） |
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
| `daily_follow_up_summary.py` | 每日 follow-up 摘要（D5.7） |
| `daily_ops_summary_check.py` | Daily Operations API smoke（D5.8） |
| `daily_work_summary.py` | End-of-day work summary CLI（D5.10） |
| `dev_runtime_doctor.py` | 统一 runtime 诊断（D5.11） |
| `smoke_all_d5.py` | 一键 D5.x smoke（D5.11） |
| `product_opportunity_check.py` | Product opportunity board smoke（D5.13） |
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
