"""Unit tests for D6.5 quote delivery and mark-sent."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.errors import ApiError
from app.services.quotes.quote_delivery_service import (
    DELIVERY_SAFETY,
    delivery_log_to_dict,
    list_delivery_logs,
    mark_sent_with_delivery,
    mask_email,
)


def _quote(status="ready_to_send", *, expired=False):
    quote_id = uuid4()
    valid = date.today() - timedelta(days=1) if expired else date.today() + timedelta(days=21)
    quote = SimpleNamespace(
        id=quote_id,
        quote_number="Q-2026-0001",
        status=status,
        valid_until=valid,
        manual_sent=False,
        bill_to_name="Jane",
        bill_to_company="Acme",
        sent_at=None,
        sent_by_id=None,
        send_channel=None,
        last_delivery_log_id=None,
        follow_up_date=None,
        updated_by_id=None,
        line_items=[SimpleNamespace()],
    )
    return quote


def test_mask_email():
    assert mask_email("james@example.com") == "j***@example.com"
    assert mask_email(None) is None


def test_mark_sent_creates_delivery_log(monkeypatch):
    quote = _quote()
    user = SimpleNamespace(id=uuid4())
    db = MagicMock()
    added = []

    def _add(obj):
        added.append(obj)

    db.add.side_effect = _add
    monkeypatch.setattr("app.services.quotes.quote_delivery_service.get_quote", lambda db_, qid: quote)
    monkeypatch.setattr(
        "app.services.quotes.quote_delivery_service.derived_expired",
        lambda q, today=None: False,
    )

    result = mark_sent_with_delivery(
        db,
        quote.id,
        user=user,
        sent_channel="email",
        sent_to_name="Bob",
        sent_to_company="Acme",
        follow_up_date=date(2026, 5, 29),
    )
    assert result["status"] == "sent"
    assert result["delivery_log"]["sent_channel"] == "email"
    assert result["safety"] == DELIVERY_SAFETY
    assert quote.status == "sent"
    assert quote.manual_sent is True
    assert len(added) == 1
    assert added[0].manual_sent is True
    db.commit.assert_called()


def test_internal_review_cannot_mark_sent(monkeypatch):
    quote = _quote(status="internal_review")
    user = SimpleNamespace(id=uuid4())
    db = MagicMock()
    monkeypatch.setattr("app.services.quotes.quote_delivery_service.get_quote", lambda db_, qid: quote)
    monkeypatch.setattr(
        "app.services.quotes.quote_delivery_service.derived_expired",
        lambda q, today=None: False,
    )
    with pytest.raises(ApiError) as exc:
        mark_sent_with_delivery(db, quote.id, user=user, sent_channel="email")
    assert exc.value.status_code == 400


def test_expired_cannot_mark_sent(monkeypatch):
    quote = _quote(status="ready_to_send", expired=True)
    user = SimpleNamespace(id=uuid4())
    db = MagicMock()
    monkeypatch.setattr("app.services.quotes.quote_delivery_service.get_quote", lambda db_, qid: quote)
    monkeypatch.setattr(
        "app.services.quotes.quote_delivery_service.derived_expired",
        lambda q, today=None: True,
    )
    with pytest.raises(ApiError):
        mark_sent_with_delivery(db, quote.id, user=user, sent_channel="email")


def test_already_sent_appends_log(monkeypatch):
    quote = _quote(status="sent")
    quote.manual_sent = True
    user = SimpleNamespace(id=uuid4())
    db = MagicMock()
    monkeypatch.setattr("app.services.quotes.quote_delivery_service.get_quote", lambda db_, qid: quote)
    monkeypatch.setattr(
        "app.services.quotes.quote_delivery_service.derived_expired",
        lambda q, today=None: False,
    )
    result = mark_sent_with_delivery(db, quote.id, user=user, sent_channel="phone")
    assert result["status"] == "sent"
    assert "already sent" in result["warnings"][0]


def test_pdf_export_must_belong_to_quote(monkeypatch):
    quote = _quote()
    user = SimpleNamespace(id=uuid4())
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    monkeypatch.setattr("app.services.quotes.quote_delivery_service.get_quote", lambda db_, qid: quote)
    monkeypatch.setattr(
        "app.services.quotes.quote_delivery_service.derived_expired",
        lambda q, today=None: False,
    )
    with pytest.raises(ApiError) as exc:
        mark_sent_with_delivery(db, quote.id, user=user, sent_channel="email", pdf_export_id=uuid4())
    assert "pdf_export_id" in str(exc.value.message).lower() or "pdf_export" in str(exc.value).lower()
