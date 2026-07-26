"""Tests for latest HOSUN classification catalog sync helpers."""

from __future__ import annotations

from scripts.sync_hosun_classification_catalog import (
    ADDITIONAL_HOSUN_PRODUCTS,
    additional_hosun_rows,
    load_classification_rows,
    resolve_default_classification,
    taxonomy,
)


def test_latest_classification_workbook_loads_when_available():
    path = resolve_default_classification()
    rows = load_classification_rows(path)

    assert len(rows) >= 50
    assert rows[0]["model"] == "HS90602PRLCZ"
    assert rows[0]["name"] == "Rectangular Lifting Column 2-Stage 60*90mm"
    assert rows[0]["load_capacity"] == "60kg"


def test_classification_taxonomy_keeps_hosun_lifting_system_families():
    assert taxonomy("Lifting Columns", "Rectangular Lifting Column 2-Stage 60*90mm") == (
        "lifting_systems",
        "lifting_columns",
    )
    assert taxonomy("Dual-Motor Standing Desk Frames", "Rectangular Column Dual Motor Desk Frame 2-Stage") == (
        "lifting_systems",
        "desk_frames",
    )
    assert taxonomy("Combination Workstation", "Square Column Combination Workstation Frame 2-Stage") == (
        "lifting_systems",
        "benching_frames",
    )


def test_hosun_fixed_accessory_rows_are_part_of_active_catalog_scope():
    rows = additional_hosun_rows()
    models = {row["model"] for row in rows}

    assert len(ADDITIONAL_HOSUN_PRODUCTS) == 6
    assert {"HS11A", "HS11B", "HS11C", "HS11D", "HS11E", "SWATCH-4COLOR"} == models
    assert taxonomy("Hand Control Panel", "Hand Control Panel HS11A") == (
        "lifting_systems",
        "desk_accessories",
    )
    assert taxonomy("Color Swatch Sample", "Four Color Roll Swatch Sample Set") == (
        "lifting_systems",
        "desk_accessories",
    )
