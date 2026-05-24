"""Import pricing Excel from local_data into product catalog (D6.2 / D6.2.1)."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
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
from app.services.quotes.pricing_excel_parser import (
    ParsedCostRow,
    ParsedMarginRow,
    ParsedPriceRow,
    SheetParseReport,
    format_sheet_debug,
    load_sheet_rows,
    parse_workbook_sheet,
)

DEFAULT_PARTNERS = (
    {"code": "HOSUN", "name": "HOSUN Lifting Systems", "type": "Lifting System Manufacturer"},
    {"code": "JOOBOO", "name": "JOOBOO Education Furniture", "type": "Education Furniture Manufacturer"},
    {"code": "CHONGQING_HUIJU", "name": "Chongqing Huiju", "type": "Manufacturing Partner"},
    {"code": "OTHER", "name": "Other Partner", "type": "Manufacturing Partner"},
)


def _ensure_partner(db, code: str, *, overwrite: bool) -> tuple[ManufacturingPartner, str]:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == code).first()
    if row:
        return row, "skipped"
    spec = next((p for p in DEFAULT_PARTNERS if p["code"] == code), None)
    name = spec["name"] if spec else f"{code} Partner"
    ptype = spec["type"] if spec else "Manufacturing Partner"
    row = ManufacturingPartner(
        partner_name=name,
        partner_type=ptype,
        country="China",
        partner_code=code,
        default_incoterm="FOB",
        default_currency="USD",
        catalog_status="active",
        notes="excel_import",
    )
    db.add(row)
    db.flush()
    return row, "created"


def _find_product(db, *, sku: str | None, name: str, partner_id) -> ProductCatalog | None:
    if sku:
        hit = db.query(ProductCatalog).filter(ProductCatalog.internal_sku == sku).first()
        if hit:
            return hit
    return (
        db.query(ProductCatalog)
        .filter(ProductCatalog.partner_id == partner_id, ProductCatalog.product_name.ilike(name.strip()))
        .first()
    )


def _upsert_product(
    db,
    *,
    row: ParsedCostRow | ParsedPriceRow,
    partner: ManufacturingPartner,
    overwrite: bool,
    summary: dict,
    sku: str | None = None,
) -> ProductCatalog | None:
    name = row.product_name
    internal_sku = sku or getattr(row, "internal_sku", None)
    if not internal_sku:
        from app.services.quotes.pricing_excel_parser import generate_internal_sku

        partner_code = getattr(row, "partner_code", None) or partner.partner_code or "OTHER"
        internal_sku = generate_internal_sku(name, partner_code=partner_code)

    existing = _find_product(db, sku=internal_sku, name=name, partner_id=partner.id)
    partner_code = getattr(row, "partner_product_code", None)
    if existing and not overwrite:
        summary["products"]["skipped"] += 1
        return existing
    if existing and overwrite:
        existing.product_name = name
        if partner_code:
            existing.partner_product_code = partner_code
        existing.notes = "excel_import"
        summary["products"]["updated"] += 1
        return existing
    product = ProductCatalog(
        partner_id=partner.id,
        internal_sku=internal_sku,
        partner_product_code=partner_code,
        product_name=name,
        product_category="other",
        status="active",
        base_currency="USD",
        default_incoterm="FOB",
        notes="excel_import",
    )
    db.add(product)
    db.flush()
    summary["products"]["created"] += 1
    return product


def _import_cost_row(
    db,
    row: ParsedCostRow,
    *,
    meta,
    overwrite: bool,
    summary: dict,
    partners: dict[str, ManufacturingPartner],
) -> None:
    partner = partners.get(row.partner_code) or partners.get("OTHER")
    if not partner:
        summary["errors"].append(f"no partner for {row.product_name}")
        return
    product = _upsert_product(db, row=row, partner=partner, overwrite=overwrite, summary=summary, sku=row.internal_sku)
    if not product:
        return
    existing = db.query(ProductCostModel).filter(ProductCostModel.product_id == product.id).first()
    if existing and not overwrite:
        summary["cost_models"]["skipped"] += 1
        return
    if existing and overwrite:
        cm = existing
        summary["cost_models"]["updated"] += 1
    else:
        cm = ProductCostModel(product_id=product.id, cost_currency="CNY", source="excel_import")
        db.add(cm)
        summary["cost_models"]["created"] += 1
    cm.unit_material_cost = row.material_cost
    cm.unit_weight = row.weight
    cm.domestic_transport_cost = row.domestic_transport
    cm.ocean_freight_unit_price = meta.ocean_freight_unit
    cm.domestic_profit_rate = meta.domestic_profit_rate
    cm.fob_cost_usd = row.fob_cost_usd
    cm.ddp_cost_usd = row.ddp_cost_usd


def _import_price_row(
    db,
    row: ParsedPriceRow,
    *,
    overwrite: bool,
    summary: dict,
    partners: dict[str, ManufacturingPartner],
    product_cache: dict[str, ProductCatalog],
) -> None:
    partner_code = row.partner_code or "OTHER"
    partner = partners.get(partner_code) or partners.get("OTHER")
    if not partner:
        summary["warnings"].append(f"price tier skipped — no partner: {row.product_name}")
        return
    cache_key = f"{partner.id}:{row.product_name.lower()}"
    product = product_cache.get(cache_key)
    if not product:
        product = _find_product(db, sku=None, name=row.product_name, partner_id=partner.id)
    if not product:
        from app.services.quotes.pricing_excel_parser import generate_internal_sku

        sku = generate_internal_sku(row.product_name, partner_code=partner_code)
        product = _upsert_product(db, row=row, partner=partner, overwrite=overwrite, summary=summary, sku=sku)
    if not product:
        summary["warnings"].append(f"price tier skipped — product not found: {row.product_name}")
        return
    product_cache[cache_key] = product

    for inc, price, adj in (
        ("FOB", row.fob, row.fob_adjustment),
        ("DDP", row.ddp, row.ddp_adjustment),
    ):
        if price is None:
            continue
        q = db.query(ProductPriceTier).filter(
            ProductPriceTier.product_id == product.id,
            ProductPriceTier.min_qty == row.min_qty,
            ProductPriceTier.incoterm == inc,
        )
        if row.max_qty is None:
            q = q.filter(ProductPriceTier.max_qty.is_(None))
        else:
            q = q.filter(ProductPriceTier.max_qty == row.max_qty)
        tier = q.first()
        if tier and not overwrite:
            summary["price_tiers"]["skipped"] += 1
            continue
        if tier and overwrite:
            tier.final_unit_price = price
            tier.adjustment_value = adj
            tier.pricing_strategy = row.pricing_strategy
            summary["price_tiers"]["updated"] += 1
        else:
            db.add(
                ProductPriceTier(
                    product_id=product.id,
                    min_qty=row.min_qty,
                    max_qty=row.max_qty,
                    incoterm=inc,
                    final_unit_price=price,
                    adjustment_value=adj,
                    currency="USD",
                    pricing_strategy=row.pricing_strategy,
                    source="excel_import",
                )
            )
            summary["price_tiers"]["created"] += 1


def _import_margin_row(db, row: ParsedMarginRow, *, overwrite: bool, summary: dict) -> None:
    q = db.query(MarginStrategyTier).filter(
        MarginStrategyTier.strategy_code == row.strategy_code,
        MarginStrategyTier.min_qty == row.min_qty,
    )
    if row.max_qty is None:
        q = q.filter(MarginStrategyTier.max_qty.is_(None))
    else:
        q = q.filter(MarginStrategyTier.max_qty == row.max_qty)
    existing = q.first()
    if existing and not overwrite:
        summary["margin_tiers"]["skipped"] += 1
        return
    if existing and overwrite:
        existing.multiplier = row.multiplier
        existing.strategy_name = row.strategy_name
        existing.notes = "excel_import"
        summary["margin_tiers"]["updated"] += 1
        return
    db.add(
        MarginStrategyTier(
            strategy_code=row.strategy_code,
            strategy_name=row.strategy_name,
            min_qty=row.min_qty,
            max_qty=row.max_qty,
            multiplier=row.multiplier,
            notes="excel_import",
        )
    )
    summary["margin_tiers"]["created"] += 1


def _import_fx(db, rate: Decimal | None, *, overwrite: bool, summary: dict) -> None:
    if rate is None:
        return
    today = date.today()
    fx_row = (
        db.query(FxRate)
        .filter(FxRate.base_currency == "USD", FxRate.quote_currency == "CNY", FxRate.rate_date == today)
        .first()
    )
    if fx_row and overwrite:
        fx_row.rate = rate
        fx_row.source = "excel_import"
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
        summary["fx_rates"]["skipped"] += 1


def _apply_sheet_report(
    db,
    report: SheetParseReport,
    *,
    overwrite: bool,
    summary: dict,
    partners: dict[str, ManufacturingPartner],
    product_cache: dict[str, ProductCatalog],
) -> None:
    if report.detected_type == "cost_model":
        if report.meta.fx_rate:
            _import_fx(db, report.meta.fx_rate, overwrite=overwrite, summary=summary)
        for row in report.cost_rows:
            _import_cost_row(db, row, meta=report.meta, overwrite=overwrite, summary=summary, partners=partners)
    elif report.detected_type == "price_tier":
        for row in report.price_rows:
            _import_price_row(
                db, row, overwrite=overwrite, summary=summary, partners=partners, product_cache=product_cache
            )
        for row in report.margin_rows:
            _import_margin_row(db, row, overwrite=overwrite, summary=summary)
    elif report.detected_type == "margin_strategy":
        for row in report.margin_rows:
            _import_margin_row(db, row, overwrite=overwrite, summary=summary)


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
    sheet_reports: list[SheetParseReport] = []
    total_candidates = 0

    if not file_path.is_file():
        print(f"Excel file not found: {file_path}")
        print("Place workbook at local_data/报价模型与格式.xlsx (gitignored)")
        return 1

    print(f"Workbook: {file_path.resolve()}")
    wb = load_workbook(file_path, data_only=True, read_only=True)
    print(f"Available sheets: {', '.join(wb.sheetnames)}")

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = load_sheet_rows(ws)
        report = parse_workbook_sheet(sheet_name, rows)
        sheet_reports.append(report)
        total_candidates += report.candidate_rows
        summary["warnings"].extend(report.warnings)
        print()
        print(format_sheet_debug(report))

    db = SessionLocal()
    try:
        partners: dict[str, ManufacturingPartner] = {}
        partner_codes = {"OTHER"}
        for report in sheet_reports:
            for row in report.cost_rows:
                partner_codes.add(row.partner_code)
            for row in report.price_rows:
                if row.partner_code:
                    partner_codes.add(row.partner_code)

        for code in sorted(partner_codes):
            partner, action = _ensure_partner(db, code, overwrite=overwrite)
            partners[code] = partner
            summary["partners"][action] += 1

        product_cache: dict[str, ProductCatalog] = {}
        for report in sheet_reports:
            _apply_sheet_report(
                db, report, overwrite=overwrite, summary=summary, partners=partners, product_cache=product_cache
            )

        if apply:
            db.commit()
            print("\nImport applied.")
        else:
            db.rollback()
            print("\nDry-run — no database changes.")
    finally:
        db.close()
        wb.close()

    print("\nExcel Import Summary")
    print(f"  total candidate rows: {total_candidates}")
    for key, counts in summary.items():
        if key in ("warnings", "errors"):
            continue
        print(f"  {key}: {counts}")
    if summary["warnings"]:
        print(f"  warnings ({len(summary['warnings'])}):", summary["warnings"][:15])
    if summary["errors"]:
        print("  errors:", summary["errors"])
    return 0 if not summary["errors"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Import pricing Excel into D6.2 catalog tables")
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
