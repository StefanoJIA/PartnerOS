"""Tests for HOSUN cost-to-catalog mapping definitions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.api.v1.routes.products import _product_payload
from app.models import FxRate, ProductCatalog, ProductCostModel
from app.services.quotes.pricing_assumptions import PricingAssumptionSnapshot
from scripts.backfill_hosun_cost_mappings import HOSUN_COST_MAPPINGS


def _mapping(source_name: str):
    return next(row for row in HOSUN_COST_MAPPINGS if row.source_name == source_name)


def test_heavy_duty_cost_row_maps_to_heavy_duty_sku_and_quote_name():
    row = _mapping("2-Stage Dual-Motor Rectangular Desk Frame 90x60mm 300kg Capacity")

    assert "IO-HOSUN-HD-HS90602HRDDFZ" in row.target_skus
    assert "2-Stage Dual-Motor Rectangular 3.54''×2.36'' Heavy Duty Desk Frame" in row.target_names
    assert "2-Stage Dual-Motor Rectangular 3.54''×2.36'' Heavy Duty Desk Frame" in row.price_source_names


def test_3_stage_90x60_cost_row_maps_to_catalog_model_and_quote_name():
    row = _mapping("3-Stage Dual-Motor Rectangular Desk Frame 90x60mm")

    assert "IO-HOSUN-DF-HS90603PRDDFZ" in row.target_skus
    assert "3-Stage Dual-Motor Rectangular 3.54''×2.36'' Desk Frame" in row.target_names


def test_benching_cost_rows_map_to_rectangular_and_square_catalog_skus():
    two_stage = _mapping("2-Stage Four-Motor Face-to-Face Rectangular Benching Frame 80x50mm / 70x70mm")
    three_stage = _mapping("3-Stage Four-Motor Face-to-Face Rectangular Benching Frame 80x50mm / 70x70mm")

    assert {"IO-HOSUN-BF-HS80502PRCWSZ", "IO-HOSUN-BF-HS70702PRCWSZ"}.issubset(two_stage.target_skus)
    assert {"IO-HOSUN-BF-HS80503PRCWSZ", "IO-HOSUN-BF-HS70703PRCWSZ"}.issubset(three_stage.target_skus)


def test_3_leg_cost_row_maps_to_existing_l_shape_catalog_skus():
    row = _mapping("3-Leg 3-Stage Triple-Motor Rectangular Desk Frame 90x60mm")

    assert {"IO-HOSUN-LS-HS80503PRTDFZ", "IO-HOSUN-LS-HS70703PRTDFZ"}.issubset(row.target_skus)
    assert "IO-HOSUN-LS-HS90603PRTDFZ" not in row.target_skus


def test_80x50_70x70_cost_row_uses_customer_quote_interval_source():
    row = _mapping("2-Stage Dual-Motor Rectangular Desk Frame 80x50mm / 70x70mm")

    assert {"IO-HOSUN-DF-HS80502PRDDFZ", "IO-HOSUN-DF-HS70702PRDDFZ"}.issubset(row.target_skus)
    assert "2-Stage Dual-Motor Rectangular 3.15''×1.97'' / Square 2.76'' Desk Frame" in row.price_source_names


def test_product_payload_exposes_internal_pricing_model_summary():
    product_id = uuid4()
    product = ProductCatalog(
        id=product_id,
        partner_id=uuid4(),
        internal_sku="IO-HOSUN-HD-HS90602HRDDFZ",
        product_name="2-Stage Dual-Motor Rectangular Heavy-Duty Frame",
        product_category="lifting_systems",
        status="active",
        default_uom="EA",
        base_currency="USD",
        attributes_json={
            "customer_safe_pricing_mode": "full_quantity_interval_quote_table",
            "target_margin": "0.25",
        },
    )
    cost_model = ProductCostModel(
        product_id=product_id,
        cost_currency="RMB",
        unit_material_cost=Decimal("1199"),
        unit_weight=Decimal("35"),
        ocean_freight_unit_price=Decimal("18"),
        domestic_transport_cost=Decimal("999"),
        fob_cost_usd=Decimal("1.00"),
        ddp_cost_usd=Decimal("2.00"),
    )
    fx = FxRate(
        base_currency="USD",
        quote_currency="CNY",
        rate=Decimal("6.70"),
        rate_date=date.today(),
        source="manual",
    )
    assumptions = PricingAssumptionSnapshot(
        ocean_freight_unit_price=Decimal("22"),
        ocean_freight_unit="RMB/kg",
        ocean_freight_source="manual_provider_quote",
        ocean_freight_effective_from=date.today(),
        fallback_used=False,
    )

    payload = _product_payload(
        product,
        partner=None,
        quote_interval_count=9,
        cost_model=cost_model,
        latest_fx=fx,
        assumptions=assumptions,
    )
    summary = payload["pricing_model_summary"]

    assert payload["quote_interval_count"] == 9
    assert payload["has_interval_pricing"] is True
    assert summary["internal_only"] is True
    assert summary["factory_cost_rmb"] == "1199.00"
    assert summary["unit_weight_kg"] == "35.0000"
    assert summary["ocean_freight_unit_price"] == "22.0000"
    assert summary["domestic_transport_cost_rmb"] == "770.00"
    assert summary["fob_cost_usd"] == "178.96"
    assert summary["ddp_cost_usd"] == "293.88"
    assert summary["stored_fob_cost_usd_snapshot"] == "1.00"
    assert summary["stored_ddp_cost_usd_snapshot"] == "2.00"
    assert summary["stored_cost_snapshot_used"] is False
    assert summary["product_target_margin_percent"] == "25.00"
