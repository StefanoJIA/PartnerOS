# D5.2.1 Demo-Ready Half Product — 验证记录

**日期**：2026-05-23  
**任务**：在不改 DB schema、不进入 Phase 2 前提下，打磨 A 域演示闭环。

---

## 演示闭环检查

| # | 步骤 | 结果 | 备注 |
|---|------|------|------|
| 1 | 打开 `/login` | **PASS** | http://127.0.0.1:5174 |
| 2 | 默认 seed admin 登录 | **PASS** | proxy + API 200 |
| 3 | Companies 列表 | **PASS** | 5 家 UAT 公司可搜到 |
| 4 | Company Detail | **PASS** | workspace + Enrichment Panel |
| 5 | 联系人可见 | **PASS** | 3/5 公司有联系人 |
| 6 | Enrichment sources/suggestions | **PASS** | Office/Ergo 有 run |
| 7 | Accept / Reject | **PASS** | `verify_enrichment_review.py` |
| 8 | Lead Intelligence workflow | **PASS** | score + segments + suggestions |
| 9 | Touchpoint / Next Action | **PASS** | 3 条 persisted |
| 10 | 刷新后 persisted | **PASS** | API 复验 |

---

## 业务规则调参（D5.2.1）

| 场景 | 调参前 | 调参后 | 是否通过 |
|------|--------|--------|----------|
| Healthcare Lab Workspace | `[]` | `['medical_vertical']` | **PASS** |
| Contract Project Interiors | `['general_office_furniture_only']` | `['project_based_furniture']` | **PASS** |
| New England Office Dealer | `general_office_furniture_only` | 不变 | **PASS** |

验证命令：`python scripts/verify_segment_tuning.py`（需 backend 加载新代码）

---

## UI Polishing

| 项 | 状态 |
|----|------|
| Enrichment status fallback | `Unknown` / `Completed` |
| Empty evidence | "No evidence collected yet." |
| Empty suggestions | "No suggestions available yet." |
| Empty segments | "No segment assigned yet." |
| Empty next action | "No next action set." |
| No enrichment run | "Run enrichment to collect public evidence." |
| `project_based_furniture` 标签 | Lead Intelligence 工作台已显示 |

---

## 截图归档

| 文件 | 状态 |
|------|------|
| 8 张核心截图 | **Manual screenshot required** |
| 路径 | `docs/records/screenshots/20260523/` |

---

## 测试

| 命令 | 结果 |
|------|------|
| `python -m pytest -q` | 68 passed, 1 skipped |
| `npm run test -- --run CompanyEnrichmentPanel.spec.ts` | 4 passed |
| `python scripts/verify_ui_data.py` | OK |
| `python scripts/verify_enrichment_review.py` | OK |

---

## 结论

**可作为 D5.2.1 demo-ready half product 使用。**

无 blocking issue；未改数据库；未进入 Phase 2。
