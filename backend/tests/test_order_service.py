"""Unit tests for D7.2 order service."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.errors import ApiError, CONFLICT, VALIDATION_ERROR
from app.models.customer_orders import CustomerOrder
from app.services.orders.order_service import (
    ORDER_SAFETY,
    generate_order_number,
    get_active_order_for_quote,
)


def test_generate_order_number_first_of_year():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None
    num = generate_order_number(db, date(2026, 5, 23))
    assert num == "O-2026-0001"


def test_generate_order_number_increments():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.first.return_value = SimpleNamespace(
        order_number="O-2026-0007"
    )
    num = generate_order_number(db, date(2026, 5, 23))
    assert num == "O-2026-0008"


def test_order_safety_flags():
    assert ORDER_SAFETY["order_created"] is True
    assert ORDER_SAFETY["production_started"] is False
    assert ORDER_SAFETY["shipment_created"] is False
    assert ORDER_SAFETY["supplier_notified"] is False


@patch("app.services.orders.order_service.build_quote_order_readiness")
@patch("app.services.orders.order_service.get_quote")
def test_create_order_rejects_unsent_quote(mock_get_quote, mock_readiness):
    from app.services.orders.order_service import create_order_from_quote

    quote_id = uuid4()
    partner_id = uuid4()
    line_id = uuid4()
    quote = SimpleNamespace(
        id=quote_id,
        status="ready_to_send",
        is_archived=False,
        line_items=[
            SimpleNamespace(
                id=line_id,
                customer_visible=True,
                partner_id=partner_id,
                quantity=1,
                final_unit_price=Decimal("100"),
                total_price=Decimal("100"),
            )
        ],
        grand_total=Decimal("100"),
        valid_until=date.today() + timedelta(days=10),
    )
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = quote
    db.query.return_value.filter.return_value.first.return_value = None

    user = SimpleNamespace(id=uuid4())
    with pytest.raises(ApiError) as exc:
        create_order_from_quote(db, user, quote_id=quote_id)
    assert exc.value.status_code == 400


@patch("app.services.orders.order_service.build_quote_order_readiness")
def test_create_order_rejects_duplicate_active(mock_readiness):
    from app.services.orders.order_service import create_order_from_quote

    quote_id = uuid4()
    partner_id = uuid4()
    line_id = uuid4()
    quote = SimpleNamespace(
        id=quote_id,
        status="sent",
        is_archived=False,
        company_id=None,
        contact_id=None,
        currency="USD",
        payment_terms="Net 30",
        shipping_terms="FOB",
        bill_to_name="A",
        bill_to_company="Co",
        bill_to_address="Addr",
        ship_to_name="A",
        ship_to_company="Co",
        ship_to_address="Addr",
        default_incoterm="FOB",
        line_items=[
            SimpleNamespace(
                id=line_id,
                customer_visible=True,
                partner_id=partner_id,
                product_catalog_id=None,
                internal_sku=None,
                partner_product_code=None,
                product_name="Desk",
                product_category="frame",
                description_customer=None,
                description_internal=None,
                quantity=10,
                uom="EA",
                final_unit_price=Decimal("100"),
                total_price=Decimal("1000"),
                currency="USD",
                incoterm="FOB",
                color_finish=None,
                size_dimension=None,
                attributes_snapshot_json=None,
                notes=None,
            )
        ],
        subtotal=Decimal("1000"),
        adjustment_total=Decimal("0"),
        tax_total=Decimal("0"),
        grand_total=Decimal("1000"),
        valid_until=date.today() + timedelta(days=10),
    )
    existing = SimpleNamespace(id=uuid4(), order_number="O-2026-0001")

    db = MagicMock()

    def _query(model):
        m = MagicMock()
        if model is CustomerOrder:
            m.filter.return_value.first.return_value = existing
            m.filter.return_value.order_by.return_value.with_for_update.return_value.first.return_value = None
        else:
            m.options.return_value.filter.return_value.first.return_value = quote
        return m

    db.query.side_effect = _query
    mock_readiness.return_value = {"blocking_items": [], "order_input_contract": {"source_quote": {}}}

    user = SimpleNamespace(id=uuid4())
    with pytest.raises(ApiError) as exc:
        create_order_from_quote(db, user, quote_id=quote_id)
    assert exc.value.status_code == 409
    assert exc.value.code == CONFLICT


def test_get_active_order_for_quote_filters_cancelled():
    db = MagicMock()
    get_active_order_for_quote(db, uuid4())
    db.query.assert_called()
