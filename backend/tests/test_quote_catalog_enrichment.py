from decimal import Decimal

from app.services.quotes.catalog_enrichment import (
    PROFIT_MARGIN_TIERS,
    infer_margin_strategy,
    infer_configuration_summary,
    suggest_internal_sku,
)


def test_infers_combination_workstation_per_side_load_and_model_dimensions():
    summary = infer_configuration_summary(
        name="Rectangular Column Combination Workstation Frame 2-Stage",
        category="lifting_systems",
        product_family="benching_frames",
        partner_model="HS80502PRCWSZ",
        attrs={},
    )

    assert summary["stage"] == "2-stage"
    assert summary["dimensions"] == "80x50mm"
    assert summary["load_capacity"] == "120 kg / 265 lb"
    assert summary["total_estimated_load_capacity"] == "240 kg / 529 lb"
    assert summary["load_capacity_basis"] == "combination_workstation_per_side_two_leg_standard"


def test_infers_heavy_duty_load_and_inch_dimensions():
    summary = infer_configuration_summary(
        name="2-Stage Dual-Motor Rectangular 3.54''x2.36'' Heavy Duty Desk Frame 300kg Capacity",
        category="lifting_systems",
        product_family="heavy_duty_desk_frames",
        partner_model=None,
        attrs={},
    )

    assert summary["stage"] == "2-stage"
    assert summary["dimensions"] == "Rectangular 3.54x2.36 in"
    assert summary["load_capacity"] == "300 kg / 661 lb"
    assert summary["load_capacity_basis"] == "heavy_duty_rule"


def test_quote_catalog_sku_rule_and_profit_margin_table():
    assert suggest_internal_sku(
        partner_code="HOSUN",
        product_family="desk_frames",
        partner_model="HS90602PRDDFZ",
        name="Desk Frame",
    ) == "HS90602PRDDFZ"
    assert suggest_internal_sku(
        partner_code="JOOBOO",
        product_family="project_furniture",
        partner_model="JO-CHAIR-001",
        name="Classroom Chair",
    ) == "JO-CHAIR-001"

    lookup = {(code, min_qty, max_qty): multiplier for code, _name, min_qty, max_qty, multiplier in PROFIT_MARGIN_TIERS}
    assert lookup[("traffic", 1, 49)] == Decimal("1.10")
    assert lookup[("traffic", 500, None)] == Decimal("1.02")
    assert lookup[("volume", 1, 49)] == Decimal("1.25")
    assert lookup[("volume", 500, None)] == Decimal("1.10")
    assert lookup[("profit", 1, 49)] == Decimal("1.50")
    assert lookup[("profit", 500, None)] == Decimal("1.30")


def test_margin_strategy_classification_fills_target_margin():
    assert infer_margin_strategy(
        name="2-Stage Single-Motor Rectangular Desk Frame 80x50mm",
        category="lifting_systems",
        product_family="desk_frames",
    ) == ("traffic", "entry_or_traffic_product", Decimal("0.08"))
    assert infer_margin_strategy(
        name="2-Stage Dual-Motor Rectangular Desk Frame 90x60mm",
        category="lifting_systems",
        product_family="desk_frames",
    ) == ("volume", "mainstream_volume_product", Decimal("0.20"))
    assert infer_margin_strategy(
        name="2-Stage Four-Motor Face-to-Face Rectangular Benching Frame",
        category="lifting_systems",
        product_family="benching_frames",
    ) == ("profit", "technical_or_project_complexity", Decimal("0.45"))
