"""Production milestone templates for customer orders (D7.5)."""

from __future__ import annotations

from typing import Any

LIFTING_CATEGORIES = frozenset(
    {
        "lifting_frame",
        "desk_legs",
        "lifting_columns",
        "heavy_duty_lifting_system",
        "oem_odm_component",
    }
)

EDUCATION_CATEGORIES = frozenset(
    {
        "education_desk",
        "education_chair",
        "education_set",
    }
)

MILESTONE_LABELS: dict[str, str] = {
    "order_received": "Order Received",
    "supplier_confirmed": "Supplier Confirmed",
    "materials_prepared": "Materials Prepared",
    "cutting": "Cutting",
    "welding": "Welding",
    "painting": "Painting",
    "assembly": "Assembly",
    "quality_check": "Quality Check",
    "packing": "Packing",
    "ready_to_ship": "Ready to Ship",
    "production_started": "Production Started",
    "production_pending": "Production Pending",
    "custom": "Custom",
}


def _item(milestone_type: str, sequence: int) -> dict[str, Any]:
    return {
        "milestone_type": milestone_type,
        "milestone_label": MILESTONE_LABELS.get(milestone_type, milestone_type.replace("_", " ").title()),
        "sequence": sequence,
        "status": "planned",
    }


LIFTING_TEMPLATE = [
    _item("order_received", 1),
    _item("supplier_confirmed", 2),
    _item("materials_prepared", 3),
    _item("cutting", 4),
    _item("welding", 5),
    _item("painting", 6),
    _item("assembly", 7),
    _item("quality_check", 8),
    _item("packing", 9),
    _item("ready_to_ship", 10),
]

EDUCATION_TEMPLATE = [
    _item("order_received", 1),
    _item("supplier_confirmed", 2),
    _item("materials_prepared", 3),
    _item("production_started", 4),
    _item("assembly", 5),
    _item("quality_check", 6),
    _item("packing", 7),
    _item("ready_to_ship", 8),
]

GENERIC_TEMPLATE = [
    _item("order_received", 1),
    _item("supplier_confirmed", 2),
    _item("materials_prepared", 3),
    _item("production_started", 4),
    _item("quality_check", 5),
    _item("packing", 6),
    _item("ready_to_ship", 7),
]

FALLBACK_TEMPLATE = [
    _item("order_received", 1),
    _item("supplier_confirmed", 2),
    _item("production_pending", 3),
    _item("quality_check", 4),
    _item("ready_to_ship", 5),
]


def _normalize_partner_code(partner_code: str | None) -> str:
    return (partner_code or "").strip().upper()


def get_default_milestone_template(
    partner_code: str | None,
    product_category: str | None,
    *,
    partner_type: str | None = None,
) -> list[dict[str, Any]]:
    """Return milestone template items for a partner split."""
    code = _normalize_partner_code(partner_code)
    category = (product_category or "").strip().lower()
    ptype = (partner_type or "").strip().lower()

    if category in LIFTING_CATEGORIES or "lifting" in ptype or "metal" in ptype:
        return [dict(x) for x in LIFTING_TEMPLATE]
    if category in EDUCATION_CATEGORIES or "education" in ptype or "furniture" in ptype:
        return [dict(x) for x in EDUCATION_TEMPLATE]
    if category in ("generic", "project_supply", "office_furniture"):
        return [dict(x) for x in GENERIC_TEMPLATE]
    if category:
        return [dict(x) for x in GENERIC_TEMPLATE]
    if code:
        return [dict(x) for x in GENERIC_TEMPLATE]
    return [dict(x) for x in FALLBACK_TEMPLATE]
