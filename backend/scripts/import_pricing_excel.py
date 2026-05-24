"""Import pricing Excel from local_data into product catalog (D6.2)."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from openpyxl import load_workbook

from app.core.database import SessionLocal
from app.models import (
    FxRate,
    ManufacturingPartner,
    MarginStrategyTier,
    ProductCatalog,
    ProductCostModel,
    ProductPriceTier,
)

SHEET_COST = ("cost model", "成本", "cost")
SHEET_PRICE = ("price list", "价目", "price")
SHEET_MARGIN = ("margin", "利润", "倍率")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def _dec(val) -> Decimal | None:
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _int(val) -> int | None:
    if val is None or val == "":
        return None
    try:
        return int(float(str(val).replace(",", "")))
    except (ValueError, TypeError):
        return None


def _find_sheet(wb, names: tuple[str, ...]) -> str | None:
    for ws in wb.sheetnames:
        n = _norm(ws)
        for key in names:
            if key in n:
                return ws
    return None


def _cell_value(cell):
    if cell is None:
        return None
    if hasattr(cell, "value"):
        return cell.value
    return cell


def _header_map(row) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for i, cell in enumerate(row):
        val = _cell_value(cell)
        key = _norm(val)
        if key:
            mapping[key] = i
    return mapping


def _col(headers: dict[str, int], *candidates: str) -> int | None:
    for c in candidates:
        for k, idx in headers.items():
            if c in k:
                return idx
    return None


def _partner_by_name(db, name: str) -> ManufacturingPartner | None:
    if not name:
        return None
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == name.upper()).first()
    if row:
        return row
    return (
        db.query(ManufacturingPartner)
        .filter(ManufacturingPartner.partner_name.ilike(f"%{name.strip()}%"))
        .first()
    )


def run(
    file_path: Path,
    *,
    apply: bool,
    overwrite: bool,
) -> int:
    summary = {
        "partners": {"created": 0, "updated": 0, "skipped": 0},
        "products": {"created": 0, "updated": 0, "skipped": 0},
        "cost_models": {"created": 0, "updated": 0, "skipped": 0},
        "price_tiers": {"created": 0, "updated": 0, "skipped": 0},
        "margin_tiers": {"created": 0, "updated": 0, "skipped": 0},
        "fx_rates": {"created": 0, "updated": 0, "skipped": 0},
        "warnings": [],
        "errors": [],
    }

    if not file_path.is_file():
        print(f"Excel file not found: {file_path}")
        print("Place workbook at local_data/报价模型与格式.xlsx (gitignored)")
        return 1

    wb = load_workbook(file_path, data_only=True, read_only=True)
    print(f"Available sheets: {', '.join(wb.sheetnames)}")

    db = SessionLocal()
    try:
        cost_sheet = _find_sheet(wb, SHEET_COST)
        if cost_sheet:
            ws = wb[cost_sheet]
            rows = ws.iter_rows(values_only=True)
            headers = _header_map(next(rows, ()))
            name_i = _col(headers, "product name", "product", "产品")
            mat_i = _col(headers, "material", "rmb material")
            weight_i = _col(headers, "weight")
            freight_i = _col(headers, "ocean freight", "freight unit")
            transport_i = _col(headers, "transportation", "transport")
            profit_i = _col(headers, "profit", "domestic profit")
            fob_i = _col(headers, "fob cost")
            ddp_i = _col(headers, "ddp cost")
            fx_i = _col(headers, "exchange rate", "fx")
            for row in rows:
                if not row or not name_i or not row[name_i]:
                    continue
                pname = str(row[name_i]).strip()
                sku = re.sub(r"[^A-Z0-9]+", "-", pname.upper())[:48] or "IMPORT-SKU"
                product = db.query(ProductCatalog).filter(ProductCatalog.internal_sku == sku).first()
                if product and not overwrite:
                    summary["products"]["skipped"] += 1
                    continue
                if not product:
                    partner = db.query(ManufacturingPartner).first()
                    if not partner:
                        summary["errors"].append("no partner for cost import")
                        break
                    product = ProductCatalog(
                        partner_id=partner.id,
                        internal_sku=sku,
                        product_name=pname,
                        product_category="other",
                        status="active",
                        notes="excel_import",
                    )
                    db.add(product)
                    db.flush()
                    summary["products"]["created"] += 1
                elif overwrite:
                    product.product_name = pname
                    summary["products"]["updated"] += 1

                existing_cost = (
                    db.query(ProductCostModel).filter(ProductCostModel.product_id == product.id).first()
                )
                if existing_cost and not overwrite:
                    summary["cost_models"]["skipped"] += 1
                else:
                    if existing_cost and overwrite:
                        summary["cost_models"]["updated"] += 1
                        cm = existing_cost
                    else:
                        cm = ProductCostModel(product_id=product.id, cost_currency="CNY", source="excel_import")
                        db.add(cm)
                        summary["cost_models"]["created"] += 1
                    cm.unit_material_cost = _dec(row[mat_i]) if mat_i is not None else None
                    cm.unit_weight = _dec(row[weight_i]) if weight_i is not None else None
                    cm.ocean_freight_unit_price = _dec(row[freight_i]) if freight_i is not None else None
                    cm.domestic_transport_cost = _dec(row[transport_i]) if transport_i is not None else None
                    cm.domestic_profit_rate = _dec(row[profit_i]) if profit_i is not None else None
                    cm.fob_cost_usd = _dec(row[fob_i]) if fob_i is not None else None
                    cm.ddp_cost_usd = _dec(row[ddp_i]) if ddp_i is not None else None

                if fx_i is not None and row[fx_i]:
                    rate = _dec(row[fx_i])
                    if rate:
                        today = date.today()
                        fx_row = (
                            db.query(FxRate)
                            .filter(
                                FxRate.base_currency == "USD",
                                FxRate.quote_currency == "CNY",
                                FxRate.rate_date == today,
                            )
                            .first()
                        )
                        if fx_row and overwrite:
                            fx_row.rate = rate
                            summary["fx_rates"]["updated"] += 1
                        elif not fx_row:
                            db.add(
                                FxRate(
                                    base_currency="USD",
                                    quote_currency="CNY",
                                    rate=rate,
                                    rate_date=today,
                                    source="excel_import",
                                    is_manual_override=True,
                                    created_at=datetime.now(timezone.utc),
                                )
                            )
                            summary["fx_rates"]["created"] += 1
        else:
            summary["warnings"].append("cost model sheet not found")

        price_sheet = _find_sheet(wb, SHEET_PRICE)
        if price_sheet:
            ws = wb[price_sheet]
            rows = ws.iter_rows(values_only=True)
            headers = _header_map(next(rows, ()))
            prod_i = _col(headers, "product")
            min_i = _col(headers, "minqty", "min qty", "min")
            max_i = _col(headers, "maxqty", "max qty", "max")
            fob_i = _col(headers, "fob")
            ddp_i = _col(headers, "ddp")
            fob_adj_i = _col(headers, "fob adjustment", "fob adj")
            ddp_adj_i = _col(headers, "ddp adjustment", "ddp adj")
            for row in rows:
                if not row or prod_i is None or not row[prod_i]:
                    continue
                pname = str(row[prod_i]).strip()
                sku = re.sub(r"[^A-Z0-9]+", "-", pname.upper())[:48]
                product = db.query(ProductCatalog).filter(
                    (ProductCatalog.internal_sku == sku) | (ProductCatalog.product_name.ilike(pname))
                ).first()
                if not product:
                    summary["warnings"].append(f"price tier skipped — product not found: {pname}")
                    continue
                min_q = _int(row[min_i]) if min_i is not None else 1
                max_q = _int(row[max_i]) if max_i is not None else None
                if min_q is None:
                    continue
                for inc, price_i, adj_i in (("FOB", fob_i, fob_adj_i), ("DDP", ddp_i, ddp_adj_i)):
                    if price_i is None:
                        continue
                    price = _dec(row[price_i])
                    adj = _dec(row[adj_i]) if adj_i is not None else None
                    if price is None:
                        continue
                    q = db.query(ProductPriceTier).filter(
                        ProductPriceTier.product_id == product.id,
                        ProductPriceTier.min_qty == min_q,
                        ProductPriceTier.incoterm == inc,
                    )
                    if max_q is None:
                        q = q.filter(ProductPriceTier.max_qty.is_(None))
                    else:
                        q = q.filter(ProductPriceTier.max_qty == max_q)
                    tier = q.first()
                    if tier and not overwrite:
                        summary["price_tiers"]["skipped"] += 1
                        continue
                    if tier and overwrite:
                        tier.final_unit_price = price
                        tier.adjustment_value = adj
                        summary["price_tiers"]["updated"] += 1
                    else:
                        db.add(
                            ProductPriceTier(
                                product_id=product.id,
                                min_qty=min_q,
                                max_qty=max_q,
                                incoterm=inc,
                                final_unit_price=price,
                                adjustment_value=adj,
                                currency="USD",
                                source="excel_import",
                            )
                        )
                        summary["price_tiers"]["created"] += 1
        else:
            summary["warnings"].append("price list sheet not found")

        margin_sheet = _find_sheet(wb, SHEET_MARGIN)
        if margin_sheet:
            ws = wb[margin_sheet]
            rows = ws.iter_rows(values_only=True)
            headers = _header_map(next(rows, ()))
            strat_i = _col(headers, "strategy", "strategy_code", "策略")
            min_i = _col(headers, "min")
            max_i = _col(headers, "max")
            mult_i = _col(headers, "multiplier", "倍率", "rate")
            code_map = {"引流": "traffic", "销量": "volume", "利润": "profit"}
            for row in rows:
                if strat_i is None or mult_i is None or not row[strat_i]:
                    continue
                raw = str(row[strat_i]).strip()
                code = code_map.get(raw, raw.lower())
                min_q = _int(row[min_i]) if min_i is not None else 1
                max_q = _int(row[max_i]) if max_i is not None else None
                mult = _dec(row[mult_i])
                if min_q is None or mult is None:
                    continue
                q = db.query(MarginStrategyTier).filter(
                    MarginStrategyTier.strategy_code == code,
                    MarginStrategyTier.min_qty == min_q,
                )
                if max_q is None:
                    q = q.filter(MarginStrategyTier.max_qty.is_(None))
                else:
                    q = q.filter(MarginStrategyTier.max_qty == max_q)
                if q.first() and not overwrite:
                    summary["margin_tiers"]["skipped"] += 1
                    continue
                db.add(
                    MarginStrategyTier(
                        strategy_code=code,
                        strategy_name=raw,
                        min_qty=min_q,
                        max_qty=max_q,
                        multiplier=mult,
                        notes="excel_import",
                    )
                )
                summary["margin_tiers"]["created"] += 1
        else:
            summary["warnings"].append("margin strategy sheet not found")

        if apply:
            db.commit()
            print("Import applied.")
        else:
            db.rollback()
            print("Dry-run — no database changes.")
    finally:
        db.close()
        wb.close()

    print("Excel Import Summary")
    for key, counts in summary.items():
        if key in ("warnings", "errors"):
            continue
        print(f"  {key}: {counts}")
    if summary["warnings"]:
        print("  warnings:", summary["warnings"][:10])
    if summary["errors"]:
        print("  errors:", summary["errors"])
    return 0 if not summary["errors"] else 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.apply and not args.confirm:
        print("Refusing --apply without --confirm")
        sys.exit(1)
    apply = args.apply and args.confirm
    sys.exit(run(Path(args.file), apply=apply, overwrite=args.overwrite))


if __name__ == "__main__":
    main()
