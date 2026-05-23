# D5.2.10 Portal Consumer Mock & Deployment Readiness

## Goal

验证统一 Portal 可以只读消费 intelliOffice 状态，并准备未来服务器部署前检查。

## Read-only Consumer Flow

1. Portal 请求 `GET /api/v1/portal/manifest`
2. Portal 请求 `GET /api/v1/portal/summary`
3. Portal 请求 `GET /api/v1/portal/a-domain/status`
4. Portal 请求 `GET /api/v1/system/readiness`（可选）
5. Portal 显示 service status 和 daily lead summary
6. Portal **不写入** intelliOffice

## UI Mock

- 路由：`/portal-consumer-mock`
- 从 `/system-health` 可跳转
- 只读展示 service、health、lead counts、safety flags、capabilities、warnings

## Local Config

| 变量 | 用途 |
|------|------|
| `BACKEND_BASE_URL` | 后端脚本默认 `http://127.0.0.1:8000` |
| `VITE_API_PROXY_TARGET` | Vite dev proxy 目标 |
| `PUBLIC_BASE_URL` | manifest 中对外 URL 拼接 |
| Backend port | 8000（默认）或 8010（备用） |

三者应一致指向同一 backend 实例。

## Check Scripts

```powershell
cd backend
python scripts/portal_consumer_check.py
python scripts/config_readiness_check.py
python scripts/portal_readiness_check.py
```

8010 示例：

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8010"
python scripts/portal_consumer_check.py
```

## Server Readiness Checklist

- [ ] `DATABASE_URL` 设置正确且可达
- [ ] `SECRET_KEY` 已设置（非 dev 默认值）
- [ ] `PUBLIC_BASE_URL` 设置为对外 HTTPS 域名
- [ ] CORS / reverse proxy 规划（nginx / IIS / cloud LB）
- [ ] `GET /health` → status ok
- [ ] `GET /api/v1/system/readiness` → ok
- [ ] `GET /api/v1/portal/manifest` → envelope ok
- [ ] `GET /api/v1/portal/summary` → lead_intelligence counts
- [ ] `GET /api/v1/portal/a-domain/status` → manual_outreach_ready true
- [ ] no secret leakage in portal responses
- [ ] automatic sending disabled
- [ ] LinkedIn / Outlook automation disabled
- [ ] `.env`、`local_data/` 不在 git 中

## Safety

- no automatic sending
- no LinkedIn scraping
- no Outlook integration
- no database writes from Portal
- no private CSV committed

## Acceptance

- [x] Portal consumer mock page works
- [x] `portal_consumer_check.py` PASS
- [x] `config_readiness_check.py` PASS (or WARN only)
- [x] no database migration
- [x] no Phase 2
