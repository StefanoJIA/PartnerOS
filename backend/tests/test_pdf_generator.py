"""Tests for D6.4 quote PDF generator."""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pdfplumber
import pytest

from app.services.quotes.pdf_data_builder import PDF_SAFETY
from app.services.quotes.pdf_generator import generate_quote_pdf, pdf_text_for_audit


FORBIDDEN = (
    "guaranteed price",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
)


def _quote():
    partner_id = uuid4()
    quote_id = uuid4()
    line = SimpleNamespace(
        line_number=1,
        partner_id=partner_id,
        product_name="Test Product",
        manual_product_name=None,
        product_category="desk",
        quantity=2,
        uom="EA",
        unit_price=Decimal("150"),
        final_unit_price=Decimal("150"),
        total_price=Decimal("300"),
        currency="USD",
        incoterm="FOB",
        color_finish=None,
        size_dimension=None,
        internal_cost=Decimal("80"),
        estimated_margin=Decimal("70"),
        pricing_breakdown_json={"hidden": True},
    )
    quote = SimpleNamespace(
        id=quote_id,
        quote_number="Q-2026-0001",
        quote_date=date.today(),
        valid_until=date.today() + timedelta(days=21),
        status="ready_to_send",
        manual_sent=False,
        currency="USD",
        default_incoterm="FOB",
        bill_to_company="Test Co",
        bill_to_name="Alice",
        bill_to_address="123 Test Ave",
        ship_to_company="Test Co",
        ship_to_name="",
        ship_to_address="123 Test Ave",
        payment_terms="Subject to confirmation",
        shipping_terms="Subject to confirmation",
        customer_notes="",
        subtotal=Decimal("300"),
        tax_total=Decimal("0"),
        grand_total=Decimal("300"),
        line_items=[line],
        adjustments=[],
        terms=None,
    )
    return quote, partner_id


def test_generate_quote_pdf_creates_file(tmp_path, monkeypatch):
    quote, partner_id = _quote()
    user = SimpleNamespace(id=uuid4())
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=partner_id, partner_name="Partner X")
    ]

    monkeypatch.setattr("app.services.quotes.pdf_generator.get_quote", lambda db_, qid: quote)
    monkeypatch.setattr("app.services.quotes.pdf_data_builder.get_quote", lambda db_, qid: quote)

    result = generate_quote_pdf(db, quote.id, output_dir=tmp_path, user=user)
    assert result["status"] == "generated"
    assert result["file_size_bytes"] > 0
    assert Path(result["file_path"]).is_file()
    assert result["safety"] == PDF_SAFETY
    db.commit.assert_called()


def test_generate_quote_pdf_no_forbidden_phrases(tmp_path, monkeypatch):
    quote, partner_id = _quote()
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=partner_id, partner_name="Partner X")
    ]
    monkeypatch.setattr("app.services.quotes.pdf_generator.get_quote", lambda db_, qid: quote)
    monkeypatch.setattr("app.services.quotes.pdf_data_builder.get_quote", lambda db_, qid: quote)

    result = generate_quote_pdf(db, quote.id, output_dir=tmp_path)
    path = Path(result["file_path"])
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "").lower()
    assert not any(p in text for p in FORBIDDEN)
    assert "intellioffice" in text or "intelliopus" in text
