"""Compatibility API for the imported customer-facing desk order site.

The imported site is an HTML/JS frontend that expects the old `/api/...`
contract. PartnerOS keeps the internal admin API separate, so these routes live
under `/api/site/...` and return customer-safe catalog/order/feedback data.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Company, Contact, ManufacturingPartner, ProductCatalog, Sample
from app.models.customer_orders import CustomerOrder, OrderLineItem, OrderProductionMilestone, ShipmentPlan
from app.services.portal.customer_order_snapshot import build_customer_order_snapshot
from app.services.portal.customer_portal_bridge import create_feedback_ticket

router = APIRouter(prefix="/site", tags=["customer-site-compat"])

# Legacy imported customer-site image host (bucket segment only — no hard-coded partner branding).
_LEGACY_GCS_IMAGE_MARKER = "desk-order-storage/products/images/"


class SiteFeedbackIn(BaseModel):
    order_id: str | None = None
    order_number: str | None = None
    feedback_category: str | None = None
    feedback_type: str | None = None
    feedback_text: str | None = None
    message: str | None = None
    suggestions: str | None = None
    subject: str | None = None
    priority: str = "normal"
    customer_name: str | None = None
    customer_email: EmailStr | None = None
    company_name: str | None = None


class SitePasswordChangeIn(BaseModel):
    old_password: str | None = None
    current_password: str | None = None
    new_password: str


class SiteProductConfigFindIn(BaseModel):
    base_type: str
    stage: str | None = None
    column_type: str | None = None
    dimensions: str | None = None


def _attrs(row: ProductCatalog) -> dict[str, Any]:
    return row.attributes_json if isinstance(row.attributes_json, dict) else {}


def _partner_code(row: ProductCatalog, partners: dict[Any, ManufacturingPartner]) -> str:
    partner = partners.get(row.partner_id)
    return partner.partner_code if partner and partner.partner_code else "INTELLIOPUS"


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    replacements = {
        "กม": " x ",
        "姝": "",
        "鍗": "",
        "妗": "",
        "鐢": "",
        "瑙": "",
        "甯": "",
        "�": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.split())


def _clean_image_url(value: Any, group: str) -> str:
    url = str(value or "").strip()
    if not url:
        return _fallback_group_image(group)
    if "storage.googleapis.com" in url and _LEGACY_GCS_IMAGE_MARKER in url:
        return _fallback_group_image(group)
    return url


def _fallback_group_image(group: str) -> str:
    mapping = {
        "Accessories": "/static/images/products/accessories.png",
        "Multi-User Benching": "/static/images/products/multi-user-benching.png",
        "Electric Columns": "/static/images/products/electric-columns.png",
        "Education Furniture": "/static/images/placeholder.png",
    }
    return mapping.get(group, "/static/images/products/standalone-frames.png")


PUBLIC_PRODUCT_GROUPS: dict[str, dict[str, Any]] = {
    "Standalone Frames": {
        "name_en": "Standalone Frames",
        "description": "Single-user desk frames, pneumatic desks, and standard lifting desk products.",
        "icon": "frame",
        "emoji": "⚙️",
        "image_url": "/static/images/products/standalone-frames.png",
    },
    "Multi-User Benching": {
        "name_en": "Multi-User Benching",
        "description": "Face-to-face benching and workstation systems for multiple users.",
        "icon": "bench",
        "emoji": "🏢",
        "image_url": "/static/images/products/multi-user-benching.png",
    },
    "Electric Columns": {
        "name_en": "Electric Columns",
        "description": "Independent lifting columns and leg sets used as column components.",
        "icon": "column",
        "emoji": "🔧",
        "image_url": "/static/images/products/electric-columns.png",
    },
    "Accessories": {
        "name_en": "Accessories",
        "description": "Hand control panels, color swatches, and supporting accessories.",
        "icon": "control",
        "emoji": "🎛️",
        "image_url": "/static/images/products/accessories.png",
    },
    "Education Furniture": {
        "name_en": "Education Furniture",
        "description": "Reserved for JOOBOO school desks, chairs, and project furniture after data approval.",
        "icon": "education",
        "emoji": "🪑",
        "image_url": "/static/images/placeholder.png",
        "is_pending": True,
    },
}


PUBLIC_GROUP_ORDER = list(PUBLIC_PRODUCT_GROUPS.keys())


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    replacements = {
        "鈱€": "Ø",
        "脳": "x",
        "鈫?": "->",
        "鈿": "",
        "鉁?": "",
        "馃": "",
        "กม": " x ",
        "�": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.split())


def _clean_image_url(value: Any, group: str) -> str:
    url = str(value or "").strip()
    if not url:
        return _fallback_group_image(group)
    if "storage.googleapis.com" in url and _LEGACY_GCS_IMAGE_MARKER in url:
        return _fallback_group_image(group)
    return url


def _money(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _order_item_count(order: CustomerOrder) -> int:
    try:
        return len(order.line_items or [])
    except Exception:
        return 0


def _group_name(row: ProductCatalog) -> str:
    attrs = _attrs(row)
    family = str(attrs.get("product_family_hint") or row.product_family or "").lower()
    category = str(row.product_category or "").lower()
    name = str(row.product_name or "").lower()
    sku = str(row.internal_sku or "").lower()
    model = str(row.partner_product_code or "").lower()
    if "hand" in name or "control" in name or "swatch" in name or category == "accessories":
        return "Accessories"
    if "bench" in name or "workstation" in name or "face-to-face" in name:
        return "Multi-User Benching"
    if "education" in category or "school" in family or "furniture" in category or sku.startswith("jo"):
        return "Education Furniture"
    is_frame = "frame" in name or "desk frame" in name or "desk" in name
    is_column = (
        "lifting_column" in family
        or category in {"lifting_column", "electric_column", "columns"}
        or "lifting column" in name
        or (("column" in name or "column" in model or "column" in sku) and not is_frame)
    )
    if is_column:
        return "Electric Columns"
    return "Standalone Frames"


def _stage_count(row: ProductCatalog) -> str | None:
    attrs = _attrs(row)
    specs = attrs.get("product_specs") if isinstance(attrs.get("product_specs"), dict) else {}
    explicit = specs.get("stage_count") or attrs.get("stage_count")
    if explicit:
        return str(explicit)
    lower = row.product_name.lower()
    if "3-stage" in lower or "3 stage" in lower:
        return "3"
    if "2-stage" in lower or "2 stage" in lower:
        return "2"
    return None


def _load_capacity(row: ProductCatalog) -> int | None:
    attrs = _attrs(row)
    specs = attrs.get("product_specs") if isinstance(attrs.get("product_specs"), dict) else {}
    raw = specs.get("load_capacity") or attrs.get("load_capacity")
    if isinstance(raw, (int, float)):
        return int(raw)
    text = f"{raw or ''} {row.product_name}".lower()
    if "300kg" in text or "300 kg" in text or "heavy" in text:
        return 300
    if "3-leg" in text or "three-leg" in text:
        return 360
    if "workstation" in text or "benching" in text or "face-to-face" in text:
        return 240
    if "single-motor" in text:
        return 80
    if "dual-motor" in text or "2-stage" in text or "3-stage" in text:
        return 120
    return None


def _dimensions(row: ProductCatalog) -> str | None:
    attrs = _attrs(row)
    specs = attrs.get("product_specs") if isinstance(attrs.get("product_specs"), dict) else {}
    value = specs.get("dimensions") or attrs.get("dimensions")
    return str(value) if value else None


def _legacy_product(row: ProductCatalog, index: int, partners: dict[Any, ManufacturingPartner]) -> dict[str, Any]:
    attrs = _attrs(row)
    name = _clean_text(attrs.get("customer_quote_name") or row.description_customer or row.product_name) or "Product"
    group = _group_name(row)
    return {
        "id": index,
        "source_id": str(row.id),
        "sku": _clean_text(row.internal_sku),
        "product_sku": _clean_text(row.internal_sku),
        "name": name,
        "product_name": name,
        "category": group,
        "group_name": group,
        "partner": _partner_code(row, partners),
        "image_url": _clean_image_url(row.image_url, group),
        "specification": _clean_text(_dimensions(row)),
        "stages": _stage_count(row),
        "load_capacity": _load_capacity(row),
        "lifting_range": _clean_text(attrs.get("lifting_range")),
        "lifting_speed": attrs.get("lifting_speed"),
        "box_count": attrs.get("box_count"),
        "box_dimensions": _clean_text(attrs.get("box_dimensions")),
        "price": 0,
        "is_active": row.status == "active",
    }


def _product_search_text(product: dict[str, Any]) -> str:
    values = [
        product.get("sku"),
        product.get("product_sku"),
        product.get("name"),
        product.get("product_name"),
        product.get("specification"),
        product.get("partner"),
    ]
    return " ".join(str(value or "") for value in values).lower()


def _matches_base_type(product: dict[str, Any], base_type: str) -> bool:
    text = _product_search_text(product)
    base = base_type.lower()
    if product.get("group_name") == "Electric Columns" or product.get("group_name") == "Accessories":
        return False
    if base == "dual motor":
        return (
            "dual" in text
            and "motor" in text
            and "short" not in text
            and "heavy" not in text
            and "300kg" not in text
            and "single" not in text
            and "l-shape" not in text
            and "l shape" not in text
            and "face-to-face" not in text
            and "workstation" not in text
            and "bench" not in text
        )
    if base == "dual motor short":
        return "dual" in text and "motor" in text and ("short" in text or "3psddfz" in text)
    if base == "l-shape":
        return "l-shape" in text or "l shape" in text or "prtdfz" in text
    if base == "heavy-duty":
        return "heavy" in text or "300kg" in text or "300 kg" in text or "hrddfz" in text
    if base == "single motor":
        return "single" in text and "motor" in text
    if base == "face-to-face":
        return ("face-to-face" in text or "face to face" in text or "cws" in text) and "fdf" not in text and "trio" not in text
    if base == "trio":
        return "trio" in text or "120" in text or "fdf" in text
    return base in text


def _base_card(
    products: list[dict[str, Any]],
    *,
    fallback_id: str,
    fallback_sku: str,
    name: str,
    description: str,
    base_type: str,
    image_url: str,
) -> dict[str, Any]:
    match = next((product for product in products if _matches_base_type(product, base_type)), None)
    source = match or {}
    return {
        "id": source.get("id") or fallback_id,
        "source_id": source.get("source_id"),
        "sku": source.get("sku") or fallback_sku,
        "product_sku": source.get("product_sku") or fallback_sku,
        "name": name,
        "product_name": name,
        "description": description,
        "category": source.get("category") or ("Multi-User Benching" if base_type in {"Face-to-Face", "Trio"} else "Standalone Frames"),
        "group_name": source.get("group_name") or ("Multi-User Benching" if base_type in {"Face-to-Face", "Trio"} else "Standalone Frames"),
        "partner": source.get("partner") or "INTELLIOPUS",
        "image_url": source.get("image_url") or image_url,
        "specification": source.get("specification"),
        "stages": source.get("stages"),
        "load_capacity": source.get("load_capacity"),
        "lifting_range": source.get("lifting_range"),
        "lifting_speed": source.get("lifting_speed"),
        "box_count": source.get("box_count"),
        "box_dimensions": source.get("box_dimensions"),
        "base_type": base_type,
        "price": 0,
        "is_active": True,
        "is_configurable": True,
    }


def _standalone_base_products(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    standalone = [item for item in products if item["group_name"] == "Standalone Frames"]
    return [
        _base_card(
            standalone,
            fallback_id="base-dual-motor",
            fallback_sku="HS **** * PRDDFZ",
            name="Dual Motor Desk Frame",
            description="Configurable dual-motor standing desk frame.",
            base_type="Dual Motor",
            image_url="/static/images/products/standalone-frames.png",
        ),
        _base_card(
            standalone,
            fallback_id="base-dual-motor-short",
            fallback_sku="HS **** 3PSDDFZ",
            name="Dual Motor Desk Short Frame",
            description="Configurable short-stroke dual-motor frame.",
            base_type="Dual Motor Short",
            image_url="/static/images/products/standalone-frames.png",
        ),
        _base_card(
            standalone,
            fallback_id="base-l-shape",
            fallback_sku="HS **** * PRTDFZ",
            name="L-shape Standing Desk Frame",
            description="Configurable three-leg L-shape standing desk frame.",
            base_type="L-shape",
            image_url="/static/images/products/standalone-frames.png",
        ),
        _base_card(
            standalone,
            fallback_id="base-heavy-duty",
            fallback_sku="HS **** 2HRDDFZ",
            name="Heavy-Duty Desk Frame",
            description="Configurable 300 kg heavy-duty standing desk frame.",
            base_type="Heavy-Duty",
            image_url="/static/images/products/standalone-frames.png",
        ),
        _base_card(
            standalone,
            fallback_id="base-single-motor",
            fallback_sku="HS **** * PRSDFZ",
            name="Single Motor Desk Frame",
            description="Configurable single-motor standing desk frame.",
            base_type="Single Motor",
            image_url="/static/images/products/standalone-frames.png",
        ),
    ]


def _multi_user_base_products(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    multi_user = [item for item in products if item["group_name"] == "Multi-User Benching"]
    return [
        _base_card(
            multi_user,
            fallback_id="base-face-to-face",
            fallback_sku="HS **** * PRCWSZ",
            name="Face-to-Face Workstation Frame",
            description="Configurable face-to-face benching workstation frame.",
            base_type="Face-to-Face",
            image_url="/static/images/products/multi-user-benching.png",
        ),
        _base_card(
            multi_user,
            fallback_id="base-trio",
            fallback_sku="HS **** * PRFDF2",
            name="120° Trio Workstation Frame",
            description="Configurable 120 degree trio workstation frame.",
            base_type="Trio",
            image_url="/static/images/products/multi-user-benching.png",
        ),
    ]


def _norm_config(value: str | None) -> str:
    return str(value or "").lower().replace(" ", "").replace('"', "").replace("×", "*").replace("x", "*").replace("ø", "o")


def _config_match_score(product: dict[str, Any], request: SiteProductConfigFindIn) -> int:
    text = _product_search_text(product).replace("×", "*").replace("x", "*")
    score = 0
    if _matches_base_type(product, request.base_type):
        score += 40
    stage = _norm_config(request.stage)
    if stage and (stage in _norm_config(product.get("name")) or stage in _norm_config(product.get("stages"))):
        score += 25
    column = _norm_config(request.column_type)
    if column and column in _norm_config(text):
        score += 20
    dimensions = _norm_config(request.dimensions)
    if dimensions:
        compact_text = _norm_config(text)
        if dimensions in compact_text:
            score += 25
        elif dimensions.replace("*", "") in compact_text.replace("*", ""):
            score += 15
    return score


def _catalog_rows(db: Session) -> list[ProductCatalog]:
    return (
        db.query(ProductCatalog)
        .filter(ProductCatalog.status == "active")
        .order_by(ProductCatalog.product_category.asc(), ProductCatalog.product_name.asc())
        .all()
    )


def _legacy_products(db: Session) -> list[dict[str, Any]]:
    rows = _catalog_rows(db)
    partners = (
        {p.id: p for p in db.query(ManufacturingPartner).filter(ManufacturingPartner.id.in_({r.partner_id for r in rows})).all()}
        if rows
        else {}
    )
    products = [_legacy_product(row, idx + 1, partners) for idx, row in enumerate(rows)]
    return [item for item in products if item["group_name"] in PUBLIC_PRODUCT_GROUPS and item["group_name"] != "Education Furniture"]


@router.get("/auth/me")
def site_auth_me() -> dict[str, Any]:
    return {
        "id": "customer-site-local",
        "email": "portal@intelli-opus.local",
        "name": "IntelliOpus Portal",
        "role": "customer",
        "password_changed": True,
    }


@router.post("/auth/login")
def site_auth_login() -> dict[str, Any]:
    return {
        "access_token": "customer-site-local-token",
        "token_type": "bearer",
        "password_changed": True,
        "is_admin": False,
    }


@router.post("/auth/register")
def site_auth_register() -> dict[str, Any]:
    return {
        "access_token": "customer-site-local-token",
        "token_type": "bearer",
        "password_changed": True,
        "is_admin": False,
    }


@router.post("/auth/change-password")
def site_change_password(body: SitePasswordChangeIn) -> dict[str, Any]:
    if len(body.new_password or "") < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters.")
    return {
        "message": "Password updated for this local customer portal session.",
        "password_changed": True,
    }


@router.post("/auth/send-verification-code")
def site_send_verification_code() -> dict[str, Any]:
    return {"message": "Verification is handled by the local customer site compatibility layer."}


@router.get("/products/categories/groups")
def site_product_groups(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    products = _legacy_products(db)
    counts = Counter(item["group_name"] for item in products)
    return [
        {
            "group_name": name,
            **PUBLIC_PRODUCT_GROUPS[name],
            "product_count": counts[name],
            "is_available": counts[name] > 0,
        }
        for name in PUBLIC_GROUP_ORDER
    ]


@router.get("/products/group/{group_name}")
def site_products_by_group(group_name: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    wanted = group_name.replace("%20", " ")
    products = _legacy_products(db)
    if wanted.lower() == "standalone frames":
        return _standalone_base_products(products)
    if wanted.lower() == "multi-user benching":
        return _multi_user_base_products(products)
    if wanted.lower() == "education furniture":
        return []
    return [item for item in products if item["group_name"].lower() == wanted.lower()]


@router.post("/products/config/find")
def site_product_config_find(body: SiteProductConfigFindIn, db: Session = Depends(get_db)) -> dict[str, Any]:
    products = [
        product
        for product in _legacy_products(db)
        if product["group_name"] in {"Standalone Frames", "Multi-User Benching"}
    ]
    scored = [
        (_config_match_score(product, body), product)
        for product in products
        if _matches_base_type(product, body.base_type)
    ]
    scored = [(score, product) for score, product in scored if score >= 40]
    if not scored:
        raise HTTPException(status_code=404, detail="No matching product found for the selected configuration.")
    scored.sort(key=lambda item: item[0], reverse=True)
    score, product = scored[0]
    return {
        "product_id": product["id"],
        "source_id": product.get("source_id"),
        "sku": product.get("sku"),
        "name": product.get("name"),
        "base_type": body.base_type,
        "match_score": score,
        "configuration": {
            "stage": body.stage,
            "column_type": body.column_type,
            "dimensions": body.dimensions,
        },
    }


@router.get("/products")
def site_products(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return _legacy_products(db)


@router.get("/products/{product_id}")
def site_product_detail(product_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    for product in _legacy_products(db):
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


@router.get("/inventory/colors")
def site_inventory_colors(color_type: str | None = None) -> list[dict[str, Any]]:
    colors = [
        {"id": 1, "color_name": "Traffic White", "color_code": "RAL 9016", "hex_code": "#F6F6F6", "color_type": "basic"},
        {"id": 2, "color_name": "White Aluminium", "color_code": "RAL 9006", "hex_code": "#A5A5A5", "color_type": "basic"},
        {"id": 3, "color_name": "Anthracite Grey", "color_code": "RAL 7016", "hex_code": "#383E42", "color_type": "basic"},
        {"id": 4, "color_name": "Jet Black", "color_code": "RAL 9005", "hex_code": "#0A0A0A", "color_type": "basic"},
        {"id": 5, "color_name": "Signal White", "color_code": "RAL 9003", "hex_code": "#F4F4F4", "color_type": "classic"},
        {"id": 6, "color_name": "Pure White", "color_code": "RAL 9010", "hex_code": "#F1F0EA", "color_type": "classic"},
        {"id": 7, "color_name": "Light Grey", "color_code": "RAL 7035", "hex_code": "#CBD0CC", "color_type": "classic"},
        {"id": 8, "color_name": "Window Grey", "color_code": "RAL 7040", "hex_code": "#9DA3A6", "color_type": "classic"},
        {"id": 9, "color_name": "Gentian Blue", "color_code": "RAL 5010", "hex_code": "#004F7C", "color_type": "classic"},
        {"id": 10, "color_name": "Ruby Red", "color_code": "RAL 3003", "hex_code": "#8A1A1A", "color_type": "classic"},
        {"id": 11, "color_name": "Pastel Green", "color_code": "RAL 6019", "hex_code": "#B9CEAC", "color_type": "classic"},
        {"id": 12, "color_name": "Light Ivory", "color_code": "RAL 1015", "hex_code": "#E6D2B5", "color_type": "classic"},
    ]
    return [c for c in colors if not color_type or c["color_type"] == color_type]


@router.get("/inventory/products")
def site_inventory_products(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for product in _legacy_products(db):
        attrs = product.copy()
        available = 0
        source_id = attrs.get("source_id")
        row = db.query(ProductCatalog).filter(ProductCatalog.id == source_id).first() if source_id else None
        raw_attrs = _attrs(row) if row else {}
        inventory = raw_attrs.get("inventory_snapshot")
        if isinstance(inventory, list):
            available = sum(int(item.get("available_quantity") or item.get("quantity") or 0) for item in inventory if isinstance(item, dict))
        elif raw_attrs.get("sample_available"):
            available = 1
        if available <= 0:
            continue
        items.append(
            {
                "id": len(items) + 1,
                "product_id": attrs["id"],
                "product_name": attrs["product_name"],
                "product_sku": attrs["sku"],
                "product_image": attrs.get("image_url"),
                "image_url": attrs.get("image_url"),
                "color_name": "Standard",
                "color_code": "",
                "color_type": "basic",
                "quantity": available,
                "reserved_quantity": 0,
                "available_quantity": available,
                "lead_time_days": 7,
            }
        )
    return items


@router.get("/cart/count")
def site_cart_count() -> dict[str, int]:
    return {"count": 0}


@router.get("/cart")
def site_cart() -> dict[str, Any]:
    return {"items": [], "count": 0, "total": 0}


@router.post("/cart/items")
def site_cart_add_item() -> dict[str, Any]:
    return {"message": "Item captured locally. Formal order creation is not enabled in this compatibility layer.", "count": 0}


@router.delete("/cart/items/{item_id}")
def site_cart_delete_item(item_id: str) -> dict[str, Any]:
    return {"message": "Item removed from local compatibility cart.", "count": 0}


@router.get("/customer/statistics")
def site_customer_statistics(db: Session = Depends(get_db)) -> dict[str, Any]:
    total_orders = db.query(CustomerOrder).count()
    pending_orders = db.query(CustomerOrder).filter(CustomerOrder.status != "delivered").count()
    completed_orders = db.query(CustomerOrder).filter(CustomerOrder.status == "delivered").count()
    total_amount = sum(_money(value) for (value,) in db.query(CustomerOrder.grand_total).all())
    return {
        "total_orders": total_orders,
        "total_amount": total_amount,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
    }


def _date_iso(value: Any) -> str | None:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if value:
        return str(value)
    return None


def _customer_order_by_number(db: Session, order_number: str) -> CustomerOrder | None:
    return (
        db.query(CustomerOrder)
        .filter(func.lower(CustomerOrder.order_number) == order_number.strip().lower())
        .first()
    )


def _site_order_shipping_status(order: CustomerOrder) -> str:
    active_shipments = [plan for plan in order.shipment_plans if plan.status != "cancelled"]
    if any(plan.status == "delivered" for plan in active_shipments) or order.status == "delivered":
        return "delivered"
    if any(plan.status == "shipped" for plan in active_shipments) or order.status == "shipped":
        return "in_transit"
    if any(plan.status in {"planned", "draft"} for plan in active_shipments):
        return "processing"
    if order.status == "ready_to_ship":
        return "ready_to_ship"
    return "pending"


def _site_order_item_payload(line: OrderLineItem) -> dict[str, Any]:
    return {
        "id": str(line.id),
        "product_name": line.product_name,
        "product_sku": line.internal_sku or line.partner_product_code,
        "final_sku": line.internal_sku or line.partner_product_code,
        "color_name": line.color_finish,
        "color": line.color_finish,
        "quantity": line.quantity,
        "unit_price": _money(line.unit_price),
        "subtotal": _money(line.total_price),
        "currency": line.currency,
    }


def _site_order_detail_payload(order: CustomerOrder) -> dict[str, Any]:
    company_name = order.bill_to_company or order.ship_to_company or None
    contact_name = order.bill_to_name or order.ship_to_name or None
    active_shipments = [plan for plan in order.shipment_plans if plan.status != "cancelled"]
    tracking_number = next((plan.tracking_number for plan in active_shipments if plan.tracking_number), None)
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "shipping_status": _site_order_shipping_status(order),
        "order_date": _date_iso(order.order_date),
        "customer_name": contact_name or company_name or "Customer",
        "company_name": company_name,
        "bill_to_name": order.bill_to_name,
        "bill_to_company": order.bill_to_company,
        "ship_to_name": order.ship_to_name,
        "ship_to_company": order.ship_to_company,
        "billing_address": order.bill_to_address,
        "shipping_address": order.ship_to_address,
        "tracking_number": tracking_number,
        "grand_total": _money(order.grand_total),
        "total_amount": _money(order.grand_total),
        "currency": order.currency,
        "item_count": _order_item_count(order),
        "items": [_site_order_item_payload(line) for line in order.line_items],
        "customer_visible_only": True,
        "customer_notified": False,
        "automatic_email_sent": False,
    }


_TRACKING_STEP_NAMES = {
    "order_placed": "Order Placed",
    "factory_order_created": "Factory Order Created",
    "material_prepared": "Material Prepared",
    "painting_started": "Painting Started",
    "assembly_started": "Assembly Started",
    "testing_shipping": "Testing & Shipping",
    "container_packed": "Container Packed",
    "shipment_departed": "Shipment Departed",
    "arrived_port": "Arrived at Port",
    "land_transport": "Land Transport",
    "order_completed": "Order Completed",
}


def _step_payload(
    *,
    index: int,
    step: str,
    status: str,
    update_date: Any = None,
    details: str | None = None,
    notes: str | None = None,
    operator: str | None = None,
    shipment: ShipmentPlan | None = None,
) -> dict[str, Any]:
    return {
        "id": index,
        "step": step,
        "step_name": _TRACKING_STEP_NAMES.get(step, step.replace("_", " ").title()),
        "status": status,
        "update_date": _date_iso(update_date),
        "details": details,
        "notes": notes,
        "operator": operator,
        "images": [],
        "vessel_name": None,
        "vessel_number": None,
        "vessel_imo": None,
        "vessel_mmsi": None,
        "vessel_callsign": None,
        "departure_port": shipment.origin if shipment else None,
        "arrival_port": shipment.destination if shipment else None,
        "estimated_arrival_date": _date_iso(shipment.estimated_arrival_date) if shipment else None,
        "vessel_finder_url": None,
        "transport_company": shipment.shipment_method if shipment else None,
        "transport_number": shipment.tracking_number if shipment else None,
        "created_at": _date_iso(getattr(shipment, "created_at", None)) if shipment else None,
    }


def _latest_milestone_by_type(rows: list[OrderProductionMilestone]) -> dict[str, OrderProductionMilestone]:
    result: dict[str, OrderProductionMilestone] = {}
    for row in sorted(rows, key=lambda item: (item.sequence, _date_iso(item.created_at) or "")):
        result[row.milestone_type] = row
    return result


def _milestone_status(row: OrderProductionMilestone | None) -> str | None:
    if not row:
        return None
    if row.status == "completed":
        return "completed"
    if row.status in {"in_progress", "delayed", "blocked"}:
        return "in_progress"
    return None


def _milestone_date_value(row: OrderProductionMilestone | None) -> Any:
    if not row:
        return None
    return row.actual_date or row.planned_date or row.created_at


def _build_site_tracking_payload(order: CustomerOrder, db: Session) -> dict[str, Any]:
    production_rows = (
        db.query(OrderProductionMilestone)
        .filter(OrderProductionMilestone.order_id == order.id)
        .order_by(OrderProductionMilestone.sequence.asc())
        .all()
    )
    shipment_rows = (
        db.query(ShipmentPlan)
        .filter(ShipmentPlan.order_id == order.id, ShipmentPlan.status != "cancelled")
        .order_by(ShipmentPlan.created_at.desc())
        .all()
    )
    milestones = _latest_milestone_by_type(production_rows)
    shipment = shipment_rows[0] if shipment_rows else None

    steps: list[dict[str, Any]] = []
    index = 1
    confirmed_statuses = {
        "confirmed",
        "supplier_confirmation_pending",
        "supplier_confirmed",
        "production_pending",
        "in_production",
        "ready_to_ship",
        "shipped",
        "delivered",
    }
    steps.append(
        _step_payload(
            index=index,
            step="order_placed",
            status="completed" if order.status in confirmed_statuses or order.customer_confirmed_at else "in_progress",
            update_date=order.customer_confirmed_at or order.order_date,
            details="Order record is available in PartnerOS.",
            notes="Customer-visible tracking only; planned dates are guidance.",
        )
    )
    index += 1

    factory_status = "completed" if order.status in confirmed_statuses else None
    if factory_status:
        steps.append(
            _step_payload(
                index=index,
                step="factory_order_created",
                status=factory_status,
                update_date=order.customer_confirmed_at or order.order_date,
                details="Order has been confirmed internally and is ready for supplier / production coordination.",
            )
        )
        index += 1

    milestone_map = [
        ("material_prepared", "materials_prepared", "Material preparation update from PartnerOS."),
        ("painting_started", "painting", "Painting / finish process update from PartnerOS."),
        ("assembly_started", "assembly", "Assembly process update from PartnerOS."),
        ("testing_shipping", "quality_check", "Quality check update from PartnerOS."),
        ("container_packed", "packing", "Packing update from PartnerOS."),
    ]
    for step_key, milestone_type, fallback in milestone_map:
        row = milestones.get(milestone_type)
        status = _milestone_status(row)
        if not status:
            continue
        steps.append(
            _step_payload(
                index=index,
                step=step_key,
                status=status,
                update_date=_milestone_date_value(row),
                details=row.milestone_label or fallback,
                notes=row.notes,
                operator=row.responsible_party,
            )
        )
        index += 1

    if shipment:
        shipment_status = "completed" if shipment.status in {"shipped", "delivered"} else "in_progress"
        steps.append(
            _step_payload(
                index=index,
                step="shipment_departed",
                status=shipment_status,
                update_date=shipment.estimated_ship_date or shipment.created_at,
                details="Shipment plan is available from PartnerOS tracking records.",
                notes=shipment.notes,
                shipment=shipment,
            )
        )
        index += 1
        if shipment.estimated_arrival_date or shipment.status == "delivered":
            steps.append(
                _step_payload(
                    index=index,
                    step="arrived_port",
                    status="completed" if shipment.status == "delivered" else "in_progress",
                    update_date=shipment.estimated_arrival_date,
                    details="Destination arrival information is available or planned.",
                    notes="Estimated dates are planned references unless marked delivered.",
                    shipment=shipment,
                )
            )
            index += 1
        if shipment.status == "delivered":
            steps.append(
                _step_payload(
                    index=index,
                    step="order_completed",
                    status="completed",
                    update_date=shipment.estimated_arrival_date or shipment.updated_at,
                    details="Order is marked delivered in PartnerOS tracking records.",
                    shipment=shipment,
                )
            )

    if len(steps) == 1 and steps[0]["status"] != "completed":
        steps[0]["details"] = "Order has been received. Production and shipment tracking will appear after internal updates are added."

    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "steps": steps,
        "safety": {
            "customer_visible_only": True,
            "customer_notified": False,
            "supplier_notified": False,
            "carrier_api_called": False,
            "order_status_mutated": False,
        },
    }


@router.get("/customer/orders")
def site_customer_orders(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.query(CustomerOrder).order_by(CustomerOrder.created_at.desc()).limit(50).all()
    return [
        {
            "id": str(row.id),
            "order_number": row.order_number,
            "status": row.status,
            "order_date": row.order_date.isoformat() if row.order_date else None,
            "company_name": row.bill_to_company or row.ship_to_company,
            "grand_total": float(row.grand_total or 0),
            "total_amount": _money(row.grand_total),
            "item_count": _order_item_count(row),
            "currency": row.currency,
        }
        for row in rows
    ]


@router.get("/customer/orders/by-number/{order_number}")
def site_customer_order_by_number(order_number: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    order = _customer_order_by_number(db, order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _site_order_detail_payload(order)


@router.get("/customer/orders/by-number/{order_number}/tracking")
def site_customer_order_tracking_by_number(order_number: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    order = _customer_order_by_number(db, order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _build_site_tracking_payload(order, db)


@router.get("/customer/orders/{order_id}/tracking")
def site_customer_order_tracking(order_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    order = db.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _build_site_tracking_payload(order, db)


@router.get("/customer/orders/{order_id}")
def site_customer_order_detail(order_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    order = db.query(CustomerOrder).filter(CustomerOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return build_customer_order_snapshot(db, order.id)


@router.post("/customer/orders")
def site_customer_order_create() -> dict[str, Any]:
    return {
        "message": "Customer order submission is pending formal quote acceptance workflow integration.",
        "order_created": False,
        "status": "draft_intake_not_persisted",
    }


@router.post("/customer/custom-order")
def site_customer_custom_order_create() -> dict[str, Any]:
    return site_customer_order_create()


@router.post("/customer/feedback")
def site_customer_feedback(body: SiteFeedbackIn, db: Session = Depends(get_db)) -> dict[str, Any]:
    order_id: UUID | None = None
    company_id: UUID | None = None
    if body.order_number:
        order = db.query(CustomerOrder).filter(CustomerOrder.order_number == body.order_number).first()
        if order:
            order_id = order.id
            company_id = order.company_id
    elif body.order_id:
        try:
            order_uuid = UUID(body.order_id)
        except ValueError:
            order_uuid = None
        if order_uuid:
            order = db.query(CustomerOrder).filter(CustomerOrder.id == order_uuid).first()
            if order:
                order_id = order.id
                company_id = order.company_id

    if body.company_name and not company_id:
        company = db.query(Company).filter(func.lower(Company.company_name) == body.company_name.lower()).first()
        if company:
            company_id = company.id

    message = body.message or body.feedback_text or body.suggestions or ""
    subject = body.subject or body.feedback_category or body.feedback_type or "Customer feedback"
    data = create_feedback_ticket(
        db,
        source="customer_site",
        order_id=order_id,
        company_id=company_id,
        feedback_type=body.feedback_type or body.feedback_category or "general",
        subject=subject,
        message=message or subject,
        priority=body.priority,
        customer_name=body.customer_name,
        customer_email=str(body.customer_email) if body.customer_email else None,
    )
    return {"message": "Feedback submitted for internal review.", "ticket": data}


@router.post("/custom-product-request")
def site_custom_product_request() -> dict[str, Any]:
    return {
        "message": "Custom product request intake is pending CRM workflow integration.",
        "request_created": False,
    }
