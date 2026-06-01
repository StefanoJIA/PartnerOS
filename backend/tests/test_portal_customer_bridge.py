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


def test_portal_customer_manifest_is_token_gated_and_safe():
    settings = Settings(
        PORTAL_CUSTOMER_API_ENABLED=True,
        PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
        PORTAL_CUSTOMER_API_TOKEN="test-token",
        PUBLIC_BASE_URL="https://partneros-staging.example.com",
    )
    client, _ = _client(settings)
    with client as c:
        missing = c.get("/api/v1/portal/customer/manifest")
        ok = c.get("/api/v1/portal/customer/manifest", headers={"X-Portal-Customer-Token": "test-token"})

    assert missing.status_code == 401
    assert ok.status_code == 200
    data = ok.json()["data"]
    raw = ok.text.lower()
    assert data["source_of_truth"] == "PartnerOS"
    assert data["consumer"] == "service.intelli-opus.com"
    assert data["auth"]["header_name"] == "X-Portal-Customer-Token"
    assert data["auth"]["token_configured"] is True
    assert data["auth"]["token_value_exposed"] is False
    assert "customer_status_stages" in data["field_contract"]
    assert "customer_next_action" in data["field_contract"]
    assert "tracking_summary" in data["field_contract"]
    assert "links" in data["field_contract"]["snapshot"]
    assert "snapshot_links" in data["field_contract"]
    assert "next_action_label" in data["field_contract"]["customer_status"]
    assert "ready_to_ship" in data["field_contract"]["customer_status_stages"]
    assert data["field_contract"]["date_policy"]["planned_dates_are_guarantees"] is False
    assert "feedback_snapshot" in data["field_contract"]
    assert "allowed_feedback_types" in data["field_contract"]["feedback_snapshot"]
    assert "resolution_time_promised" in data["field_contract"]["feedback_snapshot"]
    assert data["field_contract"]["feedback_form_contract"]["submit_method"] == "POST"
    assert data["field_contract"]["feedback_form_contract"]["allowed_feedback_types"] == [
        "tracking",
        "resource",
        "quality",
        "general",
    ]
    assert data["field_contract"]["feedback_form_contract"]["allowed_priorities"] == ["normal", "high", "urgent"]
    assert data["field_contract"]["feedback_form_contract"]["resolution_time_promised"] is False
    assert data["field_contract"]["feedback_form_contract"]["customer_notified"] is False
    assert "feedback_create_response" in data["field_contract"]
    assert "next_links" in data["field_contract"]["feedback_create_response"]
    assert "feedback_next_links" in data["field_contract"]
    assert data["field_policy"]["planned_dates_are_guarantees"] is False
    assert data["safety"]["automatic_customer_notification"] is False
    assert data["safety"]["order_status_mutated"] is False
    assert "test-token" not in raw
    assert "internal_cost" not in raw
    assert "storage_key" not in raw


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
            "customer_status": {
                "stage": "ready_to_ship",
                "next_action_label": "Shipment planning",
                "next_action_detail": "Operator will add shipment details when available.",
                "planned_dates_are_guarantees": False,
            },
            "tracking_summary": {
                "stage": "ready_to_ship",
                "has_active_shipment": True,
                "planned_dates_are_guarantees": False,
            },
            "links": {
                "order_detail": f"/api/v1/portal/customer/orders/{oid}",
                "order_snapshot": f"/api/v1/portal/customer/orders/{oid}/snapshot",
                "production": f"/api/v1/portal/customer/orders/{oid}/production",
                "shipment": f"/api/v1/portal/customer/orders/{oid}/shipment",
                "resources": f"/api/v1/portal/customer/orders/{oid}/resources",
                "feedback_submit": "/api/v1/portal/customer/feedback",
            },
            "feedback": {
                "submit_endpoint": "/api/v1/portal/customer/feedback",
                "submit_method": "POST",
                "allowed_feedback_types": ["tracking", "resource", "quality", "general"],
                "allowed_priorities": ["normal", "high", "urgent"],
                "requires_order_id": False,
                "resolution_time_promised": False,
                "customer_notified": False,
                "automatic_reply_sent": False,
            },
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
    assert snapshot.json()["data"]["customer_status"]["next_action_label"] == "Shipment planning"
    assert snapshot.json()["data"]["tracking_summary"]["has_active_shipment"] is True
    assert snapshot.json()["data"]["links"]["shipment"] == f"/api/v1/portal/customer/orders/{order_id}/shipment"
    assert snapshot.json()["data"]["links"]["feedback_submit"] == "/api/v1/portal/customer/feedback"
    assert snapshot.json()["data"]["feedback"]["submit_method"] == "POST"
    assert "tracking" in snapshot.json()["data"]["feedback"]["allowed_feedback_types"]
    assert snapshot.json()["data"]["feedback"]["resolution_time_promised"] is False


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
            "next_links": {
                "orders": "/api/v1/portal/customer/orders",
                "order_snapshot": None,
                "production": None,
                "shipment": None,
                "resources": None,
                "feedback_submit": "/api/v1/portal/customer/feedback",
            },
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
    assert data["next_links"]["orders"] == "/api/v1/portal/customer/orders"
    assert data["next_links"]["feedback_submit"] == "/api/v1/portal/customer/feedback"
    assert data["customer_notified"] is False
    assert data["automatic_reply_sent"] is False


