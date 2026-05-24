"""API tests for D6.4 Quote PDF export."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User
from app.models.customer_quotes import Quote, QuoteLineItem, QuotePdfExport


@pytest.fixture
def pdf_client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="pdf@test.example", is_active=True)
    quote_id = uuid4()
    export_id = uuid4()

    quote = Quote(
        id=quote_id,
        quote_number="Q-2026-0001",
        quote_date=date.today(),
        valid_until=date.today() + timedelta(days=21),
        status="ready_to_send",
        currency="USD",
        subtotal=Decimal("100"),
        adjustment_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("100"),
    )
    quote.line_items = [
        QuoteLineItem(
            id=uuid4(),
            quote_id=quote_id,
            line_number=1,
            partner_id=uuid4(),
            product_name="Item",
            quantity=1,
            unit_price=Decimal("100"),
            final_unit_price=Decimal("100"),
            total_price=Decimal("100"),
            pricing_source="price_tier",
        )
    ]
    quote.adjustments = []
    quote.versions = []

    export_record = QuotePdfExport(
        id=export_id,
        quote_id=quote_id,
        export_type="customer_pdf",
        file_name="Quote_Q-2026-0001_v1_20260524.pdf",
        file_path="/tmp/missing.pdf",
        file_size_bytes=100,
        status="generated",
    )

    db = MagicMock()

    def _get_quote(db_, qid):
        if qid == quote_id:
            return quote
        from app.core.errors import ApiError, NOT_FOUND
        raise ApiError(NOT_FOUND, "not found", status_code=404)

    monkeypatch.setattr("app.api.v1.routes.quote_pdf.get_quote", _get_quote)
    monkeypatch.setattr(
        "app.api.v1.routes.quote_pdf.generate_quote_pdf",
        lambda db, qid, **kw: {
            "export_id": str(export_id),
            "file_name": export_record.file_name,
            "content_type": "application/pdf",
            "file_size_bytes": 1234,
            "safety": {
                "automatic_sending_enabled": False,
                "inventory_promised": False,
                "certification_promised": False,
                "lead_time_promised": False,
                "order_created": False,
            },
        },
    )

    def _query(model):
        q = MagicMock()
        if model is QuotePdfExport:
            q.filter.return_value.order_by.return_value.all.return_value = [export_record]
            q.filter.return_value.first.return_value = export_record
        return q

    db.query.side_effect = _query

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)
    yield client, quote_id, export_id
    app.dependency_overrides.clear()


def test_export_pdf_returns_download_url(pdf_client):
    client, quote_id, export_id = pdf_client
    r = client.post(f"/api/v1/quotes/{quote_id}/export-pdf", json={"export_type": "customer_pdf"})
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["export_id"] == str(export_id)
    assert "download_url" in data
    assert data["safety"]["automatic_sending_enabled"] is False


def test_list_pdf_exports(pdf_client):
    client, quote_id, export_id = pdf_client
    r = client.get(f"/api/v1/quotes/{quote_id}/pdf-exports")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["export_id"] == str(export_id)


def test_download_wrong_quote_returns_404(pdf_client):
    client, quote_id, export_id = pdf_client
    other = uuid4()
    r = client.get(f"/api/v1/quotes/{other}/pdf-exports/{export_id}/download")
    assert r.status_code == 404
