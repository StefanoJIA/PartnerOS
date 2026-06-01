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
    assert data["customer_status"]["next_action_label"] == "Shipment planning"
    assert "guaranteed" not in data["customer_status"]["next_action_detail"].lower()
    assert data["tracking_summary"]["stage"] == "ready_to_ship"
    assert data["tracking_summary"]["production_item_count"] == 1
    assert data["tracking_summary"]["shipment_item_count"] == 1
    assert data["tracking_summary"]["has_active_shipment"] is True
    assert data["tracking_summary"]["planned_dates_are_guarantees"] is False
    assert data["portal_display"]["headline"] == "O-1: Ready to ship"
    assert data["portal_display"]["stage"] == "ready_to_ship"
    assert data["portal_display"]["current_step_label"] == "Ready to ship"
    assert data["portal_display"]["next_action_label"] == "Shipment planning"
    assert data["portal_display"]["progress_percent"] == 60
    assert data["portal_display"]["status_badges"][2] == {
        "key": "ready_to_ship",
        "label": "Ready to ship",
        "state": "current",
        "active": True,
        "date": None,
        "planned_dates_are_guarantees": False,
    }
    assert data["portal_display"]["status_badges"][3]["active"] is False
    assert data["portal_display"]["signal_cards"][0] == {
        "key": "production",
        "label": "Production",
        "active": True,
        "count": 1,
    }
    assert data["portal_display"]["signal_cards"][1]["key"] == "shipment"
    assert data["portal_display"]["signal_cards"][1]["active"] is True
    assert data["portal_display"]["feedback_cta"]["path"] == "/api/v1/portal/customer/feedback"
    assert data["portal_display"]["feedback_cta"]["automatic_reply_sent"] is False
    assert data["portal_display"]["feedback_cta"]["resolution_time_promised"] is False
    assert data["portal_display"]["planned_dates_are_guarantees"] is False
    assert data["links"]["order_snapshot"] == f"/api/v1/portal/customer/orders/{order_id}/snapshot"
    assert data["links"]["shipment"] == f"/api/v1/portal/customer/orders/{order_id}/shipment"
    assert data["links"]["feedback_submit"] == "/api/v1/portal/customer/feedback"
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
    assert data["feedback"]["submit_method"] == "POST"
    assert data["feedback"]["requires_order_id"] is False
    assert data["feedback"]["allowed_feedback_types"] == ["tracking", "resource", "quality", "general"]
    assert data["feedback"]["allowed_priorities"] == ["normal", "high", "urgent"]
    assert data["feedback"]["resolution_time_promised"] is False


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
    assert "customer_status_stages" in data["portal_contract"]["field_contract"]
    assert "customer_next_action" in data["portal_contract"]["field_contract"]
    assert "tracking_summary" in data["portal_contract"]["field_contract"]
    assert "links" in data["portal_contract"]["field_contract"]["snapshot"]
    assert "portal_display" in data["portal_contract"]["field_contract"]["snapshot"]
    assert "portal_display" in data["portal_contract"]["field_contract"]
    assert "status_badges" in data["portal_contract"]["field_contract"]["portal_display"]
    assert "portal_display_status_badge" in data["portal_contract"]["field_contract"]
    assert "signal_cards" in data["portal_contract"]["field_contract"]["portal_display"]
    assert "portal_display_feedback_cta" in data["portal_contract"]["field_contract"]
    assert "snapshot_links" in data["portal_contract"]["field_contract"]
    assert "feedback_snapshot" in data["portal_contract"]["field_contract"]
    assert "allowed_priorities" in data["portal_contract"]["field_contract"]["feedback_snapshot"]
    assert data["portal_contract"]["field_contract"]["feedback_form_contract"]["allowed_feedback_types"] == [
        "tracking",
        "resource",
        "quality",
        "general",
    ]
    assert data["portal_contract"]["field_contract"]["feedback_form_contract"]["resolution_time_promised"] is False
    assert "next_action_label" in data["portal_contract"]["field_contract"]["customer_status"]
    assert data["portal_contract"]["field_contract"]["date_policy"]["planned_dates_are_guarantees"] is False
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
    new_ticket.id = uuid4()
    new_ticket.ticket_number = "FB-2026-0001"
    new_ticket.order_id = uuid4()
    new_ticket.feedback_type = "tracking"
    new_ticket.subject = "Shipment ETA"
    new_ticket.status = "new"
    new_ticket.priority = "urgent"
    new_ticket.internal_owner = None
    new_ticket.response_summary = None
    new_ticket.created_at = datetime(2026, 5, 29, tzinfo=timezone.utc)

    resolved_ticket = MagicMock()
    resolved_ticket.id = uuid4()
    resolved_ticket.ticket_number = "FB-2026-0002"
    resolved_ticket.order_id = None
    resolved_ticket.feedback_type = "quality"
    resolved_ticket.subject = "Resolved quality note"
    resolved_ticket.status = "resolved"
    resolved_ticket.priority = "normal"
    resolved_ticket.internal_owner = "Ops"
    resolved_ticket.response_summary = None
    resolved_ticket.created_at = datetime(2026, 5, 30, tzinfo=timezone.utc)

    data = _build_feedback_operations([new_ticket, resolved_ticket])

    assert data["total_count"] == 2
    assert data["open_count"] == 1
    assert data["high_priority_count"] == 1
    assert data["needs_internal_review_count"] == 2
    assert data["response_summary_missing_count"] == 1
    assert data["ready_to_close_count"] == 1
    assert [item["action"] for item in data["action_items"]] == [
        "assign_internal_owner",
        "close_resolved_ticket",
    ]
    assert data["action_items"][0]["ticket_number"] == "FB-2026-0001"
    assert data["action_items"][0]["subject"] == "Shipment ETA"
    assert data["action_items"][0]["action_label"] == "Assign internal owner"
    assert data["action_items"][0]["route_query"]["ticket_id"] == str(new_ticket.id)
    assert data["action_items"][0]["route_query"]["status"] == "new"
    assert data["action_items"][0]["route_query"]["priority"] == "urgent"
    assert data["action_items"][0]["route_query"]["feedback_type"] == "tracking"
    assert data["action_items"][1]["action_label"] == "Close resolved ticket"
    assert data["action_items"][1]["route_query"]["status"] == "resolved"
    assert data["action_items"][0]["safety"]["internal_queue_only"] is True
    assert data["action_items"][0]["safety"]["customer_notified"] is False
    assert data["action_items"][0]["safety"]["automatic_reply_sent"] is False
    assert data["action_items"][0]["safety"]["sla_promised"] is False
    assert data["safety"]["internal_queue_only"] is True
    assert data["safety"]["customer_notified"] is False
    assert data["safety"]["automatic_reply_sent"] is False
    assert data["safety"]["sla_promised"] is False