def test_portal_feedback_response_includes_order_refresh_links(monkeypatch):
    from app.services.portal.customer_portal_bridge import create_feedback_ticket

    order_id = uuid4()
    company_id = uuid4()
    db = MagicMock()
    order = MagicMock()
    order.company_id = company_id

    db.query.return_value.filter.return_value.first.return_value = order
    monkeypatch.setattr("app.services.portal.customer_portal_bridge._next_ticket_number", lambda db: "FB-2026-0002")

    def add(row):
        row.ticket_number = "FB-2026-0002"
        row.status = "new"

    db.add.side_effect = add

    data = create_feedback_ticket(
        db,
        order_id=order_id,
        feedback_type="tracking",
        subject="Need shipment update",
        message="Can you refresh the shipment status?",
    )

    assert data["ticket_number"] == "FB-2026-0002"
    assert data["next_links"]["order_snapshot"] == f"/api/v1/portal/customer/orders/{order_id}/snapshot"
    assert data["next_links"]["shipment"] == f"/api/v1/portal/customer/orders/{order_id}/shipment"
    assert data["next_links"]["resources"] == f"/api/v1/portal/customer/orders/{order_id}/resources"
    assert data["next_links"]["feedback_submit"] == "/api/v1/portal/customer/feedback"
    assert data["customer_notified"] is False
    assert data["automatic_reply_sent"] is False


def test_portal_feedback_rejects_values_outside_customer_contract():
    settings = Settings(
        PORTAL_CUSTOMER_API_ENABLED=True,
        PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
        PORTAL_CUSTOMER_API_TOKEN="test-token",
    )
    client, _ = _client(settings)
    with client as c:
        bad_type = c.post(
            "/api/v1/portal/customer/feedback",
            headers={"X-Portal-Customer-Token": "test-token"},
            json={
                "feedback_type": "internal_margin_question",
                "subject": "Need update",
                "message": "Where is my order?",
                "priority": "normal",
            },
        )
        bad_priority = c.post(
            "/api/v1/portal/customer/feedback",
            headers={"X-Portal-Customer-Token": "test-token"},
            json={
                "feedback_type": "tracking",
                "subject": "Need update",
                "message": "Where is my order?",
                "priority": "someday",
            },
        )

    assert bad_type.status_code == 400
    assert bad_priority.status_code == 400
    assert "Invalid feedback type" in bad_type.text
    assert "Invalid feedback priority" in bad_priority.text
    assert "internal_margin" not in bad_type.text


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
