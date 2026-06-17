"""Tests for workbook-aligned quote model preview flow."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.services.quotes import pricing_service


def test_pricing_preview_returns_quote_model_snapshot(monkeypatch):
    product_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        product_name="3-Stage Dual-Motor Rectangular Desk Frame",
        product_category="lifting_frame",
        product_family="lifting_systems",
    )
    cost = SimpleNamespace(
        unit_material_cost=Decimal("950"),
        cost_currency="CNY",
        unit_weight=Decimal("30"),
        ocean_freight_unit_price=Decimal("22"),
        domestic_transport_cost=None,
        domestic_profit_rate=Decimal("0.09"),
        fob_cost_usd=None,
        ddp_cost_usd=None,
    )
    fx = SimpleNamespace(
        base_currency="USD",
        quote_currency="CNY",
        rate=Decimal("6.7"),
        rate_date=date(2026, 1, 23),
        source="workbook_fixture",
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = product

    monkeypatch.setattr(pricing_service, "_select_price_tier", lambda *args, **kwargs: None)
    monkeypatch.setattr(pricing_service, "_select_cost_model", lambda *args, **kwargs: cost)
    monkeypatch.setattr(pricing_service, "get_latest_fx", lambda *args, **kwargs: fx)
    monkeypatch.setattr(
        pricing_service,
        "_select_margin_multiplier",
        lambda *args, **kwargs: (Decimal("1.15"), []),
    )

    result = pricing_service.calculate_line_price(
        db,
        product_id=product_id,
        quantity=100,
        incoterm="DDP",
        pricing_strategy="volume",
        discount={"type": "percentage", "value": 5},
    )

    model = result["quote_model"]
    assert [step["step"] for step in model["workflow"]] == [
        "cost",
        "logistics",
        "fx",
        "price_tier",
        "profit_check",
        "customer_quote",
    ]
    assert result["source"] == "cost_model"
    assert result["cost_breakdown"]["freight_cost_usd"] == "98.51"
    assert model["cost_stage"]["selected_cost_basis_usd"] == result["cost_breakdown"]["ddp_cost_usd"]
    assert model["final_quote_stage"]["line_subtotal"] == result["price_breakdown"]["line_subtotal"]
    assert model["profit_stage"]["internal_only"] is True
    assert model["final_quote_stage"]["customer_visible"] is True
    assert model["safety"]["automatic_sending_enabled"] is False
