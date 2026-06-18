"""Backfill HOSUN cost and interval price mappings into catalog products.

The pricing workbook has cost rows keyed by commercial product names, while the
HOSUN catalog import has model-keyed IntelliOpus SKUs. This script links those
sources without exposing cost fields to customer-facing APIs.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models import ProductCatalog, ProductCostModel, ProductPriceTier


@dataclass(frozen=True)
class CostMapping:
    source_name: str
    target_skus: tuple[str, ...] = ()
    target_names: tuple[str, ...] = ()
    price_source_names: tuple[str, ...] = ()
    copy_price_tiers: bool = True
    copy_cost_model: bool = True


HOSUN_COST_MAPPINGS: tuple[CostMapping, ...] = (
    CostMapping(
        source_name="3-Leg 3-Stage Triple-Motor Rectangular Desk Frame 90x60mm",
        target_skus=("IO-HOSUN-LS-HS80503PRTDFZ", "IO-HOSUN-LS-HS70703PRTDFZ"),
    ),
    CostMapping(
        source_name="2-Stage Dual-Motor Rectangular Desk Frame 90x60mm 300kg Capacity",
        target_skus=("IO-HOSUN-HD-HS90602HRDDFZ",),
        target_names=("2-Stage Dual-Motor Rectangular 3.54''×2.36'' Heavy Duty Desk Frame",),
        price_source_names=("2-Stage Dual-Motor Rectangular 3.54''×2.36'' Heavy Duty Desk Frame",),
    ),
    CostMapping(
        source_name="3-Stage Dual-Motor Rectangular Desk Frame 90x60mm",
        target_skus=("IO-HOSUN-DF-HS90603PRDDFZ",),
        target_names=("3-Stage Dual-Motor Rectangular 3.54''×2.36'' Desk Frame",),
    ),
    CostMapping(
        source_name="3-Stage Dual-Motor Rectangular Desk Frame 80x50mm / 70x70mm",
        target_skus=("IO-HOSUN-DF-HS80503PRDDFZ", "IO-HOSUN-DF-HS70703PRDDFZ"),
        target_names=("3-Stage Dual-Motor Rectangular 3.15''×1.97'' / Square 2.76'' Desk Frame",),
    ),
    CostMapping(
        source_name="2-Stage Dual-Motor Rectangular Desk Frame 90x60mm",
        target_skus=("IO-HOSUN-DF-HS90602PRDDFZ",),
    ),
    CostMapping(
        source_name="2-Stage Dual-Motor Rectangular Desk Frame 80x50mm / 70x70mm",
        target_skus=("IO-HOSUN-DF-HS80502PRDDFZ", "IO-HOSUN-DF-HS70702PRDDFZ"),
        target_names=("2-Stage Dual-Motor Rectangular 3.15''×1.97'' / Square 2.76'' Desk Frame",),
        price_source_names=("2-Stage Dual-Motor Rectangular 3.15''×1.97'' / Square 2.76'' Desk Frame",),
    ),
    CostMapping(
        source_name="2-Stage Dual-Motor Round Desk Frame ⌀ 70",
        target_skus=("IO-HOSUN-DF-HS00702PRDDFZ",),
    ),
    CostMapping(
        source_name="2-Stage Single-Motor Rectangular Desk Frame 80x50mm",
        target_skus=("IO-HOSUN-DF-HS80502PRSDFZ",),
    ),
    CostMapping(
        source_name="2-Stage Single-Motor Round Desk Frame ⌀ 70",
        target_skus=("IO-HOSUN-DF-HS00702PRSDFZ",),
    ),
    CostMapping(
        source_name="2-Stage Four-Motor Face-to-Face Rectangular Benching Frame 80x50mm / 70x70mm",
        target_skus=("IO-HOSUN-BF-HS80502PRCWSZ", "IO-HOSUN-BF-HS70702PRCWSZ"),
        target_names=("2-Stage Four-Motor Face-to-Face Rectangular 3.15''×1.97'' / Square 2.76'' Benching Frame",),
    ),
    CostMapping(
        source_name="3-Stage Four-Motor Face-to-Face Rectangular Benching Frame 80x50mm / 70x70mm",
        target_skus=("IO-HOSUN-BF-HS80503PRCWSZ", "IO-HOSUN-BF-HS70703PRCWSZ"),
        target_names=("3-Stage Four-Motor Face-to-Face Rectangular 3.15''×1.97'' / Square 2.76'' Benching Frame",),
    ),
)


def _find_product_by_name(
    db,
    name: str,
    *,
    require_cost: bool = False,
    require_tiers: bool = False,
) -> ProductCatalog | None:
    rows = db.query(ProductCatalog).filter(ProductCatalog.product_name.ilike(name.strip())).all()
    if not rows:
        return None

    def _score(row: ProductCatalog) -> tuple[int, int, int]:
        cost_count = db.query(ProductCostModel).filter(ProductCostModel.product_id == row.id).count()
        tier_count = db.query(ProductPriceTier).filter(ProductPriceTier.product_id == row.id).count()
        if require_cost and not cost_count:
            return (-1, -1, -1)
        if require_tiers and not tier_count:
            return (-1, -1, -1)
        source_rank = 1 if row.internal_sku.startswith("HOSUN-") else 0
        return (tier_count if require_tiers else cost_count, source_rank, tier_count)

    ranked = sorted(((row, _score(row)) for row in rows), key=lambda item: item[1], reverse=True)
    best, score = ranked[0]
    if score[0] < 0:
        return None
    return best


def _find_targets(db, mapping: CostMapping) -> list[ProductCatalog]:
    targets: list[ProductCatalog] = []
    seen: set[str] = set()
    for sku in mapping.target_skus:
        row = db.query(ProductCatalog).filter(ProductCatalog.internal_sku == sku).first()
        if row and str(row.id) not in seen:
            targets.append(row)
            seen.add(str(row.id))
    for name in mapping.target_names:
        row = _find_product_by_name(db, name)
        if row and str(row.id) not in seen:
            targets.append(row)
            seen.add(str(row.id))
    return targets


def _latest_cost(db, product_id) -> ProductCostModel | None:
    return (
        db.query(ProductCostModel)
        .filter(ProductCostModel.product_id == product_id)
        .order_by(ProductCostModel.effective_from.desc().nullslast(), ProductCostModel.created_at.desc())
        .first()
    )


def _find_price_source(db, mapping: CostMapping, fallback: ProductCatalog) -> ProductCatalog | None:
    for name in mapping.price_source_names:
        row = _find_product_by_name(db, name, require_tiers=True)
        if row:
            return row
    row = _find_product_by_name(db, mapping.source_name, require_tiers=True)
    return row or fallback


def _copy_cost(db, *, source: ProductCatalog, target: ProductCatalog, overwrite: bool) -> str:
    source_cost = _latest_cost(db, source.id)
    if not source_cost:
        return "source_cost_missing"
    existing = _latest_cost(db, target.id)
    if existing and not overwrite:
        return "skipped_existing"
    row = existing or ProductCostModel(product_id=target.id, cost_currency=source_cost.cost_currency)
    if not existing:
        db.add(row)
    row.cost_currency = source_cost.cost_currency
    row.unit_material_cost = source_cost.unit_material_cost
    row.unit_weight = source_cost.unit_weight
    row.ocean_freight_unit_price = source_cost.ocean_freight_unit_price
    row.domestic_transport_cost = source_cost.domestic_transport_cost
    row.domestic_profit_rate = source_cost.domestic_profit_rate
    row.fob_cost_usd = source_cost.fob_cost_usd
    row.ddp_cost_usd = source_cost.ddp_cost_usd
    row.effective_from = source_cost.effective_from
    row.effective_to = source_cost.effective_to
    row.source = "hosun_cost_mapping"
    row.notes = f"Mapped from cost workbook product: {source.product_name}. Internal-only cost model."
    return "updated" if existing else "created"


def _copy_price_tiers(db, *, source: ProductCatalog, target: ProductCatalog, overwrite: bool) -> dict[str, int]:
    counts = {"created": 0, "updated": 0, "skipped": 0}
    source_rows = db.query(ProductPriceTier).filter(ProductPriceTier.product_id == source.id).all()
    for source_tier in source_rows:
        query = db.query(ProductPriceTier).filter(
            ProductPriceTier.product_id == target.id,
            ProductPriceTier.min_qty == source_tier.min_qty,
            ProductPriceTier.incoterm == source_tier.incoterm,
        )
        if source_tier.max_qty is None:
            query = query.filter(ProductPriceTier.max_qty.is_(None))
        else:
            query = query.filter(ProductPriceTier.max_qty == source_tier.max_qty)
        tier = query.first()
        if tier and not overwrite:
            counts["skipped"] += 1
            continue
        if not tier:
            tier = ProductPriceTier(product_id=target.id, min_qty=source_tier.min_qty, incoterm=source_tier.incoterm)
            db.add(tier)
            counts["created"] += 1
        else:
            counts["updated"] += 1
        tier.max_qty = source_tier.max_qty
        tier.base_unit_price = source_tier.base_unit_price
        tier.adjustment_value = source_tier.adjustment_value
        tier.final_unit_price = source_tier.final_unit_price
        tier.currency = source_tier.currency
        tier.pricing_strategy = source_tier.pricing_strategy
        tier.effective_from = source_tier.effective_from
        tier.effective_to = source_tier.effective_to
        tier.source = "hosun_cost_mapping"
        tier.notes = f"Mapped from quote interval product: {source.product_name}."
    return counts


def _mark_mapping(target: ProductCatalog, cost_source: ProductCatalog, price_source: ProductCatalog) -> None:
    attrs = dict(target.attributes_json or {})
    attrs.update(
        {
            "source_cost_product_name": cost_source.product_name,
            "source_price_product_name": price_source.product_name,
            "pricing_mapping_source": "hosun_cost_mapping",
            "customer_safe_pricing_mode": "full_quantity_interval_quote_table",
            "internal_only_cost_model": True,
        }
    )
    target.attributes_json = attrs


def run(*, apply: bool, overwrite: bool) -> int:
    from app.core.database import SessionLocal

    summary = {
        "source_missing": 0,
        "price_source_missing": 0,
        "target_missing": 0,
        "cost_created": 0,
        "cost_updated": 0,
        "cost_skipped": 0,
        "tiers_created": 0,
        "tiers_updated": 0,
        "tiers_skipped": 0,
        "mapped_targets": 0,
    }
    db = SessionLocal()
    try:
        for mapping in HOSUN_COST_MAPPINGS:
            source = _find_product_by_name(db, mapping.source_name, require_cost=mapping.copy_cost_model)
            if not source:
                print(f"source missing: {mapping.source_name}")
                summary["source_missing"] += 1
                continue
            price_source = _find_price_source(db, mapping, source)
            if not price_source:
                print(f"price source missing: {mapping.source_name}")
                summary["price_source_missing"] += 1
                continue
            targets = _find_targets(db, mapping)
            if not targets:
                print(f"target missing: {mapping.source_name}")
                summary["target_missing"] += 1
                continue
            for target in targets:
                if target.id == source.id:
                    continue
                if mapping.copy_cost_model:
                    result = _copy_cost(db, source=source, target=target, overwrite=overwrite)
                    if result == "created":
                        summary["cost_created"] += 1
                    elif result == "updated":
                        summary["cost_updated"] += 1
                    elif result == "skipped_existing":
                        summary["cost_skipped"] += 1
                if mapping.copy_price_tiers:
                    counts = _copy_price_tiers(db, source=price_source, target=target, overwrite=overwrite)
                    summary["tiers_created"] += counts["created"]
                    summary["tiers_updated"] += counts["updated"]
                    summary["tiers_skipped"] += counts["skipped"]
                _mark_mapping(target, cost_source=source, price_source=price_source)
                summary["mapped_targets"] += 1
                print(
                    "mapped: "
                    f"cost={source.product_name}; price={price_source.product_name} "
                    f"-> {target.internal_sku} / {target.product_name}"
                )
        if apply:
            db.commit()
            print("HOSUN cost mapping applied.")
        else:
            db.rollback()
            print("Dry-run only; no database changes.")
    finally:
        db.close()
    print("HOSUN Cost Mapping Summary")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    return 0 if not summary["source_missing"] and not summary["price_source_missing"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill HOSUN quote cost mappings")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.apply and not args.confirm:
        print("Refusing --apply without --confirm")
        sys.exit(1)
    sys.exit(run(apply=args.apply and args.confirm, overwrite=args.overwrite))


if __name__ == "__main__":
    main()
