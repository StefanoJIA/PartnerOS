"""API tests for D7.2 Customer Orders."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User
from app.models.customer_orders import CustomerOrder, OrderLineItem


@pytest.fixture
def order_client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="o@test.example", is_active=True)
    order_id = uuid4()
    quote_id = uuid4()
    partner_id = uuid4()
    line_id = uuid4()

    order = CustomerOrder(
        id=order_id,
        order_number="O-2026-0001",
        source_quote_id=quote_id,
        status="pending_customer_confirmation",
        order_date=date.today(),
        currency="USD",
        subtotal=Decimal("1000"),
        adjustment_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("1000"),
    )
    order.line_items = [
        OrderLineItem(
            id=line_id,
            order_id=order_id,
            source_quote_line_item_id=uuid4(),
            partner_id=partner_id,
            product_name="Test Product",
            quantity=10,
            unit_price=Decimal("100"),
            total_price=Decimal("1000"),
            status="pending",
        )
    ]

    db = MagicMock()

    def _get_order(db_, oid):
        if oid == order_id:
            return order
        from app.core.errors import ApiError, NOT_FOUND

        raise ApiError(NOT_FOUND, "not found", status_code=404)

    monkeypatch.setattr("app.api.v1.routes.orders.get_order", _get_order)
    monkeypatch.setattr(
        "app.api.v1.routes.orders.order_detail_payload",
        lambda db_, o: {"id": str(o.id), "order_number": o.order_number, "status": o.status, "line_items": [], "safety": {"production_started": False}},
    )
    monkeypatch.setattr(
        "app.api.v1.routes.orders.build_order_timeline",
        lambda db_, oid: {"items": [{"type": "order_created", "title": "Order created from quote"}], "total": 1},
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)

    with TestClient(app) as client:
        yield client, order_id, quote_id


def test_get_order_envelope(order_client):
    client, order_id, _ = order_client
    r = client.get(f"/api/v1/orders/{order_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["order_number"] == "O-2026-0001"
    assert "production started" not in r.text.lower()


def test_order_timeline(order_client):
    client, order_id, _ = order_client
    r = client.get(f"/api/v1/orders/{order_id}/timeline")
    assert r.status_code == 200
    assert r.json()["data"]["items"][0]["type"] == "order_created"


def test_list_orders_empty(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="o@test.example", is_active=True)
    db = MagicMock()
    db.query.return_value.count.return_value = 0
    db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)

    with TestClient(app) as client:
        r = client.get("/api/v1/orders")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 0
