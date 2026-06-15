"""API tests for D6.3 Customer Quote CRUD."""

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
from app.models import ProductCatalog, User
from app.models.customer_quotes import Quote, QuoteLineItem, QuoteVersion


@pytest.fixture
def quote_client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="q@test.example", is_active=True)
    product_id = uuid4()
    partner_id = uuid4()
    quote_id = uuid4()

    product = ProductCatalog(
        id=product_id,
        partner_id=partner_id,
        internal_sku="TEST-SKU",
        product_name="Test Desk Frame",
        product_category="lifting_frame",
        status="active",
    )
    quote = Quote(
        id=quote_id,
        quote_number="Q-2026-0001",
        quote_date=date.today(),
        valid_until=date.today() + timedelta(days=21),
        status="ready_to_send",
        currency="USD",
        subtotal=Decimal("1000.00"),
        adjustment_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("1000.00"),
        payment_terms="Subject to confirmation",
        shipping_terms="Subject to confirmation",
    )
    line = QuoteLineItem(
        id=uuid4(),
        quote_id=quote_id,
        line_number=1,
        partner_id=partner_id,
        product_catalog_id=product_id,
        product_name="Test Desk Frame",
        quantity=10,
        unit_price=Decimal("100"),
        final_unit_price=Decimal("100"),
        total_price=Decimal("1000"),
        pricing_source="price_tier",
        requires_review=False,
    )
    quote.line_items = [line]
    quote.adjustments = []
    quote.versions = [QuoteVersion(id=uuid4(), quote_id=quote_id, version_number=1, version_label="v1", version_type="internal_version", status="ready_to_send", snapshot_json={}, created_at=quote.created_at if hasattr(quote, "created_at") else None)]

    db = MagicMock()

    def _get_quote(db_, qid):
        if qid == quote_id:
            return quote
        from app.core.errors import ApiError, NOT_FOUND
        raise ApiError(NOT_FOUND, "not found", status_code=404)

    monkeypatch.setattr("app.api.v1.routes.quotes.get_quote", _get_quote)
    monkeypatch.setattr(
        "app.api.v1.routes.quotes.create_quote",
        lambda db, **kw: quote,
    )
    monkeypatch.setattr(
        "app.api.v1.routes.quotes.mark_ready",
        lambda db, qid, user: quote,
    )
    monkeypatch.setattr(
        "app.api.v1.routes.quotes.mark_sent_with_delivery",
        lambda db, qid, user, **kw: {
            "quote_id": str(quote_id),
            "status": "sent",
            "delivery_log": {"id": str(uuid4()), "sent_channel": "email", "manual_sent": True},
            "warnings": [],
            "safety": {
                "automatic_sending_enabled": False,
                "email_sent_by_system": False,
                "linkedin_sent_by_system": False,
                "attachment_sent_by_system": False,
                "order_created": False,
            },
        },
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)
    with TestClient(app) as client:
        yield client, quote_id, product_id, partner_id
    app.dependency_overrides.clear()


