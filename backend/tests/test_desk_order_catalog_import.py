"""Safety tests for desk-order product catalog import."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.import_desk_order_catalog import DEFAULT_SEED, _category_family, _parse_description


def test_desk_order_product_seed_is_product_only():
    payload = json.loads(Path(DEFAULT_SEED).read_text(encoding="utf-8"))
    assert payload["safety"]["contains_customers"] is False
    assert payload["safety"]["contains_orders"] is False
    assert payload["safety"]["contains_admins"] is False
    assert payload["safety"]["contains_tokens"] is False
    assert "customers" not in payload
    assert "orders" not in payload
    assert "admins" not in payload
    assert len(payload["products"]) >= 50
    assert len(payload["color_options"]) >= 80


def test_description_parser_extracts_desk_order_specs():
    parsed = _parse_description(
        "\n".join(
            [
                "Chinese Name: 80x50正装两节方管立柱",
                "Specification: 80*50",
                "Stages: 2",
                "Lifting Range: 710~1190mm",
                "Load Capacity: 120kg",
            ]
        )
    )
    assert parsed["specification"] == "80*50"
    assert parsed["stages"] == "2"
    assert parsed["load_capacity"] == "120kg"


def test_category_mapping_keeps_hosun_and_jooboo_extensible():
    assert _category_family("Lifting Columns", "Rectangular Lifting Column")[1] == "lifting_columns"
    assert _category_family("Dual-Motor Standing Desk Frames", "Heavy Duty Desk Frame")[1] == "heavy_duty_supply"
    assert _category_family("Education Furniture", "School Classroom Desk")[0] == "education_furniture"
