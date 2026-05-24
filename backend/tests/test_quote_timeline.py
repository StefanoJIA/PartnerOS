"""Tests for D6.5 quote timeline."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.services.quotes.quote_timeline import build_quote_timeline


def test_timeline_includes_pdf_and_manual_sent(monkeypatch):
    quote_id = uuid4()
    now = datetime.now(timezone.utc)
    export_id = uuid4()
    log_id = uuid4()

    quote = SimpleNamespace(
        id=quote_id,
        quote_number="Q-2026-0001",
        created_at=now - timedelta(days=2),
        updated_at=now,
        sent_at=now,
        follow_up_date=date(2026, 5, 29),
        versions=[
            SimpleNamespace(
                version_number=1,
                version_label="v1",
                version_type="internal_version",
                created_at=now - timedelta(days=1),
                created_by_id=None,
            )
        ],
        pdf_exports=[
            SimpleNamespace(
                id=export_id,
                status="generated",
                file_name="Quote.pdf",
                exported_at=now - timedelta(hours=2),
                created_at=now - timedelta(hours=2),
                exported_by_id=None,
            )
        ],
        delivery_logs=[
            SimpleNamespace(
                id=log_id,
                status="recorded",
                sent_at=now - timedelta(hours=1),
                sent_channel="email",
                sent_to_name="Bob",
                sent_to_email="bob@example.com",
                sent_to_company="Acme",
                sent_by_id=None,
                quote_id=quote_id,
                quote_version_id=None,
                pdf_export_id=export_id,
                manual_sent=True,
                follow_up_date=None,
                note=None,
            )
        ],
        is_archived=False,
    )

    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.first.return_value = quote
    db.query.return_value.filter.return_value.first.return_value = None

    data = build_quote_timeline(db, quote_id)
    types = [i["type"] for i in data["items"]]
    assert "quote_created" in types
    assert "version_created" in types
    assert "pdf_exported" in types
    assert "manual_sent" in types
    assert "follow_up_scheduled" in types
    assert "internal_cost" not in str(data).lower()
