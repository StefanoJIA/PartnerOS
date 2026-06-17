"""Tests for workbook-aligned quote model preview flow."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.services.quotes import pricing_service


def test_product_interval_quote_table_groups_by_product_range():
    product_id = uuid4()
    tiers = [
        SimpleNamespace(
            id=uuid4(),
            product_id=product_id,
            min_qty=1,
            max_qty=49,
            incoterm="DDP",
            currency="USD",
            pricing_strategy="volume",
            final_unit_price=Decimal("180.00"),
            base_unit_price=None,
            adjustment_value=None,
            effective_from=None,
            effective_to=None,
            source="workbook",
        ),
        SimpleNamespace(
            id=uuid4(),
            product_id=product_id,
            min_qty=50,
            max_qty=99,
            incoterm="FOB",
            currency="USD",
            pricing_strategy="volume",
            final_unit_price=Decimal("120.00"),
            base_unit_price=None,
            adjustment_value=None,
            effective_from=None,
            effective_to=None,
            source="workbook",
        ),
        SimpleNamespace(
            id=uuid4(),
            product_id=product_id,
            min_qty=50,
            max_qty=99,
            incoterm="DDP",
            currency="USD",
            pricing_strategy="volume",
            final_unit_price=Decimal("158.00"),
            base_unit_price=None,
            adjustment_value=None,
            effective_from=None,
            effective_to=None,
            source="workbook",
        ),
        SimpleNamespace(
            id=uuid4(),
            product_id=product_id,
            min_qty=100,
            max_qty=None,
            incoterm="FOB",
            currency="USD",
            pricing_strategy="volume",
            final_unit_price=Decimal("110.00"),
            base_unit_price=None,
            adjustment_value=None,
            effective_from=None,
            effective_to=None,
            source="workbook",
        ),
    ]
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = tiers

    table = pricing_service.build_product_interval_quote_table(
        db,
        product_id=product_id,
        pricing_strategy="volume",
    )

    assert [row["quantity_label"] for row in table] == ["1-49", "50-99", ">=100"]
    assert table[0]["fob_unit_price"] is None
    assert table[0]["ddp_unit_price"] == "180.00"
    assert table[1]["fob_unit_price"] == "120.00"
    assert table[1]["ddp_unit_price"] == "158.00"
    assert table[2]["fob_unit_price"] == "110.00"


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
    monkeypatch.setattr(
        pricing_service,
        "build_product_interval_quote_table",
        lambda *args, **kwargs: [
            {
                "min_qty": 1,
                "max_qty": 49,
                "quantity_label": "1-49",
                "currency": "USD",
                "fob_unit_price": None,
                "ddp_unit_price": "180.00",
                "incoterms_available": ["DDP"],
                "customer_visible": True,
            },
            {
                "min_qty": 50,
                "max_qty": 99,
                "quantity_label": "50-99",
                "currency": "USD",
                "fob_unit_price": "120.00",
                "ddp_unit_price": "158.00",
                "incoterms_available": ["FOB", "DDP"],
                "customer_visible": True,
            },
            {
                "min_qty": 100,
                "max_qty": 299,
                "quantity_label": "100-299",
                "currency": "USD",
                "fob_unit_price": "112.00",
                "ddp_unit_price": "150.00",
                "incoterms_available": ["FOB", "DDP"],
                "customer_visible": True,
            },
        ],
    )
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
    assert model["final_quote_stage"]["interval_quote_table"][2]["quantity_label"] == "100-299"
    assert model["final_quote_stage"]["selected_interval"]["quantity_label"] == "100-299"
    assert model["profit_stage"]["internal_only"] is True
    assert model["final_quote_stage"]["customer_visible"] is True
    assert model["safety"]["automatic_sending_enabled"] is False
