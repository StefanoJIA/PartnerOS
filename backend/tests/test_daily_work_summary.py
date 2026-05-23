"""Tests for daily work summary service (D5.10)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models import Interaction
from app.services.a_domain.daily_work_summary import (
    _action_label,
    _is_follow_up_scheduled,
    _mask_text,
    build_copyable_summary,
    build_daily_work_summary,
    build_daily_work_summary_degraded,
)


def test_mask_text_redacts_email():
    assert "[email]" in _mask_text("Sent to user@example.com")


def test_action_label_manual_sent():
    ix = Interaction(
        id=uuid4(),
        related_object_type="lead",
        related_object_id=uuid4(),
        interaction_type="email_intro",
        channel="email",
        summary="[manually_sent=true]",
        interaction_date=datetime.now(timezone.utc),
    )
    assert "Manual email intro" in _action_label(ix)


def test_follow_up_scheduled_detection():
    ix = Interaction(
        id=uuid4(),
        related_object_type="lead",
        related_object_id=uuid4(),
        interaction_type="follow_up_scheduled",
        channel="internal",
        summary="manually_scheduled=true",
        interaction_date=datetime.now(timezone.utc),
    )
    assert _is_follow_up_scheduled(ix) is True


def test_copyable_summary_masks_emails():
    text = build_copyable_summary(
        date(2026, 5, 23),
        {"manual_outreach_sent": 1, "contact_research_updates": 0, "follow_ups_scheduled": 0, "leads_touched": 1},
        [{"company_name": "Acme", "action": "Sent to user@example.com", "next_action": None}],
        [],
    )
    assert "user@example.com" not in text
    assert "[email]" not in text or "Acme" in text
    assert "No automatic messages" in text


def test_degraded_readable():
    raw = build_daily_work_summary_degraded(date(2026, 5, 23), "DB down")
    assert raw["degraded"] is True
    assert raw["summary"]["manual_outreach_sent"] == 0
    assert "DB down" in raw["copyable_summary"]


@patch("app.services.a_domain.daily_work_summary._interactions_on_date")
@patch("app.services.a_domain.daily_work_summary.build_lead_completeness_rows")
@patch("app.services.a_domain.daily_work_summary.build_follow_up_queue_rows")
def test_build_daily_work_summary_counts(mock_fu, mock_comp, mock_ix):
    lead_id = uuid4()
    mock_ix.return_value = [
        Interaction(
            id=uuid4(),
            related_object_type="lead",
            related_object_id=lead_id,
            interaction_type="email_intro",
            channel="email",
            summary="[manually_sent=true]",
            interaction_date=datetime(2026, 5, 23, 12, 0, tzinfo=timezone.utc),
        ),
        Interaction(
            id=uuid4(),
            related_object_type="lead",
            related_object_id=lead_id,
            interaction_type="contact_research",
            channel="manual_research",
            summary="updated",
            interaction_date=datetime(2026, 5, 23, 13, 0, tzinfo=timezone.utc),
        ),
        Interaction(
            id=uuid4(),
            related_object_type="lead",
            related_object_id=lead_id,
            interaction_type="follow_up_scheduled",
            channel="internal",
            summary="manually_scheduled=true",
            interaction_date=datetime(2026, 5, 23, 14, 0, tzinfo=timezone.utc),
        ),
    ]
    mock_fu.return_value = [
        {
            "lead_id": str(lead_id),
            "company_name": "Acme",
            "lead_score": 80,
            "segments": ["lift_system_signal"],
            "due_status": "due_soon",
            "next_action": "Follow up",
            "waiting_reply": False,
        }
    ]
    mock_comp.return_value = [{"lead_id": str(lead_id), "status": "ready_for_outreach", "missing_fields": []}]

    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.a_domain.daily_work_summary.summarize_follow_up_queue", return_value={"overdue": 0, "due_today": 0, "due_soon": 1}):
        with patch("app.services.a_domain.daily_work_summary.summarize_completeness", return_value={"needs_contact_research": 2}):
            raw = build_daily_work_summary(db, target_date=date(2026, 5, 23))

    assert raw["summary"]["manual_outreach_sent"] == 1
    assert raw["summary"]["contact_research_updates"] == 1
    assert raw["summary"]["follow_ups_scheduled"] == 1
    assert raw["summary"]["leads_touched"] == 1
    assert raw["summary"]["drafts_generated"] is None
    assert raw["copyable_summary"]
    assert "secret" not in raw["copyable_summary"].lower()


@patch("app.services.a_domain.daily_work_summary._interactions_on_date", return_value=[])
@patch("app.services.a_domain.daily_work_summary.build_lead_completeness_rows", return_value=[])
@patch("app.services.a_domain.daily_work_summary.build_follow_up_queue_rows", return_value=[])
def test_empty_day_zeros(mock_fu, mock_comp, mock_ix):
    db = MagicMock()
    with patch("app.services.a_domain.daily_work_summary.summarize_follow_up_queue", return_value={"overdue": 0, "due_today": 0, "due_soon": 0}):
        with patch("app.services.a_domain.daily_work_summary.summarize_completeness", return_value={"needs_contact_research": 0}):
            raw = build_daily_work_summary(db, target_date=date(2026, 5, 23))
    assert raw["summary"]["manual_outreach_sent"] == 0
    assert raw["highlights"] == []
