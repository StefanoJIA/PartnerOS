"""Tests for D8.5 market response intelligence aggregation."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import FeedbackTicket, MarketIntelligenceItem, Product, User
from app.models.customer_orders import CustomerOrder, OrderLineItem
from app.models.customer_quotes import Quote, QuoteLineItem
from app.services.market_response_intelligence import build_market_response_intelligence


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class _Db:
    def __init__(self, mapping):
        self.mapping = mapping

    def query(self, model):
        return _Query(self.mapping.get(model, []))


def _fixture_db():
    quote_id = uuid4()
    order_id = uuid4()
    product_id = uuid4()
    return _Db(
        {
            FeedbackTicket: [
                SimpleNamespace(
                    id=uuid4(),
                    ticket_number="FB-2026-0001",
                    feedback_type="tracking",
                    subject="Delayed adjustable frame shipment",
                    message="Customer reports late shipment and missing tracking for adjustable desk frame.",
                    response_summary=None,
                    status="new",
                    priority="high",
                    order_id=order_id,
                    created_at=datetime(2026, 5, 29, tzinfo=timezone.utc),
                )
            ],
            Quote: [
                SimpleNamespace(id=quote_id, status="converted_to_order"),
                SimpleNamespace(id=uuid4(), status="expired"),
            ],
            QuoteLineItem: [
                SimpleNamespace(
                    quote_id=quote_id,
                    product_category="Adjustable Frames",
                    product_name="Dual motor adjustable desk frame",
                    description_customer="Height adjustable frame",
                    quantity=12,
                    total_price=Decimal("2400.00"),
                )
            ],
            CustomerOrder: [
                SimpleNamespace(id=order_id, source_quote_id=quote_id, status="confirmed"),
            ],
            OrderLineItem: [
                SimpleNamespace(
                    order_id=order_id,
                    product_category="Adjustable Frames",
                    product_name="Dual motor adjustable desk frame",
                    description_customer="Height adjustable frame",
                    quantity=12,
                    total_price=Decimal("2400.00"),
                )
            ],
            MarketIntelligenceItem: [
                SimpleNamespace(
                    id=uuid4(),
                    title="Demand for quiet height adjustable frames",
                    related_product_category="Adjustable Frames",
                    market_segment="US office retrofit",
                    content="Buyers ask for lower noise and BIFMA support.",
                    tags="adjustable,quiet",
                    importance="high",
                )
            ],
            Product: [
                SimpleNamespace(
                    id=product_id,
                    product_name="Dual motor adjustable desk frame",
                    product_category="Adjustable Frames",
                    dimensions=None,
                    load_capacity=None,
                    lifting_speed="35mm/s",
                    noise_level=None,
                    available_certifications=None,
                    moq=20,
                    sample_available=True,
                    target_us_price_range=None,
                )
            ],
        }
    )


def test_market_response_intelligence_aggregates_feedback_demand_and_gaps():
    data = build_market_response_intelligence(_fixture_db())

    assert data["summary"]["feedback_ticket_count"] == 1
    assert data["feedback"]["tag_counts"]["risk_or_issue"] == 1
    assert data["feedback"]["tag_counts"]["logistics"] == 1
    assert data["win_loss"]["lost_quote_count"] == 1
    assert data["demand"]["items"][0]["category"] == "Adjustable Frames"
    assert data["demand"]["items"][0]["adjustable_frame_focus"] is True
    assert data["product_gaps"]["total"] == 1
    assert data["recommendations"][0]["human_review_required"] is True
    assert data["safety"]["read_only"] is True
    assert data["safety"]["ai_executed"] is False


def test_market_response_intelligence_route(monkeypatch):
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(),
        email="d8_5_market@test.example",
        is_active=True,
    )
    app.dependency_overrides[get_db] = lambda: (yield _fixture_db())

    with TestClient(app) as client:
        response = client.get("/api/v1/market/response-intelligence")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["summary"]["market_signal_count"] == 1
    assert payload["safety"]["customer_notified"] is False
