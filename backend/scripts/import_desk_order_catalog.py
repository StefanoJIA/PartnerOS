"""Import sanitized desk-order product catalog into PartnerOS.

This script intentionally imports product/catalog metadata only. It does not
import customers, orders, admins, credentials, carts, or any notification logic
from the legacy desk-order-system.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal
from app.models import ManufacturingPartner, ProductCatalog

DEFAULT_SEED = BACKEND_ROOT / "app" / "data" / "desk_order_product_seed.json"


PARTNERS = {
    "HOSUN": {
        "partner_name": "HOSUN",
        "brand_name": "HOSUN",
        "partner_type": "Lifting Systems Partner",
        "city": "Chongqing",
        "main_product_categories": "lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply",
    },
    "JOOBOO": {
        "partner_name": "JOOBOO",
        "brand_name": "JOOBOO",
        "partner_type": "Education Furniture Partner",
        "city": "Chongqing",
        "main_product_categories": "education furniture, school desks/chairs, project furniture",
    },
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")


def _category_family(category: str | None, name: str) -> tuple[str, str]:
    source = f"{category or ''} {name}".lower()
    if "lifting column" in source:
        return "lifting_systems", "lifting_columns"
    if "dual-motor" in source or "single-motor" in source or "triple-motor" in source or "desk frame" in source:
        if "heavy" in source:
            return "lifting_systems", "heavy_duty_supply"
        return "lifting_systems", "desk_frames"
    if "pneumatic" in source:
        return "lifting_systems", "desk_frames"
    if "accessor" in source or "control" in source or "sample set" in source:
        return "lifting_systems", "desk_accessories"
    if "education" in source or "classroom" in source or "school" in source:
        return "education_furniture", "project_furniture"
    return _slug(category or "product_catalog"), "general_product_family"


def _parse_description(description: str | None) -> dict[str, str]:
    fields: dict[str, str] = {}
    if not description:
        return fields
    label_map = {
        "Chinese Name": "chinese_name",
        "Specification": "specification",
        "Stages": "stages",
        "Lifting Range": "lifting_range",
        "Adjustable Width": "adjustable_width",
        "Load Capacity": "load_capacity",
        "Lifting Speed": "lifting_speed",
        "Package Size": "package_size",
    }
    for line in description.splitlines():
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        key = label_map.get(label.strip())
        if key and value.strip():
            fields[key] = value.strip()
    return fields


def _configuration_model(product: dict[str, Any], specs: dict[str, str]) -> dict[str, Any]:
    name = str(product.get("name") or "")
    category = str(product.get("category") or "")
    text = f"{name} {category} {specs.get('specification', '')}".lower()
    model: dict[str, Any] = {
        "source": "desk_order_system_product_config",
        "base_type": None,
        "stage": specs.get("stages"),
        "column_type": None,
        "dimensions": specs.get("specification"),
        "customer_selectable": True,
    }
    if "dual" in text:
        model["base_type"] = "dual_motor"
    elif "single" in text:
        model["base_type"] = "single_motor"
    elif "triple" in text or "tri-motor" in text:
        model["base_type"] = "triple_motor"
    elif "pneumatic" in text:
        model["base_type"] = "pneumatic"
    elif "column" in text:
        model["base_type"] = "lifting_column"
    if "rectangular" in text:
        model["column_type"] = "rectangular"
    elif "square" in text:
        model["column_type"] = "square"
    elif "round" in text:
        model["column_type"] = "round"
    elif "oval" in text:
        model["column_type"] = "oval"
    return model


def _image_url(original: str | None) -> str | None:
    if not original:
        return None
    marker = "/static/images/products/"
    if marker in original:
        return "/desk-order-assets/products/" + original.split(marker, 1)[1]
    return original


def _ensure_partner(db, code: str, *, overwrite: bool) -> ManufacturingPartner:
    existing = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == code).first()
    spec = PARTNERS[code]
    if existing:
        if overwrite:
            for field, value in spec.items():
                setattr(existing, field, value)
            existing.default_incoterm = "FOB"
            existing.default_currency = "USD"
            existing.catalog_status = "active"
        return existing
    partner = ManufacturingPartner(
        partner_code=code,
        country="China",
        default_incoterm="FOB",
        default_currency="USD",
        catalog_status="active",
        notes="Imported as a peer partner from sanitized desk-order product catalog.",
        **spec,
    )
    db.add(partner)
    db.flush()
    return partner


def _inventory_for_product(product_id: int, inventory: list[dict[str, Any]], colors_by_id: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in inventory:
        if item.get("product_id") != product_id:
            continue
        color = colors_by_id.get(int(item.get("color_id") or 0), {})
        rows.append(
            {
                "color_code": color.get("color_code"),
                "color_name": color.get("color_name"),
                "quantity": item.get("quantity"),
                "reserved_quantity": item.get("reserved_quantity"),
                "inventory_reference_only": True,
            }
        )
    return rows


def _upsert_product(
    db,
    *,
    partner: ManufacturingPartner,
    product: dict[str, Any],
    colors: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
    overwrite: bool,
) -> str:
    sku = str(product.get("sku") or "").strip()
    if not sku:
        return "skipped"
    internal_sku = f"HOSUN-{sku}" if not sku.upper().startswith("HOSUN-") else sku.upper()
    specs = _parse_description(product.get("description"))
    product_category, product_family = _category_family(product.get("category"), str(product.get("name") or ""))
    attrs = {
        "source_system": "desk_order_system",
        "source_record_id": product.get("id"),
        "source_sku": sku,
        "source_category": product.get("category"),
        "source_image_url": product.get("image_url"),
        "customer_quote_name": product.get("name"),
        "product_specs": specs,
        "configuration_model": _configuration_model(product, specs),
        "color_options_summary": {
            "total_available_colors": len(colors),
            "basic_colors": len([row for row in colors if row.get("color_type") == "basic"]),
            "ral_colors": len([row for row in colors if row.get("color_type") == "ral"]),
            "custom_ral_supported": True,
        },
        "inventory_snapshot": inventory_rows,
        "legacy_backend_mapping": {
            "product_config_api": "merged_into_product_catalog_attributes",
            "cart_api": "future_portal_quote_request_input",
            "inventory": "reference_only_no_auto_reservation",
            "order_tracking": "mapped_to_production_milestones_and_shipment_plans",
            "feedback": "mapped_to_feedback_tickets_and_market_response",
        },
        "safety": {
            "customer_visible_pricing_requires_quote_tiers": True,
            "inventory_not_promised": True,
            "automatic_sending_enabled": False,
            "raw_cost_hidden": True,
        },
    }
    if product.get("price") is not None:
        attrs["legacy_price_reference"] = {
            "value": product.get("price"),
            "source": "desk_order_system_product_price",
            "internal_reference_only": True,
            "not_quote_price": True,
        }

    existing = db.query(ProductCatalog).filter(ProductCatalog.internal_sku == internal_sku).first()
    if existing and not overwrite:
        return "skipped"
    if existing and overwrite:
        existing.partner_id = partner.id
        existing.partner_product_code = sku
        existing.product_name = str(product.get("name") or sku)
        existing.product_category = product_category
        existing.product_family = product_family
        existing.description_customer = str(product.get("name") or sku)
        existing.description_internal = product.get("description")
        existing.status = "active" if product.get("is_active", True) else "inactive"
        existing.image_url = _image_url(product.get("image_url"))
        existing.attributes_json = attrs
        existing.notes = "desk_order_system_import; product catalog only; no customer/order/admin data imported"
        return "updated"

    row = ProductCatalog(
        partner_id=partner.id,
        internal_sku=internal_sku,
        partner_product_code=sku,
        product_name=str(product.get("name") or sku),
        product_category=product_category,
        product_family=product_family,
        description_customer=str(product.get("name") or sku),
        description_internal=product.get("description"),
        status="active" if product.get("is_active", True) else "inactive",
        default_uom="EA",
        base_currency="USD",
        default_incoterm="FOB",
        image_url=_image_url(product.get("image_url")),
        attributes_json=attrs,
        notes="desk_order_system_import; product catalog only; no customer/order/admin data imported",
    )
    db.add(row)
    return "created"


def run(seed_file: Path, *, apply: bool, overwrite: bool) -> int:
    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    if payload.get("safety", {}).get("contains_tokens") or payload.get("customers"):
        print("Refusing unsafe seed: product-only sanitized seed required.")
        return 2
    products = payload.get("products", [])
    colors = payload.get("color_options", [])
    inventory = payload.get("inventory", [])
    colors_by_id = {int(row["id"]): row for row in colors if row.get("id") is not None}
    summary = {"created": 0, "updated": 0, "skipped": 0}

    db = SessionLocal()
    try:
        hosun = _ensure_partner(db, "HOSUN", overwrite=overwrite)
        _ensure_partner(db, "JOOBOO", overwrite=overwrite)
        for product in products:
            action = _upsert_product(
                db,
                partner=hosun,
                product=product,
                colors=colors,
                inventory_rows=_inventory_for_product(int(product.get("id") or 0), inventory, colors_by_id),
                overwrite=overwrite,
            )
            summary[action] += 1
        if apply:
            db.commit()
            print("Desk-order catalog import applied.")
        else:
            db.rollback()
            print("Dry-run only; no database changes.")
    finally:
        db.close()
    print("Desk-order Product Catalog Import Summary")
    print(f"  seed_file: {seed_file}")
    print(f"  products: {len(products)}")
    print(f"  colors: {len(colors)}")
    print(f"  inventory_rows: {len(inventory)}")
    print(f"  actions: {summary}")
    print("  safety: customers/orders/admins/tokens were not imported; no automatic sending or inventory reservation.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Import sanitized desk-order products into PartnerOS catalog")
    parser.add_argument("--file", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.apply and not args.confirm:
        print("Refusing --apply without --confirm")
        sys.exit(1)
    sys.exit(run(args.file, apply=args.apply and args.confirm, overwrite=args.overwrite))


if __name__ == "__main__":
    main()
