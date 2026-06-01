"""Tests for D7.7 customer portal bridge API."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import get_db
from app.main import create_app
from app.services.portal.customer_field_filter import strip_forbidden_internal_fields


def _client(settings: Settings):
    app = create_app()
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: (yield db)
    from app.core.config import get_settings

    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app), db


def test_portal_customer_api_disabled_by_default():
    client, _ = _client(Settings(PORTAL_CUSTOMER_API_ENABLED=False))
    with client as c:
        r = c.get("/api/v1/portal/customer/products")
    assert r.status_code == 503
    assert r.json()["ok"] is False


def test_portal_customer_token_required_and_valid(monkeypatch):
    settings = Settings(
        PORTAL_CUSTOMER_API_ENABLED=True,
        PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
        PORTAL_CUSTOMER_API_TOKEN="test-token",
    )
    client, _ = _client(settings)
    monkeypatch.setattr(
        "app.api.v1.routes.portal_customer.build_customer_product_list",
        lambda *a, **k: {"items": [], "total": 0},
    )
    with client as c:
        missing = c.get("/api/v1/portal/customer/products")
        wrong = c.get("/api/v1/portal/customer/products", headers={"Authorization": "Bearer wrong"})
        ok = c.get("/api/v1/portal/customer/products", headers={"Authorization": "Bearer test-token"})
        x_token_wins = c.get(
            "/api/v1/portal/customer/products",
            headers={"Authorization": "Bearer app-user-token", "X-Portal-Customer-Token": "test-token"},
        )
    assert missing.status_code == 401
    assert wrong.status_code == 403
    assert ok.status_code == 200
    assert x_token_wins.status_code == 200
    assert ok.json()["data"]["total"] == 0


def test_portal_customer_routes_return_whitelisted_payloads(monkeypatch):
    settings = Settings(
        PORTAL_CUSTOMER_API_ENABLED=True,
        PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
        PORTAL_CUSTOMER_API_TOKEN="test-token",
    )
    client, _ = _client(settings)
    order_id = uuid4()
    monkeypatch.setattr(
        "app.api.v1.routes.portal_customer.build_customer_order_detail",
        lambda db, oid: {"id": str(oid), "order_number": "O-1", "grand_total": "100.00"},
    )
    monkeypatch.setattr(
        "app.api.v1.routes.portal_customer.build_customer_production_view",
        lambda db, oid: {"order_id": str(oid), "items": [{"milestone_label": "Packed", "status": "completed"}]},
    )
    monkeypatch.setattr(
        "app.api.v1.routes.portal_customer.build_customer_shipment_view",
        lambda db, oid: {"order_id": str(oid), "items": [{"status": "planned", "tracking_number": "TRACK"}]},
    )
    monkeypatch.setattr(
        "app.api.v1.routes.portal_customer.build_customer_resource_view",
        lambda db, oid: {"order_id": str(oid), "items": [{"filename": "spec.pdf"}]},
    )
    monkeypatch.setattr(
        "app.api.v1.routes.portal_customer.build_customer_order_snapshot",
        lambda db, oid: {
            "order": {"id": str(oid), "order_number": "O-1"},
            "customer_status": {"stage": "ready_to_ship", "planned_dates_are_guarantees": False},
            "safety": {"forbidden_field_filter_enabled": True, "token_exposed": False},
        },
    )
    headers = {"X-Portal-Customer-Token": "test-token"}
    with client as c:
        detail = c.get(f"/api/v1/portal/customer/orders/{order_id}", headers=headers)
        snapshot = c.get(f"/api/v1/portal/customer/orders/{order_id}/snapshot", headers=headers)
        production = c.get(f"/api/v1/portal/customer/orders/{order_id}/production", headers=headers)
        shipment = c.get(f"/api/v1/portal/customer/orders/{order_id}/shipment", headers=headers)
        resources = c.get(f"/api/v1/portal/customer/orders/{order_id}/resources", headers=headers)
    for response in (detail, snapshot, production, shipment, resources):
        assert response.status_code == 200
        raw = response.text.lower()
        assert "internal_cost" not in raw
        assert "margin" not in raw
        assert "supplier_reference" not in raw
        assert "storage_key" not in raw
    assert snapshot.json()["data"]["customer_status"]["planned_dates_are_guarantees"] is False


def test_portal_feedback_creates_ticket_without_auto_reply(monkeypatch):
    settings = Settings(
        PORTAL_CUSTOMER_API_ENABLED=True,
        PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
        PORTAL_CUSTOMER_API_TOKEN="test-token",
    )
    client, _ = _client(settings)
    monkeypatch.setattr(
        "app.api.v1.routes.portal_customer.create_feedback_ticket",
        lambda *a, **k: {
            "ticket_number": "FB-2026-0001",
            "status": "new",
            "feedback_received": True,
            "customer_notified": False,
            "automatic_reply_sent": False,
            "resolution_time_promised": False,
        },
    )
    with client as c:
        r = c.post(
            "/api/v1/portal/customer/feedback",
            headers={"Authorization": "Bearer test-token"},
            json={"subject": "Need update", "message": "Where is my order?"},
        )
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["ticket_number"] == "FB-2026-0001"
    assert data["customer_notified"] is False
    assert data["automatic_reply_sent"] is False


def test_strip_forbidden_internal_fields_recursive():
    payload = {
        "id": "1",
        "margin": "secret",
        "nested": {"supplier_reference": "hidden", "status": "planned"},
        "items": [{"storage_key": "backend/storage/x", "filename": "ok.pdf"}],
    }
    cleaned = strip_forbidden_internal_fields(payload)
    assert "margin" not in cleaned
    assert "supplier_reference" not in cleaned["nested"]
    assert "storage_key" not in cleaned["items"][0]
    assert cleaned["nested"]["status"] == "planned"
