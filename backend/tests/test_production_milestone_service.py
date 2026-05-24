"""Unit tests for D7.5 production milestone service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.errors import ApiError


def test_milestone_safety_defaults():
    from app.services.orders.production_milestone_service import milestone_safety

    s = milestone_safety(updated=True)
    assert s["production_started"] is False
    assert s["shipment_created"] is False
    assert s["supplier_notified"] is False
    assert s["customer_notified"] is False
    assert s["milestone_updated"] is True


@patch("app.services.orders.production_milestone_service.get_partner_split")
@patch("app.services.orders.production_milestone_service.get_order")
def test_ensure_rejects_pending_order(mock_get_order, mock_get_split):
    from app.services.orders.production_milestone_service import ensure_production_milestones

    order = MagicMock()
    order.id = uuid4()
    order.status = "pending_customer_confirmation"
    mock_get_order.return_value = order
    user = MagicMock(id=uuid4())
    db = MagicMock()

    with pytest.raises(ApiError) as exc:
        ensure_production_milestones(db, user, order.id, uuid4())
    assert exc.value.status_code == 400


@patch("app.services.orders.production_milestone_service.list_production_milestones")
@patch("app.services.orders.production_milestone_service.get_partner_split")
@patch("app.services.orders.production_milestone_service.get_order")
def test_ensure_rejects_cancelled(mock_get_order, mock_get_split, mock_list):
    from app.services.orders.production_milestone_service import ensure_production_milestones

    order = MagicMock()
    order.id = uuid4()
    order.status = "cancelled"
    mock_get_order.return_value = order
    user = MagicMock(id=uuid4())
    db = MagicMock()

    with pytest.raises(ApiError) as exc:
        ensure_production_milestones(db, user, order.id, uuid4())
    assert exc.value.status_code == 400
