"""Unit tests for D7.4 partner split and supplier confirmation services."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.errors import ApiError, VALIDATION_ERROR
from app.services.orders.supplier_confirmation_service import _build_warnings, supplier_confirmation_safety


def test_supplier_confirmation_safety_defaults():
    safety = supplier_confirmation_safety(recorded=True)
    assert safety["supplier_confirmation_recorded"] is True
    assert safety["supplier_notified"] is False
    assert safety["production_started"] is False
    assert safety["shipment_created"] is False
    assert safety["inventory_promised"] is False


def test_supplier_confirmation_safety_explicit_flags():
    safety = supplier_confirmation_safety(
        recorded=True,
        inventory_confirmed=True,
        lead_time_confirmed=True,
    )
    assert safety["inventory_promised"] is True
    assert safety["lead_time_promised"] is True
    assert safety["certification_promised"] is False


def test_build_warnings_includes_production_shipment():
    row = MagicMock(
        inventory_confirmed=False,
        certification_confirmed=False,
        lead_time_confirmed=False,
        production_capacity_confirmed=False,
    )
    warnings = _build_warnings(row)
    assert any("production" in w for w in warnings)
    assert any("shipment" in w for w in warnings)


@patch("app.services.orders.partner_split_service.get_partner_splits")
@patch("app.services.orders.partner_split_service.log_activity")
@patch("app.services.orders.partner_split_service.get_order")
def test_ensure_partner_splits_rejects_cancelled(mock_get_order, mock_log, mock_get_splits):
    from app.services.orders.partner_split_service import ensure_partner_splits

    order = MagicMock()
    order.id = uuid4()
    order.status = "cancelled"
    order.line_items = []
    mock_get_order.return_value = order
    mock_get_splits.return_value = []
    db = MagicMock()

    with pytest.raises(ApiError) as exc:
        ensure_partner_splits(db, uuid4(), order.id)
    assert exc.value.status_code == 400


@patch("app.services.orders.supplier_confirmation_service.get_partner_split")
@patch("app.services.orders.supplier_confirmation_service.log_activity")
@patch("app.services.orders.supplier_confirmation_service.get_order")
def test_add_supplier_confirmation_rejects_pending_order(mock_get_order, mock_log, mock_get_split):
    from app.services.orders.supplier_confirmation_service import add_supplier_confirmation

    order = MagicMock()
    order.id = uuid4()
    order.status = "pending_customer_confirmation"
    mock_get_order.return_value = order
    user = MagicMock(id=uuid4())
    db = MagicMock()

    with pytest.raises(ApiError) as exc:
        add_supplier_confirmation(
            db, user, order.id, uuid4(), confirmation_status="confirmed"
        )
    assert exc.value.status_code == 400


@patch("app.services.orders.partner_split_service.get_partner_splits")
@patch("app.services.orders.partner_split_service.log_activity")
@patch("app.services.orders.partner_split_service.get_order")
def test_ensure_partner_splits_groups_by_partner(mock_get_order, mock_log, mock_get_splits):
    from app.services.orders.partner_split_service import ensure_partner_splits

    partner_a = uuid4()
    partner_b = uuid4()
    line_a = MagicMock(partner_id=partner_a, total_price=Decimal("100"), status="pending")
    line_b = MagicMock(partner_id=partner_b, total_price=Decimal("200"), status="pending")
    order = MagicMock()
    order.id = uuid4()
    order.status = "confirmed"
    order.currency = "USD"
    order.line_items = [line_a, line_b]
    mock_get_order.return_value = order
    mock_get_splits.side_effect = [[], [MagicMock(partner_id=partner_a), MagicMock(partner_id=partner_b)]]
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.commit = MagicMock()

    result = ensure_partner_splits(db, uuid4(), order.id)
    assert result["created"] == 2
    assert len(result["splits"]) == 2
