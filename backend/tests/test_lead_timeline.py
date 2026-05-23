"""Tests for lead timeline service (D5.6)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models import Company, Interaction, Lead
from app.services.a_domain.lead_timeline import (
    build_lead_timeline,
    compute_follow_up_hint,
    _is_contact_research,
    _is_manual_send,
)


def test_timeline_empty_list_no_touchpoints(monkeypatch):
    lead_id = uuid4()
    company_id = uuid4()
    lead = Lead(id=lead_id, company_id=company_id, lead_name="L", is_active=True)
    company = Company(id=company_id, company_name="Empty Co", company_type="Dealer")

    db = MagicMock()

    def query(model):
        q = MagicMock()
        if model is Lead:
            q.filter.return_value.first.return_value = lead
        elif model is Company:
            q.filter.return_value.first.return_value = company
        elif model is Interaction:
            q.filter.return_value.order_by.return_value.all.return_value = []
        return q

    db.query.side_effect = query
    monkeypatch.setattr(
        "app.services.a_domain.lead_timeline.build_lead_completeness_row_for_lead",
        lambda db, lid: {"status": "incomplete"},
    )

    result = build_lead_timeline(db, lead_id)
    assert result["items"] == []
    assert result["stats"]["total_touchpoints"] == 0
    assert result["follow_up_hint"] == "Needs first outreach"


def test_timeline_manual_sent_item(monkeypatch):
    lead_id = uuid4()
    company_id = uuid4()
    lead = Lead(id=lead_id, company_id=company_id, lead_name="L", next_action="Wait for reply", is_active=True)
    company = Company(id=company_id, company_name="Sent Co", company_type="Dealer")
    ix = Interaction(
        id=uuid4(),
        related_object_type="lead",
        related_object_id=lead_id,
        interaction_type="catalog_sent",
        channel="email",
        subject="Manual outreach — email_intro",
        summary='[manually_sent=true] channel=email_intro; product_focus=general; draft_preview="Hello"',
        interaction_date=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )

    db = MagicMock()

    def query(model):
        q = MagicMock()
        if model is Lead:
            q.filter.return_value.first.return_value = lead
        elif model is Company:
            q.filter.return_value.first.return_value = company
        elif model is Interaction:
            q.filter.return_value.order_by.return_value.all.return_value = [ix]
        return q

    db.query.side_effect = query
    monkeypatch.setattr(
        "app.services.a_domain.lead_timeline.build_lead_completeness_row_for_lead",
        lambda db, lid: {"status": "ready_for_outreach"},
    )

    result = build_lead_timeline(db, lead_id)
    assert len(result["items"]) == 1
    assert result["items"][0]["is_manual_send"] is True
    assert result["items"][0]["title"] == "Email intro marked as sent"
    assert result["stats"]["manual_sent_count"] == 1


def test_timeline_contact_research_item(monkeypatch):
    lead_id = uuid4()
    company_id = uuid4()
    lead = Lead(id=lead_id, company_id=company_id, lead_name="L", is_active=True)
    company = Company(id=company_id, company_name="Research Co", company_type="Dealer")
    ix = Interaction(
        id=uuid4(),
        related_object_type="lead",
        related_object_id=lead_id,
        interaction_type="contact_research",
        channel="manual_research",
        summary="Updated notes [manually_researched=true]",
        interaction_date=datetime(2026, 5, 21, tzinfo=timezone.utc),
    )

    db = MagicMock()

    def query(model):
        q = MagicMock()
        if model is Lead:
            q.filter.return_value.first.return_value = lead
        elif model is Company:
            q.filter.return_value.first.return_value = company
        elif model is Interaction:
            q.filter.return_value.order_by.return_value.all.return_value = [ix]
        return q

    db.query.side_effect = query
    monkeypatch.setattr(
        "app.services.a_domain.lead_timeline.build_lead_completeness_row_for_lead",
        lambda db, lid: {"status": "needs_contact_research"},
    )

    result = build_lead_timeline(db, lead_id)
    assert result["items"][0]["is_contact_research"] is True
    assert result["items"][0]["title"] == "Contact research updated"
    assert result["stats"]["contact_research_count"] == 1
    assert result["follow_up_hint"] == "Needs contact research"


def test_timeline_stats_correct(monkeypatch):
    lead_id = uuid4()
    company_id = uuid4()
    lead = Lead(id=lead_id, company_id=company_id, lead_name="L", is_active=True)
    company = Company(id=company_id, company_name="Stats Co", company_type="Dealer")
    items = [
        Interaction(
            id=uuid4(),
            related_object_type="lead",
            related_object_id=lead_id,
            interaction_type="contact_research",
            channel="manual_research",
            summary="[manually_researched=true]",
            interaction_date=datetime(2026, 5, 22, tzinfo=timezone.utc),
        ),
        Interaction(
            id=uuid4(),
            related_object_type="lead",
            related_object_id=lead_id,
            interaction_type="catalog_sent",
            channel="email",
            summary="[manually_sent=true]",
            interaction_date=datetime(2026, 5, 21, tzinfo=timezone.utc),
        ),
    ]

    db = MagicMock()

    def query(model):
        q = MagicMock()
        if model is Lead:
            q.filter.return_value.first.return_value = lead
        elif model is Company:
            q.filter.return_value.first.return_value = company
        elif model is Interaction:
            q.filter.return_value.order_by.return_value.all.return_value = items
        return q

    db.query.side_effect = query
    monkeypatch.setattr(
        "app.services.a_domain.lead_timeline.build_lead_completeness_row_for_lead",
        lambda db, lid: {"status": "ready_for_outreach"},
    )

    result = build_lead_timeline(db, lead_id)
    assert result["stats"]["total_touchpoints"] == 2
    assert result["stats"]["manual_sent_count"] == 1
    assert result["stats"]["contact_research_count"] == 1
    assert result["stats"]["last_channel"] == "manual_research"


def test_follow_up_hint_waiting_for_reply():
    latest = Interaction(
        id=uuid4(),
        related_object_type="lead",
        related_object_id=uuid4(),
        interaction_type="catalog_sent",
        channel="email",
        summary="[manually_sent=true] channel=email",
    )
    hint = compute_follow_up_hint(
        completeness_status="ready_for_outreach",
        touch_count=1,
        latest=latest,
        next_action="Wait for reply",
    )
    assert hint == "Waiting for reply"


def test_follow_up_hint_follow_up_soon():
    hint = compute_follow_up_hint(
        completeness_status="ready_for_outreach",
        touch_count=2,
        latest=None,
        next_action="Follow up in 5 days — waiting for email reply",
    )
    assert hint == "Follow up soon"


def test_follow_up_hint_priority_needs_research():
    hint = compute_follow_up_hint(
        completeness_status="needs_contact_research",
        touch_count=0,
        latest=None,
        next_action=None,
    )
    assert hint == "Needs contact research"


def test_invalid_lead_raises():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="Lead not found"):
        build_lead_timeline(db, uuid4())


def test_manual_send_detection():
    assert _is_manual_send("[manually_sent=true] x", None) is True
    assert _is_manual_send("plain note", None) is False


def test_contact_research_detection():
    assert _is_contact_research("contact_research", "manual_research", None) is True
    assert _is_contact_research("follow_up", "phone", "x [manually_researched=true]") is True
