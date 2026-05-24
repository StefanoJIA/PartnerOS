# D6.2 Product Catalog & Pricing Foundation

**Status:** Implemented · **Date:** 2026-05-23  
**Phase:** 2 · **Not in scope:** Quote CRUD, PDF, send, order conversion

## Goal

建立产品目录、成本模型、价格阶梯、汇率与 **pricing preview**，为 Quote MVP（D6.3）做准备。

## Scope

- `manufacturing_partners` 扩展（partner_code, default_incoterm/currency, catalog_status）
- `product_catalog`, `product_cost_models`, `product_price_tiers`, `margin_strategy_tiers`, `fx_rates`
- Pricing service + `POST /api/v1/quotes/pricing/preview`
- Catalog API `GET/POST/PATCH /api/v1/products`
- FX API `GET/POST /api/v1/fx-rates`
- Seed: `seed_quote_catalog.py`
- Excel import: `import_pricing_excel.py`（local_data only）
- Frontend: `/quote-catalog`, `/pricing-preview`

## Not in Scope

- Quote CRUD / quote_versions / quote_line_items tables
- Quote PDF export
- Mark sent / convert to order
- Automatic sending

## Pricing Safety

- no AI pricing
- no quote creation (`quote_created: false`)
- no inventory / certification / lead-time promise
- RMB cost requires FX rate — no fabricated rates

## Excel Model Mapping

| Excel | Table |
|---|---|
| 成本表 | `product_cost_models` |
| 价目表 | `product_price_tiers` |
| 利润倍率 | `margin_strategy_tiers` |
| 汇率 | `fx_rates` |
| 利润计算器 | pricing preview API |

## Excel Import

```powershell
cd backend
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --dry-run
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --apply --confirm
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --apply --confirm --overwrite
```

File must stay in `local_data/` (gitignored). Never commit Excel.

## Seed

```powershell
python scripts/seed_quote_catalog.py --dry-run
python scripts/seed_quote_catalog.py --apply --confirm
```

## Smoke

```powershell
python scripts/d6_2_pricing_foundation_check.py
```

## Acceptance Criteria

- [x] Migration `0006_product_catalog_pricing` applies
- [x] Seed works
- [x] Pricing preview works
- [x] `d6_2_pricing_foundation_check.py` PASS
- [x] pytest / vitest pass

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/products` | List catalog |
| GET | `/api/v1/products/{id}` | Product detail |
| POST | `/api/v1/products` | Create catalog item |
| PATCH | `/api/v1/products/{id}` | Update |
| GET | `/api/v1/fx-rates/latest` | Latest USD/CNY |
| POST | `/api/v1/fx-rates` | Manual FX entry |
| POST | `/api/v1/quotes/pricing/preview` | Pricing preview only |

## Related

- [D6.1 Design Review](d6_1_quote_schema_api_design_review.md)
- [Phase 2 Roadmap](phase2_roadmap.md)