def test_customer_snapshot_readiness_summarizes_portal_tracking_state():
    from app.services.portal.operations_console import _build_customer_snapshot_readiness

    data = _build_customer_snapshot_readiness(
        [
            {
                "order": {"id": str(uuid4()), "order_number": "O-1"},
                "customer_status": {
                    "stage": "ready_to_ship",
                    "label": "Ready to ship",
                    "next_action_label": "Shipment planning",
                    "production_started": True,
                    "production_completed": True,
                    "ready_to_ship": True,
                    "shipped": False,
                    "delivered": False,
                    "progress_steps": [{"key": "confirmed"}],
                },
                "tracking_summary": {
                    "has_production_updates": True,
                    "has_active_shipment": True,
                    "has_visible_resources": True,
                    "has_open_feedback": True,
                },
                "shipment": {"active_count": 1},
                "feedback": {"open_count": 2},
            },
            {
                "order": {"id": str(uuid4()), "order_number": "O-2"},
                "customer_status": {
                    "stage": "shipped",
                    "label": "Shipment in transit",
                    "next_action_label": "Track shipment",
                    "production_started": True,
                    "production_completed": True,
                    "ready_to_ship": True,
                    "shipped": True,
                    "delivered": False,
                    "progress_steps": [{"key": "confirmed"}],
                },
                "tracking_summary": {
                    "has_production_updates": True,
                    "has_active_shipment": True,
                    "has_visible_resources": False,
                    "has_open_feedback": False,
                },
                "shipment": {"active_count": 1},
                "feedback": {"open_count": 0},
            },
        ]
    )

    assert data["snapshot_count"] == 2
    assert data["stage_counts"] == {"ready_to_ship": 1, "shipped": 1}
    assert data["portal_ready"] is True
    assert data["production_visible_count"] == 2
    assert data["ready_to_ship_count"] == 2
    assert data["shipped_count"] == 1
    assert data["active_shipment_count"] == 2
    assert data["open_feedback_count"] == 2
    assert [item["action"] for item in data["action_items"]] == [
        "review_open_feedback_before_customer_update",
        "publish_customer_visible_resource",
    ]
    assert data["action_items"][0]["order_number"] == "O-1"
    assert data["action_items"][0]["stage"] == "ready_to_ship"
    assert data["action_items"][0]["safety"]["read_only"] is True
    assert data["action_items"][0]["safety"]["shipment_created"] is False
    assert data["action_items"][0]["safety"]["order_status_mutated"] is False
    assert data["safety"]["customer_visible_only"] is True
    assert data["safety"]["planned_dates_are_guarantees"] is False
    assert data["safety"]["customer_notified"] is False


