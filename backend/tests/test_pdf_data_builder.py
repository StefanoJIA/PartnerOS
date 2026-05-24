"""Unit tests for D6.4 quote PDF data builder."""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services.quotes.pdf_data_builder import build_quote_pdf_data, PDF_SAFETY


def _quote_with_internal():
    partner_id = uuid4()
    quote_id = uuid4()
    line = SimpleNamespace(
        line_number=1,
        partner_id=partner_id,
        product_name="Desk Frame",
        manual_product_name=None,
        product_category="lifting_frame",
        quantity=10,
        uom="EA",
        unit_price=Decimal("100"),
        final_unit_price=Decimal("100"),
        total_price=Decimal("1000"),
        currency="USD",
        incoterm="FOB",
        color_finish="Black",
        size_dimension="48in",
        internal_cost=Decimal("50"),
        estimated_margin=Decimal("50"),
        pricing_breakdown_json={"secret": True},
    )
    quote = SimpleNamespace(
        id=quote_id,
        quote_number="Q-2026-0001",
        quote_date=date.today(),
        valid_until=date.today() + timedelta(days=21),
        status="ready_to_send",
        currency="USD",
        default_incoterm="FOB",
        bill_to_company="Acme",
        bill_to_name="Jane",
        bill_to_address="1 Main St",
        ship_to_company="Acme WH",
        ship_to_name="",
        ship_to_address="2 Ship St",
        payment_terms="Net 30 subject to confirmation",
        shipping_terms="Subject to confirmation",
        customer_notes="",
        subtotal=Decimal("1000"),
        tax_total=Decimal("0"),
        grand_total=Decimal("1000"),
        line_items=[line],
        adjustments=[],
        terms=None,
    )
    return quote, partner_id


def test_build_quote_pdf_data_excludes_internal_fields(monkeypatch):
    quote, partner_id = _quote_with_internal()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=partner_id, partner_name="Partner A")
    ]

    monkeypatch.setattr("app.services.quotes.pdf_data_builder.get_quote", lambda db_, qid: quote)

    data = build_quote_pdf_data(db, quote.id)
    blob = json.dumps(data).lower()
    assert "internal_cost" not in blob
    assert "estimated_margin" not in blob
    assert "pricing_breakdown_json" not in blob
    assert "cost_snapshot_json" not in blob
    assert data["line_items"][0]["partner"] == "Partner A"
    assert data["safety"] == PDF_SAFETY


def test_build_quote_pdf_data_uses_version_snapshot(monkeypatch):
    quote, partner_id = _quote_with_internal()
    version_id = uuid4()
    snapshot = {
        "quote_number": "Q-2026-0099",
        "quote_date": "2026-05-01",
        "valid_until": "2026-05-22",
        "currency": "USD",
        "bill_to": {"company": "Snap Co", "name": "Bob", "address": "Addr"},
        "ship_to": {"company": "", "name": "", "address": ""},
        "line_items": [
            {
                "line_number": 1,
                "partner_id": str(partner_id),
                "product_name": "From Snapshot",
                "quantity": 5,
                "final_unit_price": "200",
                "total_price": "1000",
                "internal_cost": "99",
                "estimated_margin": "50",
                "pricing_breakdown_json": {"x": 1},
            }
        ],
        "adjustments": [],
        "totals": {"subtotal": "1000", "tax_total": "0", "grand_total": "1000"},
        "terms": {"payment_terms": "Subject to confirmation", "shipping_terms": "Subject to confirmation"},
    }
    version = SimpleNamespace(id=version_id, quote_id=quote.id, version_number=2, version_label="v2", snapshot_json=snapshot)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = version
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=partner_id, partner_name="HOSUN")
    ]

    monkeypatch.setattr("app.services.quotes.pdf_data_builder.get_quote", lambda db_, qid: quote)

    data = build_quote_pdf_data(db, quote.id, version_id=version_id)
    assert data["quote"]["quote_number"] == "Q-2026-0099"
    assert data["line_items"][0]["product_name"] == "From Snapshot"
    assert data["version"]["version_number"] == 2
    assert "internal_cost" not in json.dumps(data).lower()
