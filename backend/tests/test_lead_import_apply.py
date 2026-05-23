"""Lead import apply idempotency helpers (D5.2.6 P2)."""

from __future__ import annotations

from uuid import uuid4

from app.services.a_domain.lead_import_apply import (
    build_lead_link_payload,
    match_existing_contact,
)


def test_match_existing_contact_by_email():
    company_id = str(uuid4())
    contact_id = str(uuid4())
    contacts = [
        {
            "id": contact_id,
            "company_id": company_id,
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
        }
    ]
    row = {"contact_name": "Other Name", "contact_email": "jane@example.com"}
    assert match_existing_contact(contacts, company_id, row) == contact_id


def test_match_existing_contact_by_name():
    company_id = str(uuid4())
    contact_id = str(uuid4())
    contacts = [
        {
            "id": contact_id,
            "company_id": company_id,
            "first_name": "Alex",
            "last_name": "Rivera",
            "email": None,
        }
    ]
    row = {"contact_name": "Alex Rivera", "contact_email": ""}
    assert match_existing_contact(contacts, company_id, row) == contact_id


def test_build_lead_link_payload_fills_missing_primary_contact():
    contact_id = str(uuid4())
    lead = {"id": str(uuid4()), "primary_contact_id": None, "next_action": ""}
    payload = build_lead_link_payload(lead, contact_id, "Research contact before outreach")
    assert payload == {
        "primary_contact_id": contact_id,
        "next_action": "Research contact before outreach",
    }


def test_build_lead_link_payload_does_not_overwrite_existing_contact():
    existing = str(uuid4())
    other = str(uuid4())
    lead = {"id": str(uuid4()), "primary_contact_id": existing, "next_action": "Manual follow-up"}
    assert build_lead_link_payload(lead, other, "System default") is None


def test_build_lead_link_payload_does_not_overwrite_next_action():
    contact_id = str(uuid4())
    lead = {
        "id": str(uuid4()),
        "primary_contact_id": None,
        "next_action": "Wait for reply — follow up in 5 days",
    }
    payload = build_lead_link_payload(lead, contact_id, "Research contact before outreach")
    assert payload == {"primary_contact_id": contact_id}


def test_build_lead_link_payload_noop_when_already_linked():
    contact_id = str(uuid4())
    lead = {
        "id": str(uuid4()),
        "primary_contact_id": contact_id,
        "next_action": "Wait for reply",
    }
    assert build_lead_link_payload(lead, contact_id, "Research contact") is None
