# intelliOffice D5.2.1 Demo Script

**日期**：2026-05-23  
**环境**：Backend `http://127.0.0.1:8000` · Frontend `http://127.0.0.1:5174`（Vite 端口以终端为准）  
**凭据**：默认 seed admin 凭据（勿在演示材料中明文展示密码）

---

## Demo Goal

展示 intelliOffice 如何帮助办公家具 / 升降系统业务识别客户、补充公开信息、生成下一步动作。

---

## Demo Flow

1. 打开 **http://127.0.0.1:5174/login**，登录系统
2. 进入 **Companies**（`/companies`）
3. 打开 **Ergo Sit Stand Workspace** 公司详情
4. 查看联系人与公司业务描述 / 意向标签
5. 在 **Enrichment Panel** 查看最近 run、点击「审阅建议与证据」
6. 查看 **sources / evidence** 与 **suggestions**
7. **Accept** 一条 pending suggestion（或展示已 accept 记录）
8. 进入 **Lead Intelligence**（`/lead-intelligence`）
9. 选择 **UAT Lead — Ergo Sit Stand Workspace**
10. 查看 **lead score**、**market_fit_segments**（如 `lift_system_signal`）
11. 查看 **recommended next actions** 与当前 **Next Action**
12. （可选）打开 **Healthcare Lab Workspace** lead，展示 **`medical_vertical`** 分段
13. （可选）打开 **Contract Project Interiors** lead，展示 **`project_based_furniture`**
14. 添加一条 **touchpoint**，保存后 **刷新页面** 确认 persisted

---

## 推荐演示公司

| 公司 | 演示要点 |
|------|----------|
| Ergo Sit Stand Workspace | 升降信号、enrichment 结果、高分 lead |
| Healthcare Lab Workspace | `medical_vertical` 分段（D5.2.1 调参后） |
| Contract Project Interiors | `project_based_furniture` 分段 |
| New England Office Furniture Dealer | 一般办公 dealer、`general_office_furniture_only` |

---

## Business Narrative

强调：

- 该系统**不是普通 CRM**，而是面向 **升降桌架、桌腿、升降柱、教育/医疗家具** 等项目制销售的 intelligence 工作台。
- 它帮助判断客户**是否值得推进**（score + segments）。
- 它可记录**公开来源证据、审阅建议、下一步动作**。
- 后续可接入报价、样品、订单、生产与运输（当前演示范围外）。

---

## Current Limitations

- Healthcare / Contract segment 已做 **D5.2.1 小范围调参**，仍需更多真实案例验证。
- 截图归档 **PARTIAL**（核心 8 张待人工补齐，见 `screenshots/20260523/README.md`）。
- Portal 目前为只读 **manifest / readiness** API，无独立 System Health 页面。
- Redis / worker 尚未生产化接入。
- 不做 LinkedIn 自动化；Quote / Order 域不在本轮演示范围。

---

## 启动检查（演示前 2 分钟）

```powershell
# 仓库根目录
docker compose up -d db

cd backend
python scripts/check_database_config.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 新终端
cd frontend
npm run dev
```

若 8000 已占用且 `/health` 为 ok，**不要重复启动** backend。
