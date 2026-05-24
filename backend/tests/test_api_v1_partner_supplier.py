"""API tests for D7.4 partner splits and supplier confirmations."""

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
def partner_client(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="ps@test.example", is_active=True)
    order_id = uuid4()
    partner_id = uuid4()
    split_id = uuid4()

    order = CustomerOrder(
        id=order_id,
        order_number="O-2026-0099",
        source_quote_id=uuid4(),
        status="confirmed",
        order_date=date.today(),
        currency="USD",
        subtotal=Decimal("500"),
        adjustment_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("500"),
    )
    order.line_items = [
        OrderLineItem(
            id=uuid4(),
            order_id=order_id,
            source_quote_line_item_id=uuid4(),
            partner_id=partner_id,
            product_name="Split Product",
            quantity=5,
            unit_price=Decimal("100"),
            total_price=Decimal("500"),
            status="confirmed",
        )
    ]

    db = MagicMock()
    confirmation = MagicMock(
        id=uuid4(),
        order_id=order_id,
        partner_split_id=split_id,
        partner_id=partner_id,
        confirmation_status="confirmed",
        confirmed_at=None,
        confirmed_by_name=None,
        confirmed_by_email=None,
        confirmation_channel=None,
        inventory_confirmed=False,
        certification_confirmed=False,
        lead_time_confirmed=False,
        production_capacity_confirmed=True,
        expected_production_start=None,
        expected_ready_date=None,
        supplier_reference=None,
        note=None,
        status="active",
        voided_at=None,
        voided_reason=None,
        created_at=None,
    )

    monkeypatch.setattr("app.api.v1.routes.orders.get_order", lambda db_, oid: order)
    monkeypatch.setattr(
        "app.api.v1.routes.orders.order_detail_payload",
        lambda db_, o: {"id": str(o.id), "status": o.status, "safety": {"production_started": False}},
    )
    monkeypatch.setattr(
        "app.api.v1.routes.orders.ensure_partner_splits",
        lambda db_, uid, oid: {
            "order_id": str(order_id),
            "splits": [{"id": str(split_id), "partner_id": str(partner_id), "subtotal": "500"}],
            "created": 1,
            "updated": 0,
            "warnings": [],
            "safety": {"supplier_notified": False, "production_started": False, "shipment_created": False},
        },
    )
    monkeypatch.setattr("app.api.v1.routes.orders.get_partner_splits", lambda db_, oid: [])
    monkeypatch.setattr(
        "app.api.v1.routes.orders.split_to_dict",
        lambda db_, s: {"id": str(split_id), "subtotal": "500"},
    )
    monkeypatch.setattr(
        "app.api.v1.routes.orders.get_partner_split_detail",
        lambda db_, oid, sid: {"id": str(split_id), "line_items": [], "safety": {"production_started": False}},
    )
    monkeypatch.setattr(
        "app.api.v1.routes.orders.add_supplier_confirmation",
        lambda *a, **k: {
            "confirmation": confirmation,
            "warnings": [],
            "safety": {
                "supplier_confirmation_recorded": True,
                "supplier_notified": False,
                "production_started": False,
                "shipment_created": False,
            },
        },
    )
    monkeypatch.setattr(
        "app.api.v1.routes.orders.supplier_confirmation_to_dict",
        lambda r: {"confirmation_status": "confirmed", "status": "active"},
    )
    monkeypatch.setattr("app.api.v1.routes.orders.list_supplier_confirmations", lambda db_, oid, **k: [])

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)

    with TestClient(app) as client:
        yield client, order_id, split_id


def test_ensure_partner_splits_route(partner_client):
    client, order_id, _ = partner_client
    r = client.post(f"/api/v1/orders/{order_id}/partner-splits/ensure")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert "production started" not in r.text.lower()


def test_add_supplier_confirmation_route(partner_client):
    client, order_id, split_id = partner_client
    r = client.post(
        f"/api/v1/orders/{order_id}/partner-splits/{split_id}/supplier-confirmations",
        json={"confirmation_status": "confirmed", "production_capacity_confirmed": True},
    )
    assert r.status_code == 201
    assert r.json()["data"]["safety"]["production_started"] is False


def test_list_supplier_confirmations_route(partner_client):
    client, order_id, _ = partner_client
    r = client.get(f"/api/v1/orders/{order_id}/supplier-confirmations")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 0
