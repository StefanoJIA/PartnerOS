"""Unit tests for D6.3 quote totals and numbering."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.quotes.quote_totals import apply_totals_to_quote, calculate_quote_totals


def _line(total: str) -> SimpleNamespace:
    return SimpleNamespace(total_price=Decimal(total))


def _adj(type_: str, amount: str, percentage=None) -> SimpleNamespace:
    return SimpleNamespace(type=type_, amount=Decimal(amount), percentage=percentage)


def test_calculate_quote_totals_with_discount_and_tax():
    quote = SimpleNamespace(
        line_items=[_line("1000.00"), _line("500.00")],
        adjustments=[_adj("discount", "100.00"), _adj("tax", "72.00")],
    )
    totals = calculate_quote_totals(quote)
    assert totals["subtotal"] == Decimal("1500.00")
    assert totals["discount_total"] == Decimal("100.00")
    assert totals["tax_total"] == Decimal("72.00")
    assert totals["grand_total"] == Decimal("1472.00")


def test_apply_totals_to_quote():
    quote = SimpleNamespace(
        line_items=[_line("200.00")],
        adjustments=[],
        subtotal=Decimal("0"),
        adjustment_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("0"),
    )
    apply_totals_to_quote(quote)
    assert quote.subtotal == Decimal("200.00")
    assert quote.grand_total == Decimal("200.00")


def test_generate_quote_number_increments():
    from datetime import date

    from app.services.quotes.quote_service import generate_quote_number

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.first.return_value = SimpleNamespace(
        quote_number="Q-2026-0005"
    )
    num = generate_quote_number(db, date(2026, 5, 23))
    assert num == "Q-2026-0085"


def test_generate_quote_number_continues_after_imported_sequence_floor():
    from datetime import date

    from app.services.quotes.quote_service import generate_quote_number

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.first.return_value = SimpleNamespace(
        quote_number="Q-2026-0085"
    )
    num = generate_quote_number(db, date(2026, 5, 23))
    assert num == "Q-2026-0086"


def test_generate_quote_number_first_of_year():
    from datetime import date

    from app.services.quotes.quote_service import generate_quote_number

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None
    num = generate_quote_number(db, date(2026, 1, 1))
    assert num == "Q-2026-0085"


def test_resolve_initial_status():
    from app.services.quotes.quote_service import resolve_initial_status

    assert resolve_initial_status(["price_tier"]) == "ready_to_send"
    assert resolve_initial_status(["manual_unit_price"]) == "internal_review"
    assert resolve_initial_status(["cost_model"]) == "internal_review"
    assert resolve_initial_status(["manual_interval_override"]) == "internal_review"


def test_manual_interval_override_updates_quote_model_reference_price():
    from app.services.quotes.quote_service import _apply_manual_interval_override, _sanitize_manual_interval_table

    rows = _sanitize_manual_interval_table(
        [
            {"min_qty": 1, "max_qty": 49, "quantity_label": "1-49", "fob_unit_price": None, "ddp_unit_price": "88.53"},
            {"min_qty": 50, "max_qty": 99, "quantity_label": "50-99", "fob_unit_price": "31.06", "ddp_unit_price": "84.99"},
            {"min_qty": 100, "max_qty": 299, "quantity_label": "100-299", "fob_unit_price": "29.82", "ddp_unit_price": "81.44"},
        ]
    )

    pricing, unit_price = _apply_manual_interval_override(
        {"quote_model": {"final_quote_stage": {}, "pricing_stage": {}}, "price_breakdown": {}},
        rows=rows,
        quantity=50,
        incoterm="DDP",
    )

    assert str(unit_price) == "84.99"
    stage = pricing["quote_model"]["final_quote_stage"]
    assert stage["selected_interval"]["quantity_label"] == "50-99"
    assert stage["line_subtotal"] == "4249.50"
    assert [row["quantity_label"] for row in stage["interval_quote_table"]] == ["1-49", "50-99", "100-299"]
    assert pricing["source"] == "manual_interval_override"
    assert "manual_interval_price_override_requires_review" in pricing["warnings"]
