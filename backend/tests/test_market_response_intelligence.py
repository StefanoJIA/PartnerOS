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
    company_id = uuid4()
    other_company_id = uuid4()
    quote_id = uuid4()
    other_quote_id = uuid4()
    order_id = uuid4()
    other_order_id = uuid4()
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
                    company_id=company_id,
                    created_at=datetime(2026, 5, 29, tzinfo=timezone.utc),
                ),
                SimpleNamespace(
                    id=uuid4(),
                    ticket_number="FB-2026-0002",
                    feedback_type="general",
                    subject="Education furniture question",
                    message="Customer asks about classroom project furniture.",
                    response_summary=None,
                    status="new",
                    priority="normal",
                    order_id=other_order_id,
                    company_id=other_company_id,
                    created_at=datetime(2026, 5, 28, tzinfo=timezone.utc),
                )
            ],
            Quote: [
                SimpleNamespace(id=quote_id, company_id=company_id, status="converted_to_order"),
                SimpleNamespace(id=other_quote_id, company_id=other_company_id, status="expired"),
            ],
            QuoteLineItem: [
                SimpleNamespace(
                    quote_id=quote_id,
                    product_category="Adjustable Frames",
                    product_name="Dual motor adjustable desk frame",
                    description_customer="Height adjustable frame",
                    quantity=12,
                    total_price=Decimal("2400.00"),
                ),
                SimpleNamespace(
                    quote_id=other_quote_id,
                    product_category="Education Furniture",
                    product_name="Classroom project table",
                    description_customer="Education project furniture",
                    quantity=20,
                    total_price=Decimal("3000.00"),
                )
            ],
            CustomerOrder: [
                SimpleNamespace(id=order_id, source_quote_id=quote_id, company_id=company_id, status="confirmed"),
                SimpleNamespace(id=other_order_id, source_quote_id=other_quote_id, company_id=other_company_id, status="confirmed"),
            ],
            OrderLineItem: [
                SimpleNamespace(
                    order_id=order_id,
                    product_category="Adjustable Frames",
                    product_name="Dual motor adjustable desk frame",
                    description_customer="Height adjustable frame",
                    quantity=12,
                    total_price=Decimal("2400.00"),
                ),
                SimpleNamespace(
                    order_id=other_order_id,
                    product_category="Education Furniture",
                    product_name="Classroom project table",
                    description_customer="Education project furniture",
                    quantity=20,
                    total_price=Decimal("3000.00"),
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
                    related_company_id=company_id,
                ),
                SimpleNamespace(
                    id=uuid4(),
                    title="Education furniture project demand",
                    related_product_category="Education Furniture",
                    market_segment="US education",
                    content="Schools ask for project furniture packages.",
                    tags="education,project",
                    importance="normal",
                    related_company_id=other_company_id,
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
    ), company_id


def test_market_response_intelligence_aggregates_feedback_demand_and_gaps():
    db, _ = _fixture_db()
    data = build_market_response_intelligence(db)

    assert data["summary"]["feedback_ticket_count"] == 2
    assert data["feedback"]["tag_counts"]["risk_or_issue"] == 1
    assert data["feedback"]["tag_counts"]["logistics"] == 1
    assert data["win_loss"]["lost_quote_count"] == 1
    assert data["demand"]["items"][0]["category"] == "Adjustable Frames"
    assert data["demand"]["items"][0]["adjustable_frame_focus"] is True
    assert data["demand"]["items"][0]["focus_category"] == "adjustable_desk_frames"
    assert data["summary"]["focus_category_counts"]["adjustable_desk_frames"] >= 1
    assert data["summary"]["focus_category_counts"]["education_furniture"] >= 1
    assert data["product_gaps"]["total"] == 1
    assert data["recommendations"][0]["human_review_required"] is True
    assert data["safety"]["read_only"] is True
    assert data["safety"]["ai_executed"] is False


def test_market_response_intelligence_filters_by_related_company():
    db, company_id = _fixture_db()
    data = build_market_response_intelligence(db, related_company_id=company_id)

    assert data["summary"]["filtered_by_company"] is True
    assert data["summary"]["feedback_ticket_count"] == 1
    assert data["summary"]["market_signal_count"] == 1
    assert data["summary"]["quote_count"] == 1
    assert data["summary"]["order_count"] == 1
    assert data["demand"]["items"][0]["category"] == "Adjustable Frames"
    assert "Education Furniture" not in {row["category"] for row in data["demand"]["items"]}


def test_market_response_intelligence_filters_by_focus_category():
    db, _ = _fixture_db()
    data = build_market_response_intelligence(db, focus_category="education_furniture")

    assert data["summary"]["filtered_by_focus"] is True
    assert data["summary"]["focus_category"] == "education_furniture"
    assert data["summary"]["feedback_ticket_count"] == 1
    assert data["summary"]["market_signal_count"] == 1
    assert data["summary"]["quote_count"] == 1
    assert data["summary"]["order_count"] == 1
    assert {row["focus_category"] for row in data["demand"]["items"]} == {"education_furniture"}
    assert "Education Furniture" in {row["category"] for row in data["demand"]["items"]}
    assert data["feedback"]["items"][0]["subject"] == "Education furniture question"
    assert data["safety"]["customer_notified"] is False


def test_market_response_intelligence_route(monkeypatch):
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(),
        email="d8_5_market@test.example",
        is_active=True,
    )
    db, company_id = _fixture_db()
    app.dependency_overrides[get_db] = lambda: (yield db)

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/market/response-intelligence?related_company_id={company_id}&focus_category=adjustable_desk_frames"
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["summary"]["market_signal_count"] == 1
    assert payload["summary"]["filtered_by_company"] is True
    assert payload["summary"]["filtered_by_focus"] is True
    assert payload["safety"]["customer_notified"] is False
