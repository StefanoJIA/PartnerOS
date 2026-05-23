# D5.11 Runtime & Deployment Hardening

## Goal

让 D5.x MVP 可以稳定启动、稳定检查、准备部署。

## Runtime Flow

1. 启动 Docker DB（`docker compose up -d db`）
2. 设置环境：`.\scripts\dev_env_8010.ps1` 或手动 `BACKEND_BASE_URL` / `VITE_API_PROXY_TARGET`
3. 启动 backend 8010（勿同时运行多个不同代码版本的 uvicorn）
4. 启动 frontend
5. `python scripts/dev_runtime_doctor.py`
6. `python scripts/smoke_all_d5.py`

## Port Policy

- 推荐 **8010** 为本地 backend 默认端口
- 8010 占用且 `/health` 不通 → 手动清理 stale 进程，或 fallback **8013**
- 脚本 **不会** 自动 kill 进程

## Safety

- no automatic sending
- no LinkedIn / Outlook
- no DB schema change
- no secrets committed

## Acceptance Criteria

- [x] dev_runtime_doctor PASS
- [x] smoke_all_d5 PASS
- [x] pytest PASS
- [x] vitest PASS
- [x] no sensitive files
