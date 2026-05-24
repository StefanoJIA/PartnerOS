"""Unit tests for D7.3 order confirmation service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.errors import ApiError, VALIDATION_ERROR
from app.services.orders.order_confirmation_service import infer_strength


def test_infer_strength_mapping():
    assert infer_strength("purchase_order") == "strong"
    assert infer_strength("signed_quote") == "strong"
    assert infer_strength("email") == "medium"
    assert infer_strength("verbal") == "weak"
    assert infer_strength("internal_note") == "weak"


@patch("app.services.orders.order_confirmation_service.get_order")
@patch("app.services.orders.order_confirmation_service.log_activity")
def test_add_confirmation_rejects_cancelled(mock_log, mock_get_order):
    from app.services.orders.order_confirmation_service import add_customer_confirmation

    order = MagicMock()
    order.id = uuid4()
    order.status = "cancelled"
    order.line_items = []
    mock_get_order.return_value = order
    user = MagicMock(id=uuid4())
    db = MagicMock()

    with pytest.raises(ApiError) as exc:
        add_customer_confirmation(db, user, order.id, confirmation_type="email")
    assert exc.value.status_code == 400


def test_build_warnings_verbal():
    from app.services.orders.order_confirmation_service import _build_warnings

    warnings = _build_warnings("verbal", None)
    assert any("verbal" in w for w in warnings)
    assert any("no evidence" in w for w in warnings)
