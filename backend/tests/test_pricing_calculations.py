"""Unit tests for pricing calculations (D6.2)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.quotes.pricing_calculations import (
    apply_discount,
    compute_cost_breakdown,
    compute_profit,
    qty_in_tier,
    tier_unit_price,
)


def test_qty_in_tier():
    assert qty_in_tier(50, 50, 99)
    assert not qty_in_tier(49, 50, 99)
    assert qty_in_tier(500, 500, None)


def test_tier_unit_price_final():
    assert tier_unit_price(base_unit_price=Decimal("100"), adjustment_value=None, final_unit_price=Decimal("110")) == Decimal("110")


def test_apply_discount_percentage():
    final, disc = apply_discount(Decimal("100"), 10, {"type": "percentage", "value": 5})
    assert final == Decimal("95.0000")
    assert disc == Decimal("50.00")


def test_compute_cost_breakdown_cny():
    breakdown, fob = compute_cost_breakdown(
        unit_material_cost=Decimal("720"),
        cost_currency="CNY",
        unit_weight=Decimal("10"),
        ocean_freight_unit_price=Decimal("2"),
        domestic_transport_cost=Decimal("40"),
        domestic_profit_rate=Decimal("0.1"),
        fx_rate_usd_cny=Decimal("7.2"),
        stored_fob_cost_usd=None,
        stored_ddp_cost_usd=None,
    )
    assert fob is not None
    assert breakdown["fob_cost_usd"] != "0.00"


def test_compute_cost_breakdown_missing_fx():
    with pytest.raises(ValueError, match="FX_RATE_MISSING"):
        compute_cost_breakdown(
            unit_material_cost=Decimal("720"),
            cost_currency="CNY",
            unit_weight=Decimal("10"),
            ocean_freight_unit_price=Decimal("2"),
            domestic_transport_cost=Decimal("40"),
            domestic_profit_rate=Decimal("0.1"),
            fx_rate_usd_cny=None,
            stored_fob_cost_usd=None,
            stored_ddp_cost_usd=None,
        )


def test_compute_profit():
    total, margin = compute_profit(Decimal("100"), Decimal("70"), 10)
    assert total == "300.00"
    assert margin == "30.00"