def test_shipment_readiness_flags_portal_tracking_actions():
    from datetime import date

    from app.services.portal.operations_console import _build_shipment_readiness

    planned_missing_dates = MagicMock()
    planned_missing_dates.id = uuid4()
    planned_missing_dates.order_id = uuid4()
    planned_missing_dates.partner_split_id = None
    planned_missing_dates.status = "planned"
    planned_missing_dates.shipment_method = "sea"
    planned_missing_dates.estimated_ship_date = None
    planned_missing_dates.estimated_arrival_date = date(2026, 7, 20)
    planned_missing_dates.tracking_number = None

    shipped_missing_tracking = MagicMock()
    shipped_missing_tracking.id = uuid4()
    shipped_missing_tracking.order_id = uuid4()
    shipped_missing_tracking.partner_split_id = uuid4()
    shipped_missing_tracking.status = "shipped"
    shipped_missing_tracking.shipment_method = "air"
    shipped_missing_tracking.estimated_ship_date = date(2026, 6, 20)
    shipped_missing_tracking.estimated_arrival_date = date(2026, 6, 28)
    shipped_missing_tracking.tracking_number = None

    delivered = MagicMock()
    delivered.id = uuid4()
    delivered.order_id = uuid4()
    delivered.partner_split_id = None
    delivered.status = "delivered"
    delivered.shipment_method = "sea"
    delivered.estimated_ship_date = date(2026, 5, 1)
    delivered.estimated_arrival_date = date(2026, 6, 1)
    delivered.tracking_number = "TRACK-SECRET"

    data = _build_shipment_readiness([planned_missing_dates, shipped_missing_tracking, delivered])

    assert data["total_count"] == 3
    assert data["active_count"] == 3
    assert data["planned_count"] == 1
    assert data["shipped_count"] == 1
    assert data["delivered_count"] == 1
    assert data["missing_estimated_dates_count"] == 1
    assert data["shipped_without_tracking_count"] == 1
    assert data["ready"] is False
    assert [item["action"] for item in data["action_items"]] == [
        "add_estimated_shipment_dates",
        "add_tracking_number_for_portal",
    ]
    assert data["action_items"][1]["tracking_number_present"] is False
    assert data["action_items"][1]["safety"]["carrier_api_called"] is False
    assert data["action_items"][1]["safety"]["shipment_created"] is False
    assert data["action_items"][1]["safety"]["tracking_number_value_exposed"] is False
    assert "TRACK-SECRET" not in str(data)
    assert data["safety"]["tracking_number_values_exposed"] is False
    assert data["safety"]["planned_dates_are_guarantees"] is False


def test_recent_orders_include_portal_tracking_summary():
    from app.services.portal.operations_console import _attach_portal_tracking_to_recent_orders

    order_id = str(uuid4())
    data = _attach_portal_tracking_to_recent_orders(
        {
            "items": [
                {"id": order_id, "order_number": "O-1", "status": "confirmed"},
                {"id": str(uuid4()), "order_number": "O-2", "status": "confirmed"},
            ],
            "total": 2,
            "page": 1,
            "limit": 8,
        },
        [
            {
                "order": {"id": order_id, "order_number": "O-1"},
                "customer_status": {
                    "stage": "ready_to_ship",
                    "label": "Ready to ship",
                    "next_action_label": "Shipment planning",
                },
                "tracking_summary": {
                    "has_production_updates": True,
                    "has_active_shipment": True,
                    "has_visible_resources": False,
                    "has_open_feedback": True,
                },
                "shipment": {"active_count": 1},
                "feedback": {"open_count": 2},
            }
        ],
    )

    first = data["items"][0]["portal_tracking"]
    second = data["items"][1]["portal_tracking"]
    assert first["snapshot_available"] is True
    assert first["stage"] == "ready_to_ship"
    assert first["next_action_label"] == "Shipment planning"
    assert first["active_shipment_count"] == 1
    assert first["open_feedback_count"] == 2
    assert first["planned_dates_are_guarantees"] is False
    assert second["snapshot_available"] is False
    assert second["active_shipment_count"] == 0


