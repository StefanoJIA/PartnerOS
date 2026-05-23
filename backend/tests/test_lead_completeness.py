"""Tests for lead completeness scoring (D5.4)."""

from __future__ import annotations

from app.services.a_domain.lead_completeness import LeadCompletenessInput, compute_lead_completeness
from app.services.a_domain.follow_up_rhythm import NO_NEXT_ACTION


def test_complete_lead_high_score():
    inp = LeadCompletenessInput(
        company_name="Acme Co",
        company_type="Office Furniture Dealer",
        website="https://acme.example",
        contact_name="Alex Rivera",
        contact_title="VP Sales",
        contact_email="alex@acme.example",
        contact_phone="+1-555-0100",
        segments=["lift_system_signal"],
        intelligence_score=75,
        suggested_next_actions=["Send catalog"],
        next_action="Follow up in 5 days",
        enrichment_status="completed",
        touch_count=2,
    )
    result = compute_lead_completeness(inp)
    assert result["score"] >= 80
    assert result["status"] == "complete"


def test_missing_company_name_contact_low_score():
    inp = LeadCompletenessInput(
        company_name="",
        website="",
        contact_name="",
        segments=[],
        intelligence_score=0,
        next_action=NO_NEXT_ACTION,
        enrichment_status="No runs",
        touch_count=0,
    )
    result = compute_lead_completeness(inp)
    assert result["status"] == "incomplete"
    assert "website" in result["missing_fields"]
    assert "contact_name" in result["missing_fields"]


def test_needs_contact_research_missing_email():
    inp = LeadCompletenessInput(
        company_name="Transfer Enterprises",
        company_type="Office Furniture Dealer",
        website="https://transfer.example",
        contact_name="Unknown",
        contact_title="Buyer",
        segments=["general_office_furniture_only"],
        intelligence_score=45,
        suggested_next_actions=["Research contact"],
        next_action="Research contact before outreach",
        enrichment_status="No runs",
        touch_count=0,
    )
    result = compute_lead_completeness(inp)
    assert "contact_email_or_linkedin" in result["missing_fields"]
    assert result["status"] in ("needs_contact_research", "incomplete", "ready_for_outreach")
    assert "LinkedIn" in result["recommended_research_action"] or "contact" in result["recommended_research_action"].lower()


def test_ready_for_outreach_with_contact_method():
    inp = LeadCompletenessInput(
        company_name="SWC Office",
        company_type="Dealer",
        website="https://swc.example",
        contact_name="Sam Lee",
        contact_email="sam@swc.example",
        segments=["lift_system_signal"],
        intelligence_score=70,
        suggested_next_actions=["Send catalog"],
        next_action="Wait for reply",
        enrichment_status="completed",
        touch_count=1,
    )
    result = compute_lead_completeness(inp)
    assert result["score"] >= 60
    assert result["status"] in ("ready_for_outreach", "complete")
