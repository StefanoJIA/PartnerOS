"""Tests for daily ops summary service (D5.8)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.a_domain.daily_ops_summary import (
    SAFETY,
    _build_today_focus,
    _focus_priority_and_reason,
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
    assert "DB down" in raw["warnings"][0]


@patch("app.services.a_domain.daily_ops_summary._recent_manual_outreach", return_value=[])
@patch("app.services.a_domain.daily_ops_summary.build_lead_completeness_rows")
@patch("app.services.a_domain.daily_ops_summary.build_follow_up_queue_rows")
def test_build_daily_ops_summary_counts(mock_fu, mock_comp, _mock_recent):
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
    db = MagicMock()
    raw = build_daily_ops_summary(db)
    assert raw["summary"]["overdue"] == 1
    assert raw["summary"]["due_today"] == 1
    assert raw["summary"]["high_priority"] == 1
    assert raw["summary"]["needs_contact_research"] == 1
    assert raw["summary"]["ready_for_outreach"] == 1
    assert raw["summary"]["waiting_reply"] == 1
    assert raw["summary"]["needs_enrichment"] == 1
    assert len(raw["today_focus"]) <= 10
    assert raw["degraded"] is False


def test_empty_data_zero_counts():
    db = MagicMock()
    with patch("app.services.a_domain.daily_ops_summary.build_follow_up_queue_rows", return_value=[]):
        with patch("app.services.a_domain.daily_ops_summary.build_lead_completeness_rows", return_value=[]):
            with patch("app.services.a_domain.daily_ops_summary._recent_manual_outreach", return_value=[]):
                raw = build_daily_ops_summary(db)
    assert raw["summary"]["total_leads"] == 0
    assert raw["today_focus"] == []
