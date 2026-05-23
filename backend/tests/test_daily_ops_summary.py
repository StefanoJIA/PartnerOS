"""Tests for daily ops summary service (D5.8 / D5.9)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models import Company, Interaction, Lead
from app.services.a_domain.daily_ops_summary import (
    SAFETY,
    _activity_badge,
    _build_recent_activity,
    _build_today_focus,
    _focus_priority_and_reason,
    _mask_summary,
    build_daily_ops_summary,
    build_daily_ops_summary_degraded,
)


def test_focus_priority_overdue_before_due_today():
    fu_overdue = {"due_status": "overdue", "segments": [], "lead_score": 50}
    fu_today = {"due_status": "due_today", "segments": [], "lead_score": 90}
    p1, r1 = _focus_priority_and_reason(fu_overdue, None)
    p2, r2 = _focus_priority_and_reason(fu_today, None)
    assert p1 < p2
    assert r1 == "Overdue follow-up"
    assert r2 == "Due today"


def test_today_focus_sorts_overdue_first():
    fu_rows = [
        {
            "lead_id": "a",
            "company_name": "Later Co",
            "lead_score": 90,
            "segments": [],
            "due_status": "due_soon",
            "next_action": "Follow up",
        },
        {
            "lead_id": "b",
            "company_name": "Urgent Co",
            "lead_score": 40,
            "segments": [],
            "due_status": "overdue",
            "next_action": "Call back",
        },
    ]
    focus = _build_today_focus(fu_rows, {})
    assert focus[0]["lead_id"] == "b"
    assert focus[0]["reason"] == "Overdue follow-up"


def test_safety_flags_false():
    assert SAFETY["automatic_sending_enabled"] is False
    assert SAFETY["linkedin_automation_enabled"] is False
    assert SAFETY["outlook_integration_enabled"] is False


def test_degraded_returns_zero_counts():
    raw = build_daily_ops_summary_degraded("DB down")
    assert raw["degraded"] is True
    assert raw["summary"]["overdue"] == 0
    assert raw["today_focus"] == []
    assert raw["recent_activity"] == []
    assert raw["recent_manual_outreach"] == []
    assert raw["recent_contact_research"] == []
    assert "DB down" in raw["warnings"][0]


def test_mask_summary_redacts_email():
    assert _mask_summary("Contact user@example.com today") == "Contact [email] today"


def test_activity_badge_manual_sent():
    ix = Interaction(
        id=uuid4(),
        related_object_type="lead",
        related_object_id=uuid4(),
        interaction_type="email_intro",
        channel="email",
        summary="[manually_sent=true]",
        interaction_date=datetime.now(timezone.utc),
    )
    badge, manual, research = _activity_badge(ix)
    assert badge == "Manual sent"
    assert manual is True
    assert research is False


def test_activity_badge_contact_research():
    ix = Interaction(
        id=uuid4(),
        related_object_type="lead",
        related_object_id=uuid4(),
        interaction_type="contact_research",
        channel="manual_research",
        summary="Updated contact",
        interaction_date=datetime.now(timezone.utc),
    )
    badge, manual, research = _activity_badge(ix)
    assert badge == "Contact research"
    assert manual is False
    assert research is True


@patch("app.services.a_domain.daily_ops_summary._build_recent_activity")
@patch("app.services.a_domain.daily_ops_summary.build_lead_completeness_rows")
@patch("app.services.a_domain.daily_ops_summary.build_follow_up_queue_rows")
def test_build_daily_ops_summary_counts(mock_fu, mock_comp, mock_activity):
    mock_fu.return_value = [
        {
            "lead_id": "1",
            "company_name": "A",
            "lead_score": 80,
            "segments": ["lift_system_signal"],
            "due_status": "overdue",
            "next_action": "Follow up",
            "waiting_reply": False,
        },
        {
            "lead_id": "2",
            "company_name": "B",
            "lead_score": 60,
            "segments": [],
            "due_status": "due_today",
            "next_action": "Email",
            "waiting_reply": True,
        },
    ]
    mock_comp.return_value = [
        {
            "lead_id": "1",
            "status": "needs_contact_research",
            "missing_fields": ["enrichment"],
        },
        {
            "lead_id": "2",
            "status": "ready_for_outreach",
            "missing_fields": [],
        },
    ]
    mock_activity.return_value = {
        "recent_activity": [{"lead_id": "1", "badge": "Manual sent", "is_manual_send": True}],
        "recent_manual_outreach": [{"lead_id": "1", "badge": "Manual sent", "is_manual_send": True}],
        "recent_contact_research": [],
        "recent_outreach": [{"lead_id": "1", "badge": "Manual sent"}],
    }
    db = MagicMock()
    raw = build_daily_ops_summary(db)
    assert raw["summary"]["overdue"] == 1
    assert raw["summary"]["due_today"] == 1
    assert len(raw["recent_activity"]) == 1
    assert len(raw["recent_manual_outreach"]) == 1
    assert raw["degraded"] is False


def test_empty_data_zero_counts():
    db = MagicMock()
    with patch("app.services.a_domain.daily_ops_summary.build_follow_up_queue_rows", return_value=[]):
        with patch("app.services.a_domain.daily_ops_summary.build_lead_completeness_rows", return_value=[]):
            with patch(
                "app.services.a_domain.daily_ops_summary._fetch_recent_lead_interactions",
                return_value=[],
            ):
                raw = build_daily_ops_summary(db)
    assert raw["summary"]["total_leads"] == 0
    assert raw["today_focus"] == []
    assert raw["recent_activity"] == []
    assert raw["recent_manual_outreach"] == []
    assert raw["recent_contact_research"] == []


def test_recent_activity_filters_manual_and_research():
    lead_id = uuid4()
    manual_ix = Interaction(
        id=uuid4(),
        related_object_type="lead",
        related_object_id=lead_id,
        interaction_type="email_intro",
        channel="email",
        summary="[manually_sent=true] channel=email",
        interaction_date=datetime(2026, 5, 22, tzinfo=timezone.utc),
    )
    research_ix = Interaction(
        id=uuid4(),
        related_object_type="lead",
        related_object_id=lead_id,
        interaction_type="contact_research",
        channel="manual_research",
        summary="manually_researched=true",
        interaction_date=datetime(2026, 5, 21, tzinfo=timezone.utc),
    )
    db = MagicMock()

    def query(model):
        q = MagicMock()
        if model is Interaction:
            q.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
                manual_ix,
                research_ix,
            ]
        elif model is Lead:
            q.filter.return_value.all.return_value = []
        elif model is Company:
            q.filter.return_value.all.return_value = []
        return q

    db.query.side_effect = query
    result = _build_recent_activity(db)
    assert len(result["recent_manual_outreach"]) == 1
    assert result["recent_manual_outreach"][0]["is_manual_send"] is True
    assert len(result["recent_contact_research"]) == 1
    assert result["recent_contact_research"][0]["is_contact_research"] is True
    assert "secret" not in str(result).lower()
