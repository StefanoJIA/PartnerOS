# D5.2.3 Internal Pilot Workflow

**Date**: 2026-05-23  
**Stage**: Internal lead development pilot (not Phase 2)

---

## Goal

把 intelliOffice 用于真实客户开发试运行 — 办公家具、升降桌架/桌腿/升降柱、教育家具、医疗家具、项目制客户与 OEM/ODM 潜客跟进。

---

## Recommended Daily Workflow

1. **新增客户公司** — `/companies`（或参考 CSV 模板手工录入）
2. **新增联系人** — `/contacts`，设为主联系人
3. **填写 website / notes / source** — notes 中写清升降、项目、医疗、教育关键词
4. **查看 Lead Intelligence** — `/lead-intelligence`
5. **查看 segment 与 score** — Lead Review 表 + 详情卡片
6. **运行 enrichment** — 公司详情 Enrichment Panel（需 website）
7. **接受或拒绝建议** — Accept/Reject 审阅
8. **设置 next action** — 工作台右侧表单或快捷建议
9. **记录 touchpoint** — 保存后刷新确认 persisted
10. **每日查看需要跟进的 lead** — Review 表按分数排序 + segment 筛选

---

## Business Use Cases

| 场景 | 关注 segment | 示例动作 |
|------|--------------|----------|
| HOSUN adjustable desk frame lead | Lifting System Signal | 发 frame 规格、MOQ、交期 |
| JOOBOO education furniture lead | Education Vertical | 校园 RFP、批量报价路径 |
| Healthcare / lab workstation lead | Medical / Healthcare Vertical | 合规与医疗场景产品线 |
| Contract furniture project lead | Project-Based Furniture | BOQ、分阶段交付 |
| OEM / ODM potential partner | OEM / ODM Signal (`oem_odm_fit`) | 工程对接、私模路径 |
| General office dealer | General Office Furniture | 轻维护 + enrichment 补信号 |

**Import template**: [templates/lead_import_template.csv](../templates/lead_import_template.csv) · [templates/lead_import_template.md](../templates/lead_import_template.md)

---

## System health (unchanged)

- Dashboard **System Status** 卡片
- `/system-health` 只读页
- `redis_ready` / `worker_ready` false = **optional warning**，非 fatal

---

## Automation checks

```powershell
cd backend
python scripts/smoke_demo_ready.py
python scripts/pilot_workflow_check.py
```

Backend must be running on `:8000`.

---

## Current Limitations

- 暂无 Outlook 自动同步
- 暂无 LinkedIn 自动化
- 暂无完整报价模块接入 Lead 闭环
- 暂无 production / shipment 联动
- Redis / worker 尚未生产化接入
- CSV 模板为手工录入指南（无 bulk import API）

---

## Acceptance Criteria

- [x] 可录入真实 lead（Companies / Contacts / Leads）
- [x] 可识别 segment（Lead Intelligence + 筛选）
- [x] 可运行 enrichment
- [x] 可记录 next action & touchpoint
- [x] 可作为每日客户跟进台账使用（Review 表 + next action）

---

## Related docs

- [demo_script_20260523.md](demo_script_20260523.md)
- [d5_2_2_internal_mvp_20260523.md](d5_2_2_internal_mvp_20260523.md)
- [lead_intelligence_scoring_notes.md](../lead_intelligence_scoring_notes.md)
