"""Enrich quote catalog products with deterministic SKU/spec/pricing rules.

This script updates internal catalog metadata only. It does not create customer
quotes, send messages, change orders, import customers, or expose cost data to
customer-facing APIs.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal
from app.models import ManufacturingPartner, MarginStrategyTier, ProductCatalog, ProductPriceTier
from app.services.quotes.catalog_enrichment import (
    PROFIT_MARGIN_TIERS,
    enrich_product_attributes,
    infer_partner_code,
    infer_product_family,
    suggest_internal_sku,
)


def _partner_map(db) -> dict[str, ManufacturingPartner]:
    return {row.partner_code.upper(): row for row in db.query(ManufacturingPartner).all() if row.partner_code}


def _factory_model(product: ProductCatalog) -> str | None:
    attrs = product.attributes_json or {}
    existing = product.partner_product_code or attrs.get("partner_model") or attrs.get("source_sku")
    if existing:
        return str(existing).strip()
    text = f"{product.internal_sku} {product.product_name} {product.description_internal or ''}"
    match = re.search(r"\b(HS[A-Z0-9]{4,})\b", text, flags=re.I)
    if match:
        return match.group(1).upper()
    match = re.search(r"\b((?:JO|JB)[A-Z0-9]{4,})\b", text, flags=re.I)
    if match:
        return match.group(1).upper()
    return None


def _unique_sku(db, suggested: str, product_id: UUID, reserved: set[str]) -> str:
    candidate = suggested
    index = 2
    while True:
        existing = db.query(ProductCatalog).filter(ProductCatalog.internal_sku == candidate).first()
        reserved_by_current = candidate in reserved
        if (existing is None or existing.id == product_id) and not reserved_by_current:
            reserved.add(candidate)
            return candidate
        candidate = f"{suggested}-{index}"
        index += 1


def _should_rename_sku(current: str, suggested: str) -> bool:
    current_upper = current.upper()
    if current_upper == suggested.upper():
        return False
    return (
        current_upper.startswith("IO-")
        or
        current_upper.startswith("OTHER-")
        or current_upper.startswith("HOSUN-")
        or current_upper.startswith("JOOBOO-")
        or current_upper.count("-") > 6
    )


def _reset_margin_tiers(db) -> int:
    db.query(MarginStrategyTier).filter(
        MarginStrategyTier.strategy_code.in_(["traffic", "volume", "profit"])
    ).delete(synchronize_session=False)
    count = 0
    for code, name, min_qty, max_qty, multiplier in PROFIT_MARGIN_TIERS:
        db.add(
            MarginStrategyTier(
                strategy_code=code,
                strategy_name=name,
                min_qty=min_qty,
                max_qty=max_qty,
                multiplier=multiplier,
                notes="source: user profit table; traffic/volume/profit interval multipliers",
            )
        )
        count += 1
    return count


def _normalize_incoterms(db) -> int:
    rows = db.query(ProductPriceTier).filter(ProductPriceTier.incoterm == "EXW").all()
    for row in rows:
        row.incoterm = "FOB"
        row.source = f"{row.source or 'catalog_enrichment'}; exw_normalized_to_fob"
    return len(rows)


def run(*, apply: bool, rename_sku: bool, reset_margin_tiers: bool, normalize_incoterms: bool) -> int:
    db = SessionLocal()
    summary = {
        "products_seen": 0,
        "products_enriched": 0,
        "partners_reassigned": 0,
        "skus_renamed": 0,
        "margin_tiers_reset": 0,
        "incoterms_normalized": 0,
    }
    try:
        partners = _partner_map(db)
        products = db.query(ProductCatalog).order_by(ProductCatalog.product_name.asc()).all()
        reserved_skus = {row.internal_sku for row in products}
        for product in products:
            summary["products_seen"] += 1
            attrs = dict(product.attributes_json or {})
            current_partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == product.partner_id).first()
            partner_code = current_partner.partner_code if current_partner else None
            factory_model = _factory_model(product)
            inferred_partner = infer_partner_code(
                partner_code=partner_code,
                partner_model=factory_model,
                sku=product.internal_sku,
                name=product.product_name,
            )
            product_category, product_family = infer_product_family(
                product.product_category,
                product.product_name,
                factory_model,
            )
            enriched_attrs = enrich_product_attributes(
                name=product.product_name,
                category=product.product_category or product_category,
                product_family=product.product_family or product_family,
                partner_code=inferred_partner,
                partner_product_code=factory_model,
                internal_sku=product.internal_sku,
                attrs=attrs,
                description=product.description_internal,
            )
            suggested_sku = suggest_internal_sku(
                partner_code=inferred_partner,
                product_family=product.product_family or product_family,
                partner_model=factory_model,
                name=product.product_name,
            )
            product.attributes_json = enriched_attrs
            if factory_model and not product.partner_product_code:
                product.partner_product_code = factory_model
            if not product.product_category or product.product_category in {"product_catalog", "hosun_general"}:
                product.product_category = product_category
            if not product.product_family or product.product_family == "general_product_family":
                product.product_family = product_family
            if inferred_partner in partners and product.partner_id != partners[inferred_partner].id:
                product.partner_id = partners[inferred_partner].id
                summary["partners_reassigned"] += 1
            if rename_sku and _should_rename_sku(product.internal_sku, suggested_sku):
                reserved_skus.discard(product.internal_sku)
                product.internal_sku = _unique_sku(db, suggested_sku, product.id, reserved_skus)
                summary["skus_renamed"] += 1
            summary["products_enriched"] += 1

        if reset_margin_tiers:
            summary["margin_tiers_reset"] = _reset_margin_tiers(db)
        if normalize_incoterms:
            summary["incoterms_normalized"] = _normalize_incoterms(db)

        if apply:
            db.commit()
            print("Quote catalog enrichment applied.")
        else:
            db.rollback()
            print("Dry-run only; no database changes.")
    finally:
        db.close()

    print("Quote Catalog Enrichment Summary")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print("  safety: no quote creation, no external sending, no customer notification, no raw token handling.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich quote catalog product metadata and margin tiers")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--rename-sku", action="store_true")
    parser.add_argument("--reset-margin-tiers", action="store_true")
    parser.add_argument("--normalize-incoterms", action="store_true")
    args = parser.parse_args()
    if args.apply and not args.confirm:
        print("Refusing --apply without --confirm")
        sys.exit(1)
    sys.exit(
        run(
            apply=args.apply and args.confirm,
            rename_sku=args.rename_sku,
            reset_margin_tiers=args.reset_margin_tiers,
            normalize_incoterms=args.normalize_incoterms,
        )
    )


if __name__ == "__main__":
    main()
