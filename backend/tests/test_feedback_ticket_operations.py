"""Tests for D7.8 feedback ticket operations."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import ApiError
from app.main import create_app
from app.models import ActivityLog, User
from app.services.portal.feedback_ticket_service import feedback_safety, list_feedback_tickets, ticket_to_dict, update_feedback_ticket


def _ticket(**overrides):
    row = MagicMock()
    row.id = overrides.get("id", uuid4())
    row.ticket_number = overrides.get("ticket_number", "FB-2026-0001")
    row.source = overrides.get("source", "customer_portal")
    row.order_id = overrides.get("order_id")
    row.company_id = overrides.get("company_id")
    row.feedback_type = overrides.get("feedback_type", "tracking")
    row.subject = overrides.get("subject", "TEST shipment question")
    row.message = overrides.get("message", "TEST: customer asks for shipment status.")
    row.status = overrides.get("status", "new")
    row.priority = overrides.get("priority", "normal")
    row.internal_owner = overrides.get("internal_owner")
    row.customer_name = overrides.get("customer_name", "Test User")
    row.customer_email = overrides.get("customer_email", "test@example.com")
    row.response_summary = overrides.get("response_summary")
    row.created_at = overrides.get("created_at", datetime(2026, 5, 29, tzinfo=timezone.utc))
    row.updated_at = overrides.get("updated_at", datetime(2026, 5, 29, tzinfo=timezone.utc))
    return row


def test_ticket_to_dict_has_operations_safety_flags():
    data = ticket_to_dict(_ticket(internal_owner="Operator"))
    assert data["internal_owner"] == "Operator"
    assert data["operation"]["internal_handling_only"] is True
    assert data["operation"]["activity_logging_enabled"] is True
    assert data["operation"]["age_days"] is not None
    assert data["operation"]["open"] is True
    assert data["operation"]["needs_internal_review"] is True
    assert data["operation"]["response_summary_missing"] is False
    assert data["safety"] == feedback_safety()
    assert data["safety"]["customer_notified"] is False
    assert data["safety"]["automatic_reply_sent"] is False
    assert data["safety"]["sla_promised"] is False


def test_ticket_to_dict_marks_missing_internal_resolution_summary():
    data = ticket_to_dict(_ticket(status="resolved", response_summary=None))
    assert data["operation"]["open"] is False
    assert data["operation"]["needs_internal_review"] is True
    assert data["operation"]["response_summary_missing"] is True
    assert data["operation"]["customer_visible_response"] is False


def test_update_feedback_ticket_validates_status_and_priority():
    db = MagicMock()
    row = _ticket()
    db.query.return_value.filter.return_value.first.return_value = row

    updated = update_feedback_ticket(
        db,
        row.id,
        status="in_review",
        priority="high",
        internal_owner="Ops",
        response_summary="Reviewed internally. No customer reply sent.",
        actor_id=uuid4(),
    )

    assert updated.status == "in_review"
    assert updated.priority == "high"
    assert updated.internal_owner == "Ops"
    assert updated.response_summary.startswith("Reviewed")
    activity = next(call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], ActivityLog))
    assert activity.object_type == "feedback_ticket"
    assert activity.object_id == row.id
    assert activity.action == "feedback_status_changed"
    assert activity.diff["current"]["customer_notified"] is False
    assert activity.diff["current"]["automatic_reply_sent"] is False
    db.commit.assert_called_once()

    with pytest.raises(ApiError):
        update_feedback_ticket(db, row.id, status="emailed_customer")


def test_list_feedback_tickets_validates_operation_filter():
    db = MagicMock()

    with pytest.raises(ApiError):
        list_feedback_tickets(db, operation_filter="email_customer")


def test_feedback_ticket_routes(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="ops@test.example", is_active=True)
    db = MagicMock()
    ticket_id = uuid4()
    order_id = uuid4()
    list_kwargs = {}

    def fake_list_feedback_tickets(*args, **kwargs):
        list_kwargs.update(kwargs)
        return {"items": [ticket_to_dict(_ticket(id=ticket_id, order_id=order_id))], "total": 1, "page": 1, "limit": 50}

    monkeypatch.setattr("app.api.v1.routes.feedback_tickets.list_feedback_tickets", fake_list_feedback_tickets)
    monkeypatch.setattr(
        "app.api.v1.routes.feedback_tickets.get_feedback_ticket",
        lambda db_, tid: _ticket(id=tid, status="new"),
    )
    monkeypatch.setattr(
        "app.api.v1.routes.feedback_tickets.update_feedback_ticket",
        lambda db_, tid, **kwargs: _ticket(
            id=tid,
            status=kwargs.get("status") or "new",
            priority=kwargs.get("priority") or "normal",
            internal_owner=kwargs.get("internal_owner"),
            response_summary=kwargs.get("response_summary"),
        ),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield db)

    with TestClient(app) as client:
        listed = client.get(
            f"/api/v1/feedback-tickets?status=new&priority=normal&order_id={order_id}"
            "&operation_filter=needs_internal_review"
        )
        detail = client.get(f"/api/v1/feedback-tickets/{ticket_id}")
        patched = client.patch(
            f"/api/v1/feedback-tickets/{ticket_id}",
            json={
                "status": "resolved",
                "priority": "high",
                "internal_owner": "Ops",
                "response_summary": "TEST resolution summary. No customer notification sent.",
            },
        )
        resolved = client.post(
            f"/api/v1/feedback-tickets/{ticket_id}/resolve",
            json={"priority": "high", "internal_owner": "Ops", "response_summary": "Resolved internally."},
        )
        closed = client.post(
            f"/api/v1/feedback-tickets/{ticket_id}/close",
            json={"internal_owner": "Ops", "response_summary": "Closed internally."},
        )

    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1
    assert listed.json()["data"]["items"][0]["order_id"] == str(order_id)
    assert list_kwargs["order_id"] == order_id
    assert list_kwargs["operation_filter"] == "needs_internal_review"
    assert detail.status_code == 200
    assert patched.status_code == 200
    assert patched.json()["data"]["status"] == "resolved"
    assert patched.json()["data"]["safety"]["email_sent"] is False
    assert resolved.status_code == 200
    assert resolved.json()["data"]["status"] == "resolved"
    assert resolved.json()["data"]["safety"]["customer_notified"] is False
    assert closed.status_code == 200
    assert closed.json()["data"]["status"] == "closed"
    assert closed.json()["data"]["safety"]["automatic_reply_sent"] is False