def test_snapshot_coverage_flags_recent_orders_without_snapshots():
    from app.services.portal.operations_console import _build_snapshot_coverage

    covered_order_id = str(uuid4())
    missing_order_id = str(uuid4())
    data = _build_snapshot_coverage(
        {
            "items": [
                {"id": covered_order_id, "order_number": "O-1", "status": "confirmed"},
                {"id": missing_order_id, "order_number": "O-2", "status": "ready_to_ship"},
            ]
        },
        [{"order": {"id": covered_order_id, "order_number": "O-1"}}],
    )

    assert data["recent_order_count"] == 2
    assert data["snapshot_count"] == 1
    assert data["missing_snapshot_count"] == 1
    assert data["coverage_complete"] is False
    assert data["action_items"][0]["order_id"] == missing_order_id
    assert data["action_items"][0]["order_number"] == "O-2"
    assert data["action_items"][0]["action"] == "build_customer_order_snapshot"
    assert data["action_items"][0]["safety"]["customer_notified"] is False
    assert data["safety"]["planned_dates_are_guarantees"] is False


def test_resource_readiness_summarizes_customer_visible_resources_without_paths():
    from app.services.portal.operations_console import _build_resource_readiness

    published_visible = MagicMock()
    published_visible.id = uuid4()
    published_visible.order_id = uuid4()
    published_visible.title = "Packing list"
    published_visible.status = "published"
    published_visible.category = "packing_list"
    published_visible.customer_visible = True

    draft_visible = MagicMock()
    draft_visible.id = uuid4()
    draft_visible.order_id = uuid4()
    draft_visible.title = "Spec sheet"
    draft_visible.status = "draft"
    draft_visible.category = "spec_sheet"
    draft_visible.customer_visible = True

    hidden_published = MagicMock()
    hidden_published.id = uuid4()
    hidden_published.order_id = uuid4()
    hidden_published.title = "Certificate"
    hidden_published.status = "published"
    hidden_published.category = "certificate"
    hidden_published.customer_visible = False

    data = _build_resource_readiness([published_visible, draft_visible, hidden_published])

    assert data["total_count"] == 3
    assert data["portal_visible_count"] == 1
    assert data["customer_visible_count"] == 2
    assert data["blocked_visibility_count"] == 1
    assert data["hidden_published_count"] == 1
    assert data["status_counts"] == {"published": 2, "draft": 1}
    assert data["category_counts"] == {"packing_list": 1, "spec_sheet": 1, "certificate": 1}
    assert [item["action"] for item in data["action_items"]] == [
        "publish_customer_visible_resource",
        "review_hidden_published_resource",
    ]
    assert data["action_items"][0]["title"] == "Spec sheet"
    assert data["action_items"][0]["portal_visible"] is False
    assert data["action_items"][0]["safety"]["metadata_only"] is True
    assert data["action_items"][0]["safety"]["download_url_exposed"] is False
    assert data["action_items"][0]["safety"]["filesystem_path_exposed"] is False
    assert "storage" not in str(data["action_items"]).lower()
    assert "token" not in str(data["action_items"]).lower().replace("token_value_exposed", "")
    assert data["ready"] is True
    assert data["safety"]["metadata_only"] is True
    assert data["safety"]["download_links_signed"] is True
    assert data["safety"]["file_location_exposed"] is False
    assert data["safety"]["filesystem_path_exposed"] is False


def test_multi_partner_flow_readiness_is_neutral_and_read_only():
    from app.services.portal.operations_console import _build_multi_partner_flow_readiness

    data = _build_multi_partner_flow_readiness(
        {
            "summary": {"partner_count": 2, "order_count": 3, "split_count": 4},
            "items": [
                {
                    "partner_id": "p1",
                    "partner_name": "HOSUN",
                    "partner_type": "Brand",
                    "order_count": 2,
                    "split_count": 2,
                    "line_item_count": 5,
                    "supplier_confirmation_status_counts": {"confirmed": 2},
                    "milestone_status_counts": {"completed": 3},
                    "shipment_status_counts": {"planned": 1},
                    "active_shipment_count": 1,
                    "risk_flags": [],
                },
                {
                    "partner_id": "p2",
                    "partner_name": "JOOBOO",
                    "partner_type": "Factory",
                    "order_count": 1,
                    "split_count": 2,
                    "line_item_count": 3,
                    "supplier_confirmation_status_counts": {"pending": 1},
                    "milestone_status_counts": {},
                    "shipment_status_counts": {},
                    "active_shipment_count": 0,
                    "risk_flags": ["supplier_confirmation_open"],
                },
            ],
        }
    )

    assert data["partner_count"] == 2
    assert data["partners_with_orders"] == 2
    assert data["partners_with_production"] == 1
    assert data["partners_with_shipments"] == 1
    assert data["partners_with_risk"] == 1
    assert [row["partner_name"] for row in data["items"]] == ["HOSUN", "JOOBOO"]
    assert data["safety"]["partner_neutral"] is True
    assert data["safety"]["partner_ranked"] is False
    assert data["safety"]["partner_selection_changed"] is False
    assert data["safety"]["customer_notified"] is False


