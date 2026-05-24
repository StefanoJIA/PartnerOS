"""Seed D6.2 quote catalog demo data (safe sample prices — not real customer quotes)."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal
from app.models import (
    FxRate,
    ManufacturingPartner,
    MarginStrategyTier,
    ProductCatalog,
    ProductCostModel,
    ProductPriceTier,
)

PARTNERS = (
    {"code": "HOSUN", "name": "HOSUN Lifting Systems (demo)", "type": "Lifting System Manufacturer", "city": "Shenzhen"},
    {"code": "JOOBOO", "name": "JOOBOO Education Furniture (demo)", "type": "Education Furniture Manufacturer", "city": "Chongqing"},
)

PRODUCTS = (
    {
        "partner_code": "HOSUN",
        "sku": "HOSUN-FRAME-001",
        "code": "HS-ADF-001",
        "name": "Adjustable Desk Frame (demo sample)",
        "category": "lifting_frame",
        "family": "lifting_systems",
        "attrs": {"load_capacity": "120kg", "frame_type": "dual_motor"},
    },
    {
        "partner_code": "HOSUN",
        "sku": "HOSUN-COL-001",
        "code": "HS-LC-001",
        "name": "Lifting Column (demo sample)",
        "category": "lifting_columns",
        "family": "lifting_systems",
        "attrs": {"stage_count": "2", "load_capacity": "80kg"},
    },
    {
        "partner_code": "HOSUN",
        "sku": "HOSUN-LEG-001",
        "code": "HS-DL-001",
        "name": "Desk Legs Set (demo sample)",
        "category": "desk_legs",
        "family": "lifting_systems",
        "attrs": {},
    },
    {
        "partner_code": "JOOBOO",
        "sku": "JOOBOO-DESK-001",
        "code": "JB-EDU-D001",
        "name": "Classroom Desk (demo sample)",
        "category": "education_desk",
        "family": "education",
        "attrs": {"use_case": "classroom", "student_age_group": "6-12"},
    },
    {
        "partner_code": "JOOBOO",
        "sku": "JOOBOO-CHAIR-001",
        "code": "JB-EDU-C001",
        "name": "Classroom Chair (demo sample)",
        "category": "education_chair",
        "family": "education",
        "attrs": {"use_case": "classroom"},
    },
)

TIERS = (
    (1, 49, Decimal("185.00"), Decimal("215.00")),
    (50, 99, Decimal("172.00"), Decimal("198.00")),
    (100, 299, Decimal("158.00"), Decimal("182.00")),
    (300, 499, Decimal("145.00"), Decimal("168.00")),
    (500, None, Decimal("132.00"), Decimal("155.00")),
)

MARGIN_TIERS = (
    ("traffic", "引流", 1, 49, Decimal("1.05")),
    ("traffic", "引流", 50, 99, Decimal("1.04")),
    ("volume", "销量", 1, 49, Decimal("1.12")),
    ("volume", "销量", 50, 99, Decimal("1.10")),
    ("volume", "销量", 100, None, Decimal("1.08")),
    ("profit", "利润", 1, 49, Decimal("1.18")),
    ("profit", "利润", 50, None, Decimal("1.15")),
)


def _ensure_partner(db, spec: dict, *, overwrite: bool) -> tuple[ManufacturingPartner, str]:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == spec["code"]).first()
    if row:
        if overwrite:
            row.partner_name = spec["name"]
            row.partner_type = spec["type"]
            row.city = spec["city"]
            row.default_incoterm = "FOB"
            row.default_currency = "USD"
            row.catalog_status = "active"
            return row, "updated"
        return row, "skipped"
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_name == spec["name"]).first()
    if row:
        row.partner_code = spec["code"]
        row.default_incoterm = "FOB"
        row.default_currency = "USD"
        row.catalog_status = "active"
        return row, "updated"
    row = ManufacturingPartner(
        partner_name=spec["name"],
        partner_type=spec["type"],
        country="China",
        city=spec["city"],
        partner_code=spec["code"],
        default_incoterm="FOB",
        default_currency="USD",
        catalog_status="active",
        notes="D6.2 demo seed — sample pricing only.",
    )
    db.add(row)
    db.flush()
    return row, "created"


def run(*, apply: bool, overwrite: bool) -> int:
    summary = {
        "partners": {"created": 0, "updated": 0, "skipped": 0},
        "products": {"created": 0, "updated": 0, "skipped": 0},
        "cost_models": {"created": 0, "updated": 0, "skipped": 0},
        "price_tiers": {"created": 0, "updated": 0, "skipped": 0},
        "margin_tiers": {"created": 0, "updated": 0, "skipped": 0},
        "fx_rates": {"created": 0, "updated": 0, "skipped": 0},
        "warnings": [],
    }

    db = SessionLocal()
    try:
        partner_map: dict[str, ManufacturingPartner] = {}
        for p in PARTNERS:
            partner, action = _ensure_partner(db, p, overwrite=overwrite)
            partner_map[p["code"]] = partner
            summary["partners"][action] += 1

        for prod in PRODUCTS:
            partner = partner_map[prod["partner_code"]]
            existing = db.query(ProductCatalog).filter(ProductCatalog.internal_sku == prod["sku"]).first()
            if existing and not overwrite:
                summary["products"]["skipped"] += 1
                product = existing
            elif existing and overwrite:
                existing.product_name = prod["name"]
                existing.product_category = prod["category"]
                existing.product_family = prod["family"]
                existing.attributes_json = prod["attrs"]
                existing.status = "active"
                product = existing
                summary["products"]["updated"] += 1
            else:
                product = ProductCatalog(
                    partner_id=partner.id,
                    internal_sku=prod["sku"],
                    partner_product_code=prod["code"],
                    product_name=prod["name"],
                    product_category=prod["category"],
                    product_family=prod["family"],
                    description_customer=f"Demo catalog item — {prod['name']}. Sample pricing only.",
                    status="active",
                    attributes_json=prod["attrs"],
                    notes="demo_seed — not a real customer quote price",
                )
                db.add(product)
                db.flush()
                summary["products"]["created"] += 1

            cost_exists = db.query(ProductCostModel).filter(ProductCostModel.product_id == product.id).first()
            if not cost_exists or overwrite:
                if overwrite and cost_exists:
                    db.query(ProductCostModel).filter(ProductCostModel.product_id == product.id).delete()
                db.add(
                    ProductCostModel(
                        product_id=product.id,
                        cost_currency="CNY",
                        unit_material_cost=Decimal("680.00"),
                        unit_weight=Decimal("12.5"),
                        ocean_freight_unit_price=Decimal("2.50"),
                        domestic_transport_cost=Decimal("45.00"),
                        domestic_profit_rate=Decimal("0.08"),
                        source="demo_seed",
                        notes="Sample cost — not real supplier cost",
                    )
                )
                summary["cost_models"]["updated" if cost_exists and overwrite else "created"] += 1
            else:
                summary["cost_models"]["skipped"] += 1

            for min_q, max_q, fob, ddp in TIERS:
                q = db.query(ProductPriceTier).filter(
                    ProductPriceTier.product_id == product.id,
                    ProductPriceTier.min_qty == min_q,
                    ProductPriceTier.incoterm == "FOB",
                )
                if max_q is None:
                    q = q.filter(ProductPriceTier.max_qty.is_(None))
                else:
                    q = q.filter(ProductPriceTier.max_qty == max_q)
                tier_row = q.first()
                if tier_row and not overwrite:
                    summary["price_tiers"]["skipped"] += 1
                    continue
                if tier_row and overwrite:
                    tier_row.final_unit_price = fob
                    summary["price_tiers"]["updated"] += 1
                else:
                    db.add(
                        ProductPriceTier(
                            product_id=product.id,
                            min_qty=min_q,
                            max_qty=max_q,
                            incoterm="FOB",
                            final_unit_price=fob,
                            currency="USD",
                            pricing_strategy="volume",
                            source="demo_seed",
                        )
                    )
                    db.add(
                        ProductPriceTier(
                            product_id=product.id,
                            min_qty=min_q,
                            max_qty=max_q,
                            incoterm="DDP",
                            final_unit_price=ddp,
                            currency="USD",
                            pricing_strategy="volume",
                            source="demo_seed",
                        )
                    )
                    summary["price_tiers"]["created"] += 2

        for code, name, min_q, max_q, mult in MARGIN_TIERS:
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
            if overwrite:
                db.query(MarginStrategyTier).filter(
                    MarginStrategyTier.strategy_code == code,
                    MarginStrategyTier.min_qty == min_q,
                ).delete()
            db.add(
                MarginStrategyTier(
                    strategy_code=code,
                    strategy_name=name,
                    min_qty=min_q,
                    max_qty=max_q,
                    multiplier=mult,
                    notes="demo_seed",
                )
            )
            summary["margin_tiers"]["created"] += 1

        today = date.today()
        fx = (
            db.query(FxRate)
            .filter(FxRate.base_currency == "USD", FxRate.quote_currency == "CNY", FxRate.rate_date == today)
            .first()
        )
        if fx and overwrite:
            fx.rate = Decimal("7.2000")
            fx.source = "demo_seed"
            summary["fx_rates"]["updated"] += 1
        elif not fx:
            db.add(
                FxRate(
                    base_currency="USD",
                    quote_currency="CNY",
                    rate=Decimal("7.2000"),
                    rate_date=today,
                    source="demo_seed",
                    is_manual_override=True,
                    created_at=datetime.now(timezone.utc),
                )
            )
            summary["fx_rates"]["created"] += 1
        else:
            summary["fx_rates"]["skipped"] += 1

        if apply:
            db.commit()
            print("Seed applied.")
        else:
            db.rollback()
            print("Dry-run — no database changes.")
    finally:
        db.close()

    print("D6.2 Quote Catalog Seed Summary")
    for key, counts in summary.items():
        if key == "warnings":
            continue
        print(f"  {key}: {counts}")
    if summary["warnings"]:
        print("  warnings:", summary["warnings"])
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed D6.2 quote catalog demo data")
    parser.add_argument("--dry-run", action="store_true", help="Preview only (default if no --apply)")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    apply = args.apply and args.confirm
    if args.apply and not args.confirm:
        print("Refusing --apply without --confirm")
        sys.exit(1)
    sys.exit(run(apply=apply, overwrite=args.overwrite))


if __name__ == "__main__":
    main()
