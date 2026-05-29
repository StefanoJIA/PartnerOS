"""Unit tests for D7.6 shipment plan foundation."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.errors import ApiError
from app.models import ActivityLog
from app.models.customer_orders import ShipmentPlan


def test_shipment_safety_defaults():
    from app.services.orders.shipment_plan_service import shipment_plan_to_dict, shipment_safety

    assert shipment_safety() == {
        "shipment_created": False,
        "supplier_notified": False,
        "customer_notified": False,
    }

    row = MagicMock()
    row.id = uuid4()
    row.order_id = uuid4()
    row.partner_split_id = None
    row.shipment_method = "sea"
    row.incoterm = "FOB"
    row.origin = "Ningbo"
    row.destination = "New York"
    row.estimated_ship_date = None
    row.estimated_arrival_date = None
    row.tracking_number = None
    row.status = "planned"
    row.notes = None
    row.created_at = None
    row.updated_at = None

    data = shipment_plan_to_dict(row)
    assert data["safety"]["shipment_created"] is False
    assert data["safety"]["supplier_notified"] is False
    assert data["safety"]["customer_notified"] is False
    assert data["portal_visible_fields"]["status"] == "planned"


@patch("app.services.orders.shipment_plan_service.get_order")
def test_create_rejects_pending_customer_confirmation(mock_get_order):
    from app.services.orders.shipment_plan_service import create_shipment_plan

    order = MagicMock()
    order.id = uuid4()
    order.status = "pending_customer_confirmation"
    mock_get_order.return_value = order
    db = MagicMock()
    user = MagicMock(id=uuid4())

    with pytest.raises(ApiError) as exc:
        create_shipment_plan(db, user, order.id, shipment_method="sea")

    assert exc.value.status_code == 400
    assert "customer-confirmed" in str(exc.value)


@patch("app.services.orders.shipment_plan_service.log_activity")
@patch("app.services.orders.shipment_plan_service.get_order")
def test_update_status_records_status_changed_timeline_action(mock_get_order, mock_log_activity):
    from app.services.orders.shipment_plan_service import update_shipment_plan

    order = MagicMock()
    order.id = uuid4()
    order.status = "confirmed"
    mock_get_order.return_value = order

    row = MagicMock()
    row.id = uuid4()
    row.order_id = order.id
    row.status = "planned"

    q = MagicMock()
    q.filter.return_value.first.return_value = row
    db = MagicMock()
    db.query.return_value = q
    user = MagicMock(id=uuid4())

    updated = update_shipment_plan(db, user, order.id, row.id, status="shipped")

    assert updated.status == "shipped"
    mock_log_activity.assert_called_once()
    assert mock_log_activity.call_args.kwargs["action"] == "shipment_status_changed"
    assert mock_log_activity.call_args.kwargs["diff"]["previous_status"] == "planned"
    assert mock_log_activity.call_args.kwargs["diff"]["status"] == "shipped"


def test_timeline_includes_shipment_plan_events():
    from app.services.orders.order_timeline import build_order_timeline

    order = MagicMock()
    order.id = uuid4()
    order.created_at = None
    order.created_by_id = None
    order.status = "confirmed"
    order.cancelled_at = None

    plan_id = uuid4()
    created = MagicMock(spec=ActivityLog)
    created.action = "shipment_plan_created"
    created.created_at = datetime(2026, 5, 29, 12, 0, tzinfo=timezone.utc)
    created.diff = {"shipment_plan_id": str(plan_id), "status": "planned"}
    changed = MagicMock(spec=ActivityLog)
    changed.action = "shipment_status_changed"
    changed.created_at = datetime(2026, 5, 29, 13, 0, tzinfo=timezone.utc)
    changed.diff = {"shipment_plan_id": str(plan_id), "previous_status": "planned", "status": "shipped"}

    class Query:
        def __init__(self, rows):
            self.rows = rows

        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def all(self):
            return self.rows

    db = MagicMock()

    def query(model):
        if model is ActivityLog:
            return Query([created, changed])
        if model is ShipmentPlan:
            return Query([])
        return Query([])

    db.query.side_effect = query

    with patch("app.services.orders.order_timeline.get_order", return_value=order):
        timeline = build_order_timeline(db, order.id)

    types = [item["type"] for item in timeline["items"]]
    assert "shipment_plan_created" in types
    assert "shipment_status_changed" in types
