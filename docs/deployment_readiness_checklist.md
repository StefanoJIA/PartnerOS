# Deployment Readiness Checklist

**Release:** D5.2 Internal MVP · **Scope:** 部署前准备 · **Not a production deploy runbook**

## Required Environment Variables

| Variable | Where | Notes |
|----------|-------|-------|
| `APP_RUNTIME_MODE` | `backend/.env` | 生产勿用 `development` |
| `DATABASE_URL` | `backend/.env` | PostgreSQL 连接串（勿提交） |
| `SECRET_KEY` | `backend/.env` | JWT 签名；生产必须更换 dev 默认值 |
| `PUBLIC_BASE_URL` | `backend/.env` | 对外 HTTPS 域名，用于 manifest URL |
| `BACKEND_BASE_URL` | shell / CI | 脚本探测后端，默认 **`http://127.0.0.1:8010`**（D5.11） |
| `VITE_API_PROXY_TARGET` | `frontend/.env.local` | 开发 proxy，**须与 BACKEND_BASE_URL 端口一致** |
| `PUBLIC_ENRICHMENT_ENABLED` | `backend/.env` | 无外网/CI 可设 `false` |

See `backend/.env.example` and `frontend/.env.example`.

## Production Before-Go-Live

必须完成：

- [ ] 更换 `SECRET_KEY`（非 `dev-secret-change-in-production`）
- [ ] 设置 `PUBLIC_BASE_URL` 为 **HTTPS** 域名
- [ ] 确认 `DATABASE_URL` 指向生产数据库且可达
- [ ] `alembic upgrade head` — migration 无 pending
- [ ] `GET /health` → `status: ok`
- [ ] `GET /api/v1/system/readiness` → envelope ok
- [ ] `GET /api/v1/portal/manifest` → ok
- [ ] `GET /api/v1/portal/summary` → lead_intelligence counts
- [ ] `GET /api/v1/portal/a-domain/status` → `manual_outreach_ready: true`
- [ ] `python scripts/portal_consumer_check.py` → PASS
- [ ] `python scripts/config_readiness_check.py` → PASS（允许 PUBLIC_BASE_URL 等 WARN 在 staging 修复）
- [ ] `python scripts/dev_runtime_doctor.py` → PASS（D5.11）
- [ ] `python scripts/smoke_all_d5.py` → PASS（D5.11）
- [ ] `BACKEND_BASE_URL` 与 `VITE_API_PROXY_TARGET` 端口对齐
- [ ] 确认 **no secret leakage** in portal responses
- [ ] 确认 **automatic_sending_enabled: false**
- [ ] 确认 **LinkedIn / Outlook automation disabled**
- [ ] 确认 `backend/.env`、`local_data/` **不在 git** 中

## Automated Checks (local or CI)

```powershell
cd backend
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"
python scripts/config_readiness_check.py
python scripts/dev_runtime_doctor.py
python scripts/smoke_all_d5.py
python scripts/portal_consumer_check.py
python scripts/portal_readiness_check.py
python scripts/smoke_demo_ready.py
python -m pytest -q
```

## Optional Later (not D5.2)

- Redis
- Background worker
- HTTPS reverse proxy (nginx / IIS / cloud LB)
- Server backup & restore
- Monitoring / alerting
- Role permission hardening
- **Phase 2** CRM v1 façade（需明确授权）

## Phase 2 Gate

**Do not start Phase 2** until:

1. User explicitly authorizes scope change
2. D5.2 MVP stable in daily manual outreach use
3. Production secrets and `PUBLIC_BASE_URL` configured
4. Written decision on automation boundaries (still no auto-send unless re-scoped)

## References

- [operator_guide.md](operator_guide.md)
- [testing_summary_d5_2.md](testing_summary_d5_2.md)
- [releases/d5_2_internal_mvp_release_20260523.md](releases/d5_2_internal_mvp_release_20260523.md)
