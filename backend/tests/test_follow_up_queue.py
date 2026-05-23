"""Tests for follow-up queue service (D5.7)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models import Company, Interaction, Lead, MarketIntelligenceItem
from app.services.a_domain.follow_up_queue import (
    apply_follow_up_schedule,
    build_follow_up_queue_rows,
    compute_due_status,
    summarize_follow_up_queue,
)


def test_compute_due_status_rules():
    today = date(2026, 5, 23)
    assert compute_due_status(None, today)[0] == "no_follow_up_date"
    assert compute_due_status(date(2026, 5, 20), today)[0] == "overdue"
    assert compute_due_status(date(2026, 5, 23), today)[0] == "due_today"
    assert compute_due_status(date(2026, 5, 28), today)[0] == "due_soon"
    assert compute_due_status(date(2026, 6, 15), today)[0] == "scheduled"


def test_migration_not_needed_uses_next_action_due_date():
    lead = Lead(
        id=uuid4(),
        company_id=uuid4(),
        lead_name="L",
        source="Referral",
        lead_type="New Business",
        current_stage="New",
        next_action_due_date=date(2026, 5, 28),
        is_active=True,
    )
    assert lead.next_action_due_date == date(2026, 5, 28)


def test_patch_follow_up_updates_date(monkeypatch):
    user = MagicMock(id=uuid4())
    lead_id = uuid4()
    company_id = uuid4()
    lead = Lead(
        id=lead_id,
        company_id=company_id,
        lead_name="L",
        source="Referral",
        lead_type="New Business",
        current_stage="New",
        is_active=True,
    )
    company = Company(id=company_id, company_name="Acme", company_type="Dealer")

    db = MagicMock()

    def query(model):
        q = MagicMock()
        if model is Lead:
            q.filter.return_value.first.return_value = lead
        elif model is Company:
            q.filter.return_value.first.return_value = company
        return q

    db.query.side_effect = query

    result = apply_follow_up_schedule(
        db,
        user,
        lead_id,
        next_follow_up_date=date(2026, 5, 28),
        next_action="Follow up in 5 days",
        status_note="Test schedule",
    )
    assert lead.next_action_due_date == date(2026, 5, 28)
    assert lead.next_action == "Follow up in 5 days"
    assert result["due_status"] == "due_soon"
    assert result["interaction_id"]


def test_patch_follow_up_writes_touchpoint():
    user = MagicMock(id=uuid4())
    lead_id = uuid4()
    company_id = uuid4()
    lead = Lead(
        id=lead_id,
        company_id=company_id,
        lead_name="L",
        source="Referral",
        lead_type="New Business",
        current_stage="New",
        is_active=True,
    )
    company = Company(id=company_id, company_name="Acme", company_type="Dealer")

    db = MagicMock()
    added = []

    def query(model):
        q = MagicMock()
        if model is Lead:
            q.filter.return_value.first.return_value = lead
        elif model is Company:
            q.filter.return_value.first.return_value = company
        return q

    db.query.side_effect = query
    db.add.side_effect = lambda o: added.append(o)

    apply_follow_up_schedule(
        db,
        user,
        lead_id,
        next_follow_up_date=date(2026, 5, 30),
        next_action=None,
        status_note="Scheduled",
    )
    interactions = [o for o in added if isinstance(o, Interaction)]
    assert interactions
    assert interactions[0].interaction_type == "follow_up_scheduled"
    assert interactions[0].channel == "internal"
    assert "manually_scheduled=true" in (interactions[0].summary or "")


def test_follow_up_queue_summary(monkeypatch):
    lead_id = uuid4()
    company_id = uuid4()
    lead = Lead(
        id=lead_id,
        company_id=company_id,
        lead_name="L",
        source="Referral",
        lead_type="New Business",
        current_stage="New",
        next_action_due_date=date(2026, 5, 20),
        next_action="Wait",
        is_active=True,
    )
    company = Company(id=company_id, company_name="Co", company_type="Dealer")

    db = MagicMock()

    def query(model):
        q = MagicMock()
        if model is Lead:
            q.filter.return_value.order_by.return_value.all.return_value = [lead]
        elif model is Company:
            q.filter.return_value.first.return_value = company
        elif model is Interaction:
            q.filter.return_value.order_by.return_value.first.return_value = None
            q.filter.return_value.count.return_value = 0
        elif model is MarketIntelligenceItem:
            q.filter.return_value.count.return_value = 0
        return q

    db.query.side_effect = query
    monkeypatch.setattr(
        "app.services.a_domain.follow_up_queue.compute_intelligence_score",
        lambda inp: MagicMock(score=50, market_fit_segments=[]),
    )

    rows = build_follow_up_queue_rows(db, today=date(2026, 5, 23))
    summary = summarize_follow_up_queue(rows)
    assert summary["total"] == 1
    assert summary["overdue"] == 1
    assert rows[0]["due_status"] == "overdue"


def test_invalid_lead_raises():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="Lead not found"):
        apply_follow_up_schedule(
            db,
            MagicMock(),
            uuid4(),
            next_follow_up_date=date(2026, 5, 28),
            next_action=None,
            status_note=None,
        )


def test_no_automatic_send_side_effects():
    lead = Lead(
        id=uuid4(),
        company_id=uuid4(),
        lead_name="L",
        source="Referral",
        lead_type="New Business",
        current_stage="New",
        is_active=True,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [lead, Company(id=lead.company_id, company_name="X", company_type="D")]
    apply_follow_up_schedule(
        db,
        MagicMock(id=uuid4()),
        lead.id,
        next_follow_up_date=date(2026, 6, 1),
        next_action="Follow up",
        status_note="x",
    )
    assert getattr(lead, "outreach_sent", None) is None
