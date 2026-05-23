"""Tests for D5.2.7 follow-up rhythm classification."""

from __future__ import annotations

from app.services.a_domain.follow_up_rhythm import (
    NO_NEXT_ACTION,
    RhythmLead,
    classify_follow_up_categories,
    primary_status_badge,
    recommend_top_actions,
    summarize_counts,
)


def _lead(**overrides) -> RhythmLead:
    base = {
        "company_name": "Test Co",
        "score": 50,
        "segments": ["general_office_furniture_only"],
        "next_action": NO_NEXT_ACTION,
        "touch_count": 0,
        "last_touch": "—",
        "last_touch_date": None,
        "contact_email": "a@test.com",
        "linkedin_url": None,
        "enrichment_status": "No runs",
        "company_website": None,
    }
    base.update(overrides)
    return RhythmLead(**base)


def test_needs_first_outreach():
    cats = classify_follow_up_categories(_lead(touch_count=0, segments=["lift_system_signal"]))
    assert "needs_first_outreach" in cats


def test_waiting_for_reply_from_manual_sent():
    cats = classify_follow_up_categories(
        _lead(
            touch_count=1,
            last_touch="[manually_sent=true] channel=email_intro",
            next_action="Wait for reply — follow up in 5 days",
        )
    )
    assert "waiting_for_reply" in cats


def test_needs_contact_research_no_channels():
    cats = classify_follow_up_categories(_lead(contact_email=None, linkedin_url=None))
    assert "needs_contact_research" in cats


def test_high_priority_score():
    cats = classify_follow_up_categories(_lead(score=75))
    assert "high_priority" in cats


def test_primary_badge_prefers_high_priority():
    cats = ["needs_first_outreach", "high_priority"]
    assert primary_status_badge(cats) == "high_priority"


def test_summarize_counts():
    leads = [
        _lead(company_name="A", segments=["lift_system_signal"]),
        _lead(
            company_name="B",
            touch_count=1,
            last_touch="[manually_sent=true]",
            next_action="Wait for reply",
        ),
    ]
    counts = summarize_counts(leads)
    assert counts["total"] == 2
    assert counts["needs_first_outreach"] >= 1


def test_recommend_top_actions():
    leads = [
        _lead(company_name="Low", score=30),
        _lead(company_name="High", score=80, segments=["project_based_furniture"]),
    ]
    for ld in leads:
        ld.categories = classify_follow_up_categories(ld)
    top = recommend_top_actions(leads, limit=2)
    assert top[0][0] == "High"