def test_portal_launch_readiness_aggregates_blockers_without_validating_staging():
    from app.services.portal.operations_console import _build_portal_launch_readiness

    status = {
        "enabled": True,
        "token_required": True,
        "token_configured": False,
        "public_base_url_configured": True,
        "missing_config": ["PORTAL_CUSTOMER_API_TOKEN"],
    }
    data = _build_portal_launch_readiness(
        status=status,
        runtime_health={"ok": True, "database_ready": True, "migration_pending": False},
        endpoints={"products": True, "orders": True, "production": True, "shipment": True, "resources": True, "feedback": True},
        forbidden_field_audit={"hits": []},
        customer_snapshot_readiness={"portal_ready": False},
        snapshot_coverage={"coverage_complete": False, "missing_snapshot_count": 1},
        shipment_readiness={"ready": False, "missing_estimated_dates_count": 1, "shipped_without_tracking_count": 1},
        resource_readiness={"ready": False, "blocked_visibility_count": 1},
        feedback_operations={"needs_internal_review_count": 2},
    )

    assert data["ready_for_real_staging"] is False
    assert "portal customer token missing" in data["blockers"]
    assert "missing config: PORTAL_CUSTOMER_API_TOKEN" in data["blockers"]
    assert "customer order snapshots need representative progress data" in data["warnings"]
    assert "recent customer-visible orders need snapshot coverage" in data["warnings"]
    assert "shipment plans need estimated ship and arrival dates" in data["warnings"]
    assert "shipped plans need tracking numbers for Portal" in data["warnings"]
    assert "customer-visible resources need publishing" in data["warnings"]
    assert data["checks"]["all_endpoints_ready"] is True
    assert data["checks"]["shipments_ready"] is False
    assert data["checks"]["resources_ready"] is False
    assert data["safety"]["read_only"] is True
    assert data["safety"]["staging_validated"] is False
    assert data["safety"]["token_value_exposed"] is False


def test_staging_integration_checklist_is_actionable_without_proof_records():
    from app.services.portal.operations_console import _build_staging_integration_checklist

    data = _build_staging_integration_checklist(
        status={
            "enabled": True,
            "token_configured": True,
            "missing_config": [],
        },
        runtime_health={"database_ready": True, "database_status": "ready", "migration_pending": False},
        endpoints={"products": True, "orders": True, "production": True, "shipment": True, "resources": True, "feedback": True},
        forbidden_field_audit={"hits": []},
        customer_snapshot_readiness={"portal_ready": False, "snapshot_count": 2, "missing_progress_count": 1},
        snapshot_coverage={"coverage_complete": False, "missing_snapshot_count": 1},
        shipment_readiness={"ready": False, "missing_estimated_dates_count": 1, "shipped_without_tracking_count": 0},
        resource_readiness={"ready": True, "portal_visible_count": 1, "blocked_visibility_count": 1},
        feedback_operations={"needs_internal_review_count": 2, "ready_to_close_count": 1},
    )

    statuses = {item["key"]: item["status"] for item in data["items"]}
    assert statuses["configure_portal_api"] == "done"
    assert statuses["verify_clean_runtime"] == "done"
    assert statuses["review_customer_snapshots"] == "needs_operator_action"
    assert statuses["complete_shipment_tracking"] == "needs_operator_action"
    assert statuses["publish_customer_resources"] == "needs_operator_action"
    assert statuses["triage_feedback_queue"] == "needs_operator_action"
    assert statuses["run_service_portal_smoke"] == "ready_for_operator"
    assert data["blocked_count"] == 0
    assert data["operator_action_count"] == 4
    assert data["ready_for_staging_operator"] is True
    assert data["safety"]["read_only"] is True
    assert data["safety"]["staging_validated"] is False
    assert data["safety"]["proof_record_created"] is False
    assert data["safety"]["deployment_triggered"] is False
    assert "secret" not in str(data).lower()
