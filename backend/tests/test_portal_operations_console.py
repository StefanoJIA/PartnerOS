"""Tests for D8 Portal operations console and customer snapshots."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User


def test_portal_operations_console_route_is_safe(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="ops@test.example", is_active=True)
    settings = Settings(
        PORTAL_CUSTOMER_API_ENABLED=True,
        PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
        PORTAL_CUSTOMER_API_TOKEN="secret-token",
        PORTAL_CUSTOMER_ALLOWED_ORIGINS="https://service.intelli-opus.com",
        PUBLIC_BASE_URL="https://partneros-staging.example.com",
    )

    from app.core.config import get_settings

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())
    app.dependency_overrides[get_settings] = lambda: settings
    monkeypatch.setattr(
        "app.api.v1.routes.portal_operations.build_portal_operations_console",
        lambda db, settings, recent_limit=8: {
            "status": {
                "ready": True,
                "enabled": True,
                "token_required": True,
                "token_configured": True,
                "public_base_url_configured": True,
                "allowed_origins": ["https://service.intelli-opus.com"],
                "missing_config": [],
            },
            "endpoint_readiness": {
                "products": True,
                "orders": True,
                "production": True,
                "shipment": True,
                "resources": True,
                "feedback": True,
            },
            "recent_customer_visible_orders": {"items": [], "total": 0},
            "shipment_status_counts": {},
            "feedback_status_counts": {},
            "forbidden_field_audit": {"checked": True, "hits": [], "credential_value_exposed": False},
            "safety": {"read_only": True, "customer_notified": False, "automatic_reply_sent": False},
        },
    )

    with TestClient(app) as client:
        r = client.get("/api/v1/portal/operations/console")

    assert r.status_code == 200
    raw = r.text.lower()
    assert "secret-token" not in raw
    assert "internal_cost" not in raw
    assert r.json()["data"]["endpoint_readiness"]["shipment"] is True
    assert r.json()["data"]["safety"]["customer_notified"] is False


def test_customer_snapshot_stage_and_safety(monkeypatch):
    from app.services.portal.customer_order_snapshot import build_customer_order_snapshot

    order_id = uuid4()
    db = MagicMock()
    order = MagicMock()
    order.status = "confirmed"
    milestone = MagicMock()
    milestone.status = "completed"
    milestone.milestone_type = "ready_to_ship"
    shipment = MagicMock()
    shipment.status = "planned"

    def query(model):
        q = MagicMock()
        if getattr(model, "__name__", "") == "CustomerOrder":
            q.filter.return_value.first.return_value = order
        elif getattr(model, "__name__", "") == "OrderProductionMilestone":
            q.filter.return_value.order_by.return_value.all.return_value = [milestone]
        elif getattr(model, "__name__", "") == "ShipmentPlan":
            q.filter.return_value.order_by.return_value.all.return_value = [shipment]
        else:
            q.filter.return_value.count.return_value = 0
            q.count.return_value = 0
        return q

    db.query.side_effect = query
    monkeypatch.setattr(
        "app.services.portal.customer_order_snapshot.build_customer_order_detail",
        lambda db, oid: {"id": str(oid), "order_number": "O-1", "status": "confirmed"},
    )
    monkeypatch.setattr(
        "app.services.portal.customer_order_snapshot.build_customer_production_view",
        lambda db, oid: {"order_id": str(oid), "items": [{"status": "completed"}], "total": 1},
    )
    monkeypatch.setattr(
        "app.services.portal.customer_order_snapshot.build_customer_shipment_view",
        lambda db, oid: {"order_id": str(oid), "items": [{"status": "planned"}], "total": 1},
    )
    monkeypatch.setattr(
        "app.services.portal.customer_order_snapshot.list_customer_order_resources",
        lambda db, oid: {"order_id": str(oid), "items": [], "total": 0},
    )

    data = build_customer_order_snapshot(db, order_id)

    assert data["customer_status"]["stage"] == "ready_to_ship"
    assert data["customer_status"]["current_step_index"] == 2
    assert [step["key"] for step in data["customer_status"]["progress_steps"]] == [
        "confirmed",
        "in_production",
        "ready_to_ship",
        "shipped",
        "delivered",
    ]
    assert data["customer_status"]["progress_steps"][2]["state"] == "current"
    assert data["customer_status"]["progress_steps"][2]["planned_dates_are_guarantees"] is False
    assert data["customer_status"]["planned_dates_are_guarantees"] is False
    assert data["safety"]["forbidden_field_filter_enabled"] is True
    assert data["feedback"]["customer_notified"] is False


def test_operations_console_preserves_safe_token_metadata_without_values():
    from app.services.portal.operations_console import (
        _audit_forbidden_fields,
        _build_portal_contract,
        _build_runtime_health,
        _safe_payload,
    )

    settings = Settings(
        PORTAL_CUSTOMER_API_ENABLED=True,
        PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
        PORTAL_CUSTOMER_API_TOKEN="super-secret-value",
        PORTAL_CUSTOMER_ALLOWED_ORIGINS="https://service.intelli-opus.com",
        PUBLIC_BASE_URL="https://partneros-staging.example.com",
    )
    endpoints = {name: True for name in ("products", "orders", "production", "shipment", "resources", "feedback")}
    data = _safe_payload(
        {
            "status": {"token_required": True, "token_configured": True},
            "portal_contract": _build_portal_contract(settings, endpoints, []),
            "token": "should-not-leak",
            "nested": {"storage_key": "backend/storage/private.pdf", "ok": "visible"},
            "safety": {"token_value_exposed": False},
        }
    )

    assert data["status"]["token_required"] is True
    assert data["status"]["token_configured"] is True
    assert data["safety"]["token_value_exposed"] is False
    assert data["portal_contract"]["server_to_server_auth"]["header_name"] == "X-Portal-Customer-Token"
    assert data["portal_contract"]["server_to_server_auth"]["token_configured"] is True
    assert "super-secret-value" not in str(data)
    assert "token" not in data
    assert "storage_key" not in data["nested"]

    audit = _audit_forbidden_fields(
        {
            "portal_contract": data["portal_contract"],
            "customer_snapshot": {"order": {"order_number": "O-1"}, "safety": {"token_value_exposed": False}},
            "bad": {"storage_key": "backend/storage/private.pdf", "margin": "hidden"},
        }
    )
    assert audit["checked"] is True
    assert audit["credential_value_exposed"] is False
    assert audit["server_file_path_exposed"] is True
    assert audit["cost_fields_exposed"] is True
    assert any("storage_key" in hit for hit in audit["hits"])
    assert any("margin" in hit for hit in audit["hits"])

    runtime = _build_runtime_health(settings, [])
    assert "DATABASE_URL" not in str(runtime)
    assert "super-secret-value" not in str(runtime)
    assert runtime["safety"]["read_only"] is True
    assert runtime["safety"]["secret_values_exposed"] is False


def test_market_signal_preview_groups_focus_categories():
    from app.services.portal.operations_console import _build_market_signal_preview

    order_id = uuid4()
    line = MagicMock()
    line.order_id = order_id
    line.product_category = "desk_frame"
    line.product_name = "Dual motor adjustable desk frame"
    line.description_customer = "Height adjustable frame"
    line.quantity = 12

    milestone = MagicMock()
    milestone.order_id = order_id
    milestone.status = "delayed"

    shipment = MagicMock()
    shipment.order_id = order_id
    shipment.status = "planned"
    shipment.notes = "Delay at port"

    ticket = MagicMock()
    ticket.order_id = order_id
    ticket.feedback_type = "tracking"
    ticket.subject = "Desk frame shipment update"
    ticket.message = "Customer asks about the adjustable frame ETA"
    ticket.response_summary = None

    data = _build_market_signal_preview([line], [milestone], [shipment], [ticket])
    first = data["items"][0]

    assert first["key"] == "adjustable_desk_frames"
    assert first["order_line_count"] == 1
    assert first["ordered_quantity"] == 12
    assert first["feedback_count"] == 1
    assert first["delayed_or_blocked_production_count"] == 1
    assert first["shipment_issue_count"] == 1
    assert data["safety"]["advisory_only"] is True
    assert data["safety"]["auto_ticket_created"] is False


def test_feedback_operations_summary_is_internal_only():
    from datetime import datetime, timezone

    from app.services.portal.operations_console import _build_feedback_operations

    new_ticket = MagicMock()
    new_ticket.status = "new"
    new_ticket.priority = "urgent"
    new_ticket.response_summary = None
    new_ticket.created_at = datetime(2026, 5, 29, tzinfo=timezone.utc)

    resolved_ticket = MagicMock()
    resolved_ticket.status = "resolved"
    resolved_ticket.priority = "normal"
    resolved_ticket.response_summary = None
    resolved_ticket.created_at = datetime(2026, 5, 30, tzinfo=timezone.utc)

    data = _build_feedback_operations([new_ticket, resolved_ticket])

    assert data["total_count"] == 2
    assert data["open_count"] == 1
    assert data["high_priority_count"] == 1
    assert data["needs_internal_review_count"] == 2
    assert data["response_summary_missing_count"] == 1
    assert data["ready_to_close_count"] == 1
    assert data["safety"]["internal_queue_only"] is True
    assert data["safety"]["customer_notified"] is False
    assert data["safety"]["automatic_reply_sent"] is False
    assert data["safety"]["sla_promised"] is False
