"""API tests for D7.3 order confirmations."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User
from app.models.customer_orders import CustomerOrder, OrderConfirmation


@pytest.fixture
def confirmation_client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="c@test.example", is_active=True)
    order_id = uuid4()
    conf_id = uuid4()

    order = CustomerOrder(
        id=order_id,
        order_number="O-2026-0002",
        source_quote_id=uuid4(),
        status="pending_customer_confirmation",
        order_date=date.today(),
        currency="USD",
        subtotal=Decimal("500"),
        adjustment_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("500"),
    )
    confirmation = OrderConfirmation(
        id=conf_id,
        order_id=order_id,
        confirmation_type="email",
        confirmation_strength="medium",
        confirmed_at=datetime.now(timezone.utc),
        status="active",
    )

    result = {
        "order": order,
        "confirmation": confirmation,
        "status_changed": True,
        "warnings": ["confirmed order still requires supplier confirmation before production"],
        "safety": {
            "order_confirmed": True,
            "customer_confirmation_recorded": True,
            "production_started": False,
            "shipment_created": False,
            "supplier_notified": False,
            "payment_received": False,
        },
    }

    monkeypatch.setattr(
        "app.api.v1.routes.orders.add_customer_confirmation",
        lambda db, u, oid, **kw: result,
    )
    monkeypatch.setattr(
        "app.api.v1.routes.orders.list_customer_confirmations",
        lambda db, oid: [confirmation],
    )
    monkeypatch.setattr(
        "app.api.v1.routes.orders.confirmation_to_dict",
        lambda r: {"id": str(r.id), "confirmation_type": r.confirmation_type, "status": r.status},
    )
    monkeypatch.setattr(
        "app.api.v1.routes.orders.order_detail_payload",
        lambda db, o: {
            "id": str(o.id),
            "status": o.status,
            "confirmation_summary": {"active_count": 1},
            "safety": result["safety"],
        },
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())

    with TestClient(app) as client:
        yield client, order_id, conf_id


def test_confirm_customer_envelope(confirmation_client):
    client, order_id, _ = confirmation_client
    r = client.post(
        f"/api/v1/orders/{order_id}/confirm-customer",
        json={
            "confirmation_type": "email",
            "confirmed_by_name": "Buyer",
            "evidence_reference": "Email reply",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["confirmation"]["confirmation_type"] == "email"
    assert body["data"]["safety"]["production_started"] is False
    assert "supplier notified" not in r.text.lower()


def test_list_confirmations(confirmation_client):
    client, order_id, _ = confirmation_client
    r = client.get(f"/api/v1/orders/{order_id}/confirmations")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1
