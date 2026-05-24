"""Unit tests for D6.6 quote-to-order readiness."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.errors import ApiError
from app.services.quotes.order_readiness import (
    READINESS_SAFETY,
    build_quote_order_readiness,
)


def _line(*, pricing_source="price_tier", partner_id=None, requires_review=False, catalog_id=None):
    return SimpleNamespace(
        id=uuid4(),
        line_number=1,
        partner_id=partner_id or uuid4(),
        product_catalog_id=catalog_id or uuid4(),
        product_name="Desk Frame",
        quantity=10,
        unit_price=Decimal("100"),
        final_unit_price=Decimal("100"),
        total_price=Decimal("1000"),
        pricing_source=pricing_source,
        requires_review=requires_review,
        incoterm="FOB",
        color_finish=None,
        size_dimension=None,
        attributes_snapshot_json=None,
    )


def _quote(*, status="sent", expired=False, manual_sent=True, lines=None, adjustments=None):
    quote_id = uuid4()
    valid = date.today() - timedelta(days=1) if expired else date.today() + timedelta(days=21)
    now = datetime.now(timezone.utc)
    version_id = uuid4()
    export_id = uuid4()
    log_id = uuid4()
    partner_id = uuid4()

    line_list = lines or [_line(partner_id=partner_id)]
    q = SimpleNamespace(
        id=quote_id,
        quote_number="Q-2026-0001",
        status=status,
        valid_until=valid,
        manual_sent=manual_sent,
        bill_to_name="Jane",
        bill_to_company="Acme Co",
        bill_to_address="1 Main St",
        ship_to_name="",
        ship_to_company="Acme WH",
        ship_to_address="2 Ship St",
        payment_terms="Net 30 subject to confirmation",
        shipping_terms="FOB subject to confirmation",
        currency="USD",
        default_incoterm="FOB",
        subtotal=Decimal("1000"),
        adjustment_total=Decimal("0"),
        grand_total=Decimal("1000"),
        company_id=None,
        contact_id=None,
        line_items=line_list,
        adjustments=adjustments or [],
        versions=[
            SimpleNamespace(
                id=version_id,
                version_number=1,
                version_label="v1",
                created_at=now,
            )
        ],
        pdf_exports=[
            SimpleNamespace(
                id=export_id,
                status="generated",
                file_name="Quote.pdf",
                exported_at=now,
                created_at=now,
            )
        ],
        delivery_logs=[
            SimpleNamespace(
                id=log_id,
                status="recorded",
                sent_at=now,
                sent_channel="email",
            )
        ],
        is_archived=False,
    )
    return q, partner_id


def test_sent_quote_needs_customer_confirmation(monkeypatch):
    quote, partner_id = _quote()
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = quote
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=partner_id, partner_name="Partner A")
    ]
    monkeypatch.setattr(
        "app.services.quotes.order_readiness.derived_expired",
        lambda q, today=None: False,
    )

    result = build_quote_order_readiness(db, quote.id)
    assert result["readiness_status"] == "needs_customer_confirmation"
    assert result["safety"]["order_created"] is False
    assert "order_input_contract" in result
    assert result["order_input_contract"]["source_quote"]["quote_id"] == str(quote.id)


def test_ready_to_send_not_sent_is_not_ready(monkeypatch):
    quote, partner_id = _quote(status="ready_to_send", manual_sent=False)
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = quote
    db.query.return_value.filter.return_value.all.return_value = []
    monkeypatch.setattr(
        "app.services.quotes.order_readiness.derived_expired",
        lambda q, today=None: False,
    )

    result = build_quote_order_readiness(db, quote.id)
    assert result["readiness_status"] == "not_ready"
    assert "quote_not_sent" in result["blocking_items"]


def test_expired_quote_not_ready(monkeypatch):
    quote, _ = _quote(expired=True)
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = quote
    db.query.return_value.filter.return_value.all.return_value = []
    monkeypatch.setattr(
        "app.services.quotes.order_readiness.derived_expired",
        lambda q, today=None: True,
    )

    result = build_quote_order_readiness(db, quote.id)
    assert result["readiness_status"] == "not_ready"
    assert "quote_expired" in result["blocking_items"]


def test_no_pdf_not_ready(monkeypatch):
    quote, _ = _quote()
    quote.pdf_exports = []
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = quote
    db.query.return_value.filter.return_value.all.return_value = []
    monkeypatch.setattr(
        "app.services.quotes.order_readiness.derived_expired",
        lambda q, today=None: False,
    )

    result = build_quote_order_readiness(db, quote.id)
    assert result["readiness_status"] == "not_ready"
    assert "missing_pdf_export" in result["blocking_items"]


def test_manual_price_needs_internal_review(monkeypatch):
    partner_id = uuid4()
    quote, _ = _quote(lines=[_line(pricing_source="manual_unit_price", partner_id=partner_id)])
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = quote
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=partner_id, partner_name="P1")
    ]
    monkeypatch.setattr(
        "app.services.quotes.order_readiness.derived_expired",
        lambda q, today=None: False,
    )

    result = build_quote_order_readiness(db, quote.id)
    assert result["readiness_status"] == "needs_internal_review"
    assert "manual_pricing" in result["warning_items"]


def test_multi_partner_internal_review(monkeypatch):
    p1, p2 = uuid4(), uuid4()
    quote, _ = _quote(lines=[_line(partner_id=p1), _line(partner_id=p2, pricing_source="price_tier")])
    quote.line_items[1].line_number = 2
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = quote
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=p1, partner_name="P1"),
        SimpleNamespace(id=p2, partner_name="P2"),
    ]
    monkeypatch.setattr(
        "app.services.quotes.order_readiness.derived_expired",
        lambda q, today=None: False,
    )

    result = build_quote_order_readiness(db, quote.id)
    assert result["readiness_status"] == "needs_internal_review"
    assert "multi_partner_quote" in result["warning_items"]


def test_no_forbidden_phrases_in_output(monkeypatch):
    quote, partner_id = _quote()
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = quote
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=partner_id, partner_name="P1")
    ]
    monkeypatch.setattr(
        "app.services.quotes.order_readiness.derived_expired",
        lambda q, today=None: False,
    )

    result = build_quote_order_readiness(db, quote.id)
    blob = json.dumps(result).lower()
    for phrase in ("order created", "production started", "shipment created", "delivery guaranteed"):
        assert phrase not in blob


def test_invalid_quote_raises_404(monkeypatch):
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = None

    def _raise(db_, qid):
        raise ApiError("NOT_FOUND", "quote not found", status_code=404)

    monkeypatch.setattr("app.services.quotes.order_readiness.get_quote", _raise)
    with pytest.raises(ApiError) as exc:
        build_quote_order_readiness(db, uuid4())
    assert exc.value.status_code == 404
