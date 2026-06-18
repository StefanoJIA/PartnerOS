"""Tests for HOSUN catalog SKU and metadata import helpers."""

from __future__ import annotations

from pathlib import Path

from scripts.import_hosun_product_catalog import (
    DEFAULT_CLASSIFICATION,
    category_prefix,
    generate_hosun_sku,
    infer_image_url,
    load_classification,
    taxonomy,
)


def test_generate_hosun_sku_uses_intelliopus_prefix_and_model():
    sku = generate_hosun_sku(
        "HS90603PRLCZ",
        "Lifting Columns (Components)",
        "Rectangular Lifting Column 3-Stage",
    )

    assert sku == "IO-HOSUN-LC-HS90603PRLCZ"


def test_hosun_category_taxonomy_and_image_mapping():
    assert category_prefix("Dual-Motor Standing Desk Frames", "2-Stage Desk Frame") == "DF"
    assert taxonomy("Lifting Columns", "Rectangular Lifting Column 2-Stage") == (
        "lifting_systems",
        "lifting_columns",
    )
    assert infer_image_url("Lifting Columns", "Rectangular Lifting Column 3-Stage", "HS90603PRLCZ") == (
        "/desk-order-assets/products/90X60正装三节立柱-Photoroom.png"
    )


def test_load_classification_skips_missing_or_lock_files():
    assert load_classification(None) == {}
    assert load_classification(Path("~$missing.xlsx")) == {}


def test_load_real_hosun_classification_when_available():
    if not DEFAULT_CLASSIFICATION.exists():
        return

    data = load_classification(DEFAULT_CLASSIFICATION)

    assert "HS90602PRLCZ" in data
    assert data["HS90602PRLCZ"]["product_class"] == "Lifting Columns"
