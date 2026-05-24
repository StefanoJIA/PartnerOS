# D6.2.1 Excel Pricing Import Alignment

## Goal

让 `import_pricing_excel.py` 对齐真实报价 Excel workbook 结构，能解析并导入 partner / product / cost / price tier / margin / FX。

## Workbook Location

```
local_data/报价模型与格式.xlsx
```

该文件 **必须** 被 gitignore，**不得** 提交到 Git。

## Safety

- workbook is gitignored
- no real Excel committed
- dry-run default（不写库）
- apply 必须 `--confirm`
- overwrite 必须 `--overwrite`
- 不创建 Quote、不自动发送

## Parser Strategy

1. **Sheet classification** — 按 sheet 名称 + header alias 评分识别 cost / price / margin / quote / calculator
2. **Header detection** — 扫描前 30 行，匹配 alias 最多的行作为 header
3. **Alias matching** — 中英文列名、符号、换行归一化后模糊匹配
4. **Quantity range** — 支持 `1-49`、`1 ~ 49`、`≥500`、`500+`、`500以上`
5. **Money parsing** — `$123.45`、`¥123.45`、`1,234.56`、`RMB 123.45`
6. **Percent parsing** — `10%`、`0.1`、`10`（profit rate 默认 10 = 10%）
7. **SKU generation** — partner_code + product slug；有型号则用 partner_product_code

## Import Targets

| Excel | DB Table |
|---|---|
| 成本表 | `product_catalog` + `product_cost_models` + `fx_rates` |
| 价目表 | `product_price_tiers` + embedded `margin_strategy_tiers` |
| 利润倍率表 | `margin_strategy_tiers` |

## Commands

```powershell
cd backend
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --dry-run
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --apply --confirm
python scripts/import_pricing_excel.py --file "../local_data/报价模型与格式.xlsx" --apply --confirm --overwrite
python scripts/d6_2_1_excel_import_check.py
```

## Acceptance Criteria

- workbook readable
- sheets / headers detected
- candidate rows > 0
- dry-run summary useful
- pytest pass
- no sensitive files committed

## Not in Scope

- Quote CRUD / PDF / send
- Quote template sheet import (Quote HOSUN / Jooboo / Summary skipped)
- DISPIMG / formula cells
