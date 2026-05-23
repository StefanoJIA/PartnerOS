# D5.2.2 Internal MVP — 2026-05-23

**阶段**：D5.2.2 Internal MVP Stabilization（非 Phase 2）  
**环境**：Backend `http://127.0.0.1:8000` · Frontend 以 Vite 终端为准（常见 `5173` 或 `5174`）  
**凭据**：默认 seed admin 账号（邮箱见 Login 页提示；**勿在文档或截图中明文展示密码**）

---

## 当前状态

| 项 | 状态 |
|----|------|
| 后端 `/health` | 可用（development 下 DB ready 时为 `ok`） |
| v1 readiness / manifest | 只读 API 可用 |
| 前端登录 | `/login` 可访问 |
| A 域全链路 | Company → Contact → Lead Intelligence → Enrichment → Touchpoint |
| 数据库 schema | **未变更**（无新 migration） |
| Phase 2 / CRM v1 façade | **未进入** |

---

## 可用功能（内部 MVP）

- **Dashboard**：今日动作 + **System Status / Portal Readiness** 卡片
- **System health**（`/system-health`）：只读聚合 `/health`、`/api/v1/system/readiness`、`/api/v1/portal/manifest`
- **Companies / Contacts**：UAT 测试公司与联系人
- **Lead Intelligence**：评分、segment、建议 next actions、touchpoint
- **Enrichment Panel**：公开来源抓取、证据、Accept/Reject 审阅
- **Smoke 脚本**：`backend/scripts/smoke_demo_ready.py`（只读，需 backend 运行）

---

## 登录方式

1. 确保 Docker DB（端口 **5435**）与 backend、frontend 已启动 — 见 [dev_guide.md](../dev_guide.md)
2. 浏览器打开 `http://127.0.0.1:5174/login`（或终端显示的端口）
3. 使用 seed 创建的 admin 账号登录（与 `python -m app.scripts.seed` 一致）

---

## 演示路径

完整脚本见 [demo_script_20260523.md](demo_script_20260523.md)。推荐顺序：

1. Login → Dashboard（查看 System Status 卡片）
2. `/system-health` 详情页（可选）
3. `/companies` → **Ergo Sit Stand Workspace** 详情 → Enrichment Panel
4. `/lead-intelligence` → Ergo / Healthcare / Contract 三条 workflow
5. Touchpoint / Next Action 保存并刷新验证

Segment 展示（UI 英文标签）：

| API key | 展示文案 |
|---------|----------|
| `lift_system_signal` | Lifting System Signal |
| `medical_vertical` | Medical / Healthcare Vertical |
| `project_based_furniture` | Project-Based Furniture |
| `general_office_furniture_only` | General Office Furniture |
| `education_vertical` | Education Vertical |

---

## 系统健康路径

| 用途 | URL |
|------|-----|
| Legacy health | `GET http://127.0.0.1:8000/health` |
| Readiness | `GET http://127.0.0.1:8000/api/v1/system/readiness` |
| Portal manifest | `GET http://127.0.0.1:8000/api/v1/portal/manifest` |
| 前端只读页 | `/system-health` 或 Dashboard 卡片 |

**说明**：`redis_ready` / `worker_ready` 为 false 时属 **optional warning**，非 blocking。

---

## 自动化检查

```powershell
cd backend
python scripts/check_database_config.py
python -m pytest -q
python scripts/smoke_demo_ready.py
```

Smoke 脚本 **需要 backend 已在 :8000 运行**。缺 demo 数据时提示运行 seed 或 UAT，不会自动写库。

---

## 已知限制

- 未接 Redis / worker；readiness 中相关项为 optional off
- 无 Phase 2 Portal 写操作；manifest 为只读展示
- 截图需人工补齐（见 [screenshots/20260523/README.md](screenshots/20260523/README.md)）
- 未初始化生产部署；Ubuntu 部署不在本轮范围
- 旧 `/api/*` 契约与 DB schema 保持不变

---

## 下一步建议（非本轮）

- 人工补全打码截图并归档
- 首次 `git commit`（见 D5.2.2 报告建议 message）
- Portal / Phase 2 前：CRM v1 façade 设计与路由规划（单独里程碑）
- 桌面 sidecar 打包验证（D3 路径）

---

## 相关文档

- [dev_guide.md](../dev_guide.md) — Windows 本地启动
- [testing.md](../testing.md) — pytest / smoke / 手工 check 顺序
- [demo_ready_half_product_20260523.md](demo_ready_half_product_20260523.md) — D5.2.1 收口
- [demo_script_20260523.md](demo_script_20260523.md) — 演示脚本
