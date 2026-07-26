# Multibrand Export OS — 交付证据

**Branch:** `feat/multibrand-export-os`  
**Date:** 2026-07-26  
**MULTIBRAND_READY:** YES (local gates)

## HOSUN 保留与降级

- **保留：** 历史订单、报价、测试、HOSUN adapter/import 脚本均未删除。
- **降级：** migration `0027_partner_lifecycle` 将 `partner_code=HOSUN` 设为 `lifecycle_status=legacy`，不修改历史业务记录。
- **规则：** `partner_lifecycle.py` — legacy 可查看历史；不可默认新项目推荐；不可自动营销/demo；新报价须 manual select active partner。
- **Demo 默认：** `LIFT-DEMO` 通用升降 active fixture 取代 HOSUN 作为默认演示 partner。

## 新模型与迁移

| Migration | 内容 |
|-----------|------|
| 0027 | `lifecycle_status`, `lifecycle_notes` on `manufacturing_partners` |
| 0028 | `benchmark_brands`, `benchmark_product_capabilities`, `benchmark_source_references`, `benchmark_data_rights` |
| 0029 | `supplier_discovery_records` |
| 0030 | `project_request_supplier_candidates` |
| 0031 | `platform_benchmark_records`, `channel_intelligence_metrics` |

## Benchmark vs Partner 隔离

- Benchmark 表独立 schema，含 `relationship_disclaimer`、data rights（禁止 logo/catalog/price 复制）。
- API `/benchmark-brands` 与 `/manufacturing-partners` 分离。
- 候选 `candidate_source_type=benchmark` → `eligible_for_formal_quote=false`，测试覆盖见 `test_multibrand_export_os.py`。

## 首批行业 Benchmark（seed）

- **升降：** LINAK, JIECANG, TiMOTION, Kesseböhmer — load/speed/stroke/IP/controller 等字段，标记 fact/inferred/pending_verification。
- **合同办公 / 教育：** taxonomy benchmark 品牌各一组 capability 字段。
- Seed: `python scripts/seed_benchmark_taxonomy.py`

## 供应商资质流程

- 状态流：discovered → contacted → evaluating → sample_requested → qualified → active / rejected / paused
- Admin UI: `/admin/supplier-discovery`
- **无** 自动联系、承诺或激活

## 多供应商 Demo 路径

1. 项目需求 (`/admin/project-requests`)
2. 刷新多供应商候选比对
3. 选择 active partner 候选 → QIC → 区间报价/PDF
4. Demo 场景：LIFT-DEMO active / JOOBOO candidate / contract office benchmark / HOSUN legacy

## 平台能力矩阵

- `/admin/platform-intelligence` — Alibaba, Thomasnet, Shopify B2B, Zoho CRM vs PartnerOS
- 渠道指标：direct, referral, trade_show, website, manual（manual/import only）

## PartnerOS 差异化优先级

| 优先级 | 能力 |
|--------|------|
| **P0** | CPR → 多供应商比对 → QIC → 区间报价/PDF → 生产/物流闭环 |
| **P1** | 供应商发现工作台、平台 gap 矩阵、渠道情报 |
| **P2** | Benchmark 知识库深化、Thomasnet/Alibaba 对齐 |

## 测试与 Gate

```powershell
cd backend
python -m pytest tests/test_multibrand_export_os.py tests/test_customer_project_requests.py -q
python scripts/multibrand_export_os_check.py
```

## 逻辑 Commits

1. partner lifecycle / de-HOSUN
2. benchmark knowledge model + seed
3. supplier discovery
4. multi-supplier fit
5. platform benchmark / channel intelligence
6. UI/demo/tests/docs