def test_create_quote_envelope(quote_client):
    client, _, product_id, _ = quote_client
    r = client.post(
        "/api/v1/quotes",
        json={
            "line_items": [
                {"product_id": str(product_id), "quantity": 10, "incoterm": "FOB", "pricing_strategy": "volume"}
            ]
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["quote_number"] == "Q-2026-0001"
    assert body["data"]["safety"]["quote_created"] is True
    assert body["data"]["safety"]["automatic_sending_enabled"] is False


def test_mark_sent_envelope(quote_client):
    client, quote_id, _, _ = quote_client
    r = client.post(f"/api/v1/quotes/{quote_id}/mark-sent", json={"send_channel": "email"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["safety"]["automatic_sending_enabled"] is False
    assert body["data"]["status"] == "sent"


def test_quote_safety_no_forbidden_words(quote_client):
    client, quote_id, _, _ = quote_client
    r = client.get(f"/api/v1/quotes/{quote_id}")
    text = r.text.lower()
    for phrase in ("guaranteed price", "in stock", "delivery guaranteed", "lead time confirmed"):
        assert phrase not in text


def test_quote_learning_records_manual_outcome_without_status_change(quote_client, monkeypatch):
    client, quote_id, _, _ = quote_client
    row = object()

    monkeypatch.setattr("app.api.v1.routes.quotes.create_quote_learning", lambda db, qid, body, user: row)
    monkeypatch.setattr(
        "app.api.v1.routes.quotes.quote_learning_to_dict",
        lambda _: {
            "id": str(uuid4()),
            "quote_id": str(quote_id),
            "quote_version_id": None,
            "outcome_status": "revision_requested",
            "customer_feedback": "Customer asked for clearer load and warranty wording.",
            "customer_objection": "Needs validation before customer-visible use.",
            "competitor_signal": None,
            "won_reason": None,
            "lost_reason": None,
            "price_feedback": None,
            "delivery_feedback": None,
            "product_feedback": {},
            "product_dimensions": ["load", "noise", "warranty", "certification"],
            "next_action": "Update quote wording manually.",
            "owner": "sales",
            "follow_up_date": None,
            "affects_product_intelligence": True,
            "affects_market_response": True,
            "affects_opportunity": True,
            "internal_only": True,
            "created_at": None,
            "updated_at": None,
            "safety": {
                "external_message_sent": False,
                "quote_status_changed": False,
                "order_status_changed": False,
                "customer_notified": False,
                "supplier_notified": False,
                "raw_token_recorded": False,
                "customer_forbidden_fields_exposed": False,
            },
        },
    )

    r = client.post(
        f"/api/v1/quotes/{quote_id}/learning",
        json={
            "outcome_status": "revision_requested",
            "customer_feedback": "Customer asked for clearer load and warranty wording.",
            "product_dimensions": ["load", "noise", "warranty", "certification"],
            "affects_product_intelligence": True,
            "affects_market_response": True,
        },
    )

    assert r.status_code == 201
    body = r.json()["data"]
    assert body["outcome_status"] == "revision_requested"
    assert body["safety"]["external_message_sent"] is False
    assert body["safety"]["quote_status_changed"] is False
    assert body["safety"]["order_status_changed"] is False


def test_quote_learning_promotes_to_market_response_review(quote_client, monkeypatch):
    client, quote_id, _, _ = quote_client
    learning_id = uuid4()

    monkeypatch.setattr(
        "app.api.v1.routes.quotes.promote_quote_learning_to_market_response",
        lambda db, qid, lid, user: {
            "created": True,
            "review": {
                "id": str(uuid4()),
                "partner_focus": "HOSUN",
                "focus_category": "adjustable_desk_frames",
                "product_focus": ["lifting systems"],
                "review_dimension": "load",
                "visibility_class": "needs validation",
                "priority": "P1",
                "status": "needs review",
                "source_type": "feedback",
                "source_summary": "Quote learning promoted.",
                "next_action": "Review product wording.",
                "owner": "sales",
            },
            "safety": {
                "external_message_sent": False,
                "quote_status_changed": False,
                "order_status_changed": False,
                "customer_notified": False,
                "supplier_notified": False,
                "raw_token_recorded": False,
                "customer_forbidden_fields_exposed": False,
            },
        },
    )

    r = client.post(f"/api/v1/quotes/{quote_id}/learning/{learning_id}/market-response-review")

    assert r.status_code == 201
    data = r.json()["data"]
    assert data["created"] is True
    assert data["review"]["review_dimension"] == "load"
    assert data["safety"]["external_message_sent"] is False
    assert data["safety"]["quote_status_changed"] is False
    assert data["safety"]["order_status_changed"] is False


def test_archive_ready_to_send_quote(quote_client):
    client, quote_id, _, _ = quote_client
    r = client.delete(f"/api/v1/quotes/{quote_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"] == {"archived": True, "id": str(quote_id)}


def test_sent_quote_cannot_be_archived(quote_client, monkeypatch):
    client, quote_id, _, _ = quote_client
    quote = Quote(
        id=quote_id,
        quote_number="Q-2026-0001",
        quote_date=date.today(),
        valid_until=date.today() + timedelta(days=21),
        status="sent",
        currency="USD",
        subtotal=Decimal("1000.00"),
        adjustment_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("1000.00"),
    )
    monkeypatch.setattr("app.api.v1.routes.quotes.get_quote", lambda db, qid: quote)

    r = client.delete(f"/api/v1/quotes/{quote_id}")

    assert r.status_code == 400
    assert "only unsent, revised, or expired quotes can be archived" in r.text
