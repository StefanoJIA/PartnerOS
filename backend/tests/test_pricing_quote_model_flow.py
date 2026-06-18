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


def test_product_interval_quote_table_can_be_generated_from_landed_cost(monkeypatch):
    product_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        product_name="Cost Model Desk Frame",
        product_category="lifting_frame",
        product_family="lifting_systems",
        attributes_json={"quote_markup_multiplier": "1.25"},
    )
    cost = SimpleNamespace(
        unit_material_cost=Decimal("720"),
        cost_currency="CNY",
        unit_weight=Decimal("10"),
        ocean_freight_unit_price=Decimal("2"),
        domestic_transport_cost=Decimal("40"),
        domestic_profit_rate=Decimal("0.10"),
        fob_cost_usd=None,
        ddp_cost_usd=None,
        effective_from=None,
        effective_to=None,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    table = pricing_service.build_product_interval_quote_table(
        db,
        product_id=product_id,
        product=product,
        cost_model=cost,
        pricing_strategy="volume",
        fx_rate_usd_cny=Decimal("7.2"),
    )

    assert [row["quantity_label"] for row in table] == ["1-49", "50-99", "100-299", "300-499", ">=500"]
    assert table[0]["fob_unit_price"] == "137.50"
    assert table[0]["ddp_unit_price"] == "144.45"
    assert table[1]["fob_unit_price"] == "133.38"
    assert table[-1]["pricing_basis"] == "cost_plus_landed_cost"
    assert table[-1]["internal_pricing_basis"]["internal_only"] is True


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
    assert result["source"] == "price_interval"
    assert result["cost_breakdown"]["freight_cost_usd"] == "98.51"
    assert model["cost_stage"]["selected_cost_basis_usd"] == result["cost_breakdown"]["ddp_cost_usd"]
    assert model["final_quote_stage"]["line_subtotal"] == result["price_breakdown"]["line_subtotal"]
    assert model["final_quote_stage"]["interval_quote_table"][2]["quantity_label"] == "100-299"
    assert model["final_quote_stage"]["selected_interval"]["quantity_label"] == "100-299"
    assert model["profit_stage"]["internal_only"] is True
    assert model["final_quote_stage"]["customer_visible"] is True
    assert model["safety"]["automatic_sending_enabled"] is False


def test_pricing_preview_uses_generated_interval_price_for_reference_quantity():
    product_id = uuid4()
    product = SimpleNamespace(
        id=product_id,
        product_name="Generated Range Desk Frame",
        product_category="lifting_frame",
        product_family="lifting_systems",
        attributes_json={"quote_markup_multiplier": "1.25"},
    )
    cost = SimpleNamespace(
        unit_material_cost=Decimal("720"),
        cost_currency="CNY",
        unit_weight=Decimal("10"),
        ocean_freight_unit_price=Decimal("2"),
        domestic_transport_cost=Decimal("40"),
        domestic_profit_rate=Decimal("0.10"),
        fob_cost_usd=None,
        ddp_cost_usd=None,
        effective_from=None,
        effective_to=None,
    )
    fx = SimpleNamespace(
        base_currency="USD",
        quote_currency="CNY",
        rate=Decimal("7.2"),
        rate_date=date.today(),
        source="test",
    )
    db = MagicMock()

    def query_side_effect(model):
        if model is pricing_service.ProductCatalog:
            return SimpleNamespace(filter=lambda *args, **kwargs: SimpleNamespace(first=lambda: product))
        if model is pricing_service.ProductPriceTier:
            return SimpleNamespace(
                filter=lambda *args, **kwargs: SimpleNamespace(
                    order_by=lambda *args, **kwargs: SimpleNamespace(all=lambda: [])
                )
            )
        return MagicMock()

    db.query.side_effect = query_side_effect
    db.query.return_value.filter.return_value.first.return_value = product

    # Keep the fallback cost source explicit so this test is about quote math, not query plumbing.
    import app.services.quotes.pricing_service as svc

    original_select_cost = svc._select_cost_model
    svc._select_cost_model = lambda *args, **kwargs: cost
    original_fx = svc.get_latest_fx
    svc.get_latest_fx = lambda *args, **kwargs: fx
    try:
        result = svc.calculate_line_price(
            db,
            product_id=product_id,
            quantity=50,
            incoterm="DDP",
            pricing_strategy="volume",
        )
    finally:
        svc._select_cost_model = original_select_cost
        svc.get_latest_fx = original_fx

    rows = result["quote_model"]["final_quote_stage"]["interval_quote_table"]
    selected = result["quote_model"]["final_quote_stage"]["selected_interval"]
    assert result["source"] == "cost_model_interval"
    assert selected["quantity_label"] == "50-99"
    assert result["price_breakdown"]["base_unit_price"] == selected["ddp_unit_price"]
    assert [row["quantity_label"] for row in rows] == ["1-49", "50-99", "100-299", "300-499", ">=500"]
    assert result["quote_model"]["final_quote_stage"]["reference_quantity_only"] is True
