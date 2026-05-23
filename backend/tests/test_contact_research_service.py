"""Tests for contact research service (D5.5)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

from app.models import Company, Contact, Interaction, Lead, User
from app.services.a_domain.contact_research_service import (
    _non_empty,
    _patch_company_fields,
    _update_contact_fields,
    apply_contact_research,
)
from app.services.a_domain.lead_completeness import LeadCompletenessInput, compute_lead_completeness


def test_non_empty_strips_blank():
    assert _non_empty("  ") is None
    assert _non_empty("hello") == "hello"


def test_patch_company_website_fills_empty():
    company = Company(company_name="Acme", company_type="Office Furniture Dealer")
    diff = _patch_company_fields(company, {"website": "https://acme.example"})
    assert company.website == "https://acme.example"
    assert diff["website"] == "https://acme.example"


def test_patch_company_does_not_overwrite_website_with_blank():
    company = Company(
        company_name="Acme",
        company_type="Office Furniture Dealer",
        website="https://existing.example",
    )
    diff = _patch_company_fields(company, {"website": ""})
    assert company.website == "https://existing.example"
    assert not diff


def test_patch_company_notes_appends():
    company = Company(company_name="Acme", company_type="Dealer", notes="Old note")
    _patch_company_fields(company, {"notes": "Found buyer email"})
    assert "Old note" in company.notes
    assert f"[Contact Research {date.today().isoformat()}]" in company.notes
    assert "Found buyer email" in company.notes


def test_update_contact_fields_sets_explicit_values():
    contact = Contact(
        first_name="Old",
        last_name="Name",
        company_id=uuid4(),
        email="old@example.com",
    )
    diff = _update_contact_fields(
        contact,
        {"name": "Sam Lee", "email": "sam@example.com", "linkedin_url": "https://linkedin.com/in/sam"},
    )
    assert contact.first_name == "Sam"
    assert contact.last_name == "Lee"
    assert contact.email == "sam@example.com"
    assert contact.linkedin_url == "https://linkedin.com/in/sam"
    assert "email" in diff


def test_completeness_score_increases_after_contact_update():
    before = compute_lead_completeness(
        LeadCompletenessInput(
            company_name="Transfer Enterprises",
            company_type="Dealer",
            website="https://transfer.example",
            contact_name="Unknown",
            segments=["general_office_furniture_only"],
            intelligence_score=45,
            next_action="Research contact",
            enrichment_status="No runs",
            touch_count=0,
        )
    )
    after = compute_lead_completeness(
        LeadCompletenessInput(
            company_name="Transfer Enterprises",
            company_type="Dealer",
            website="https://transfer.example",
            contact_name="Jordan Smith",
            contact_email="jordan@transfer.example",
            segments=["general_office_furniture_only"],
            intelligence_score=45,
            next_action="Research contact",
            enrichment_status="No runs",
            touch_count=1,
        )
    )
    assert after["score"] > before["score"]
    assert "contact_email_or_linkedin" not in after["missing_fields"]


def _mock_db_for_contact_research(
    *,
    lead: Lead,
    company: Company,
    contact: Contact | None,
    company_contacts: list[Contact] | None = None,
) -> MagicMock:
    db = MagicMock()
    contacts = company_contacts or ([] if contact is None else [contact])

    def query(model):
        q = MagicMock()
        if model is Lead:
            q.filter.return_value.first.return_value = lead
        elif model is Company:
            q.filter.return_value.first.return_value = company
        elif model is Contact:
            filt = q.filter.return_value

            def first_side_effect():
                # primary contact lookup by id uses filter(Contact.id == ...)
                return contact

            filt.first.side_effect = first_side_effect

            def all_side_effect():
                return contacts

            filt.all.side_effect = all_side_effect
        elif model is Interaction:
            q.filter.return_value.count.return_value = 0
            q.filter.return_value.order_by.return_value.first.return_value = None
        return q

    db.query.side_effect = query
    return db


def test_apply_contact_research_writes_touchpoint(monkeypatch):
    user = User(id=uuid4(), email="cr@test.example", is_active=True)
    company = Company(id=uuid4(), company_name="Gap Co", company_type="Dealer")
    lead = Lead(id=uuid4(), company_id=company.id, lead_name="Lead — Gap Co", is_active=True)
    db = _mock_db_for_contact_research(lead=lead, company=company, contact=None)

    monkeypatch.setattr(
        "app.services.a_domain.contact_research_service._patch_company_fields",
        lambda c, d: {},
    )
    monkeypatch.setattr(
        "app.services.a_domain.contact_research_service._resolve_or_create_contact",
        lambda *args, **kwargs: (None, False, {}),
    )
    monkeypatch.setattr(
        "app.services.a_domain.contact_research_service.build_lead_completeness_row_for_lead",
        lambda db, lid: {
            "lead_id": str(lid),
            "company_name": company.company_name,
            "lead_name": lead.lead_name,
            "score": 70,
            "status": "ready_for_outreach",
            "status_label": "Ready for Outreach",
            "missing_fields": [],
            "recommended_research_action": "Generate draft",
            "segments": [],
            "last_touchpoint": "Contact research",
        },
    )

    added: list = []

    def add_side_effect(obj):
        added.append(obj)
        if isinstance(obj, Interaction):
            obj.id = uuid4()

    db.add.side_effect = add_side_effect

    result = apply_contact_research(
        db,
        user,
        lead.id,
        company_data={"website": "https://gap.example"},
        contact_data={"name": "Alex Buyer", "email": "alex@gap.example"},
        lead_data={"next_action": "Send intro email"},
        touchpoint_note="Manual lookup",
    )

    interactions = [o for o in added if isinstance(o, Interaction)]
    assert interactions
    assert interactions[0].interaction_type == "contact_research"
    assert interactions[0].channel == "manual_research"
    assert "manually_researched=true" in (interactions[0].summary or "")
    assert lead.next_action == "Send intro email"
    assert result["interaction_id"]
    assert result["completeness"]["score"] == 70


def test_apply_no_automatic_send_side_effects(monkeypatch):
    """Contact research must not set outreach-sent flags."""
    user = User(id=uuid4(), email="cr2@test.example", is_active=True)
    company = Company(id=uuid4(), company_name="Safe Co", company_type="Dealer")
    lead = Lead(
        id=uuid4(),
        company_id=company.id,
        lead_name="Lead — Safe Co",
        is_active=True,
        next_action=None,
    )
    db = _mock_db_for_contact_research(lead=lead, company=company, contact=None)
    monkeypatch.setattr(
        "app.services.a_domain.contact_research_service._patch_company_fields",
        lambda c, d: {},
    )
    monkeypatch.setattr(
        "app.services.a_domain.contact_research_service._resolve_or_create_contact",
        lambda *args, **kwargs: (None, False, {}),
    )
    monkeypatch.setattr(
        "app.services.a_domain.contact_research_service.build_lead_completeness_row_for_lead",
        lambda db, lid: {
            "lead_id": str(lid),
            "company_name": "Safe Co",
            "lead_name": "L",
            "score": 50,
            "status": "incomplete",
            "status_label": "Incomplete",
            "missing_fields": [],
            "recommended_research_action": "—",
            "segments": [],
            "last_touchpoint": "—",
        },
    )

    apply_contact_research(
        db,
        user,
        lead.id,
        company_data={},
        contact_data={"email": "only@example.com", "name": "Only Email"},
        lead_data={},
        touchpoint_note=None,
    )

    assert getattr(lead, "outreach_sent", None) is None
