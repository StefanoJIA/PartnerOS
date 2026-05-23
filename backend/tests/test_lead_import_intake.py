"""Tests for lead CSV intake preview (D5.2.4)."""

from __future__ import annotations

from app.services.a_domain.lead_import_intake import preview_row, split_contact_name


def test_preview_lift_segment_from_notes():
    row = {
        "company_name": "Test Dealer",
        "notes": "height-adjustable desk frames and lifting columns",
        "company_type": "Office Furniture Dealer",
        "website": "https://example.com",
        "contact_name": "Alex Test",
        "contact_email": "a@test.com",
        "priority": "High",
    }
    p = preview_row(row)
    assert "lift_system_signal" in p.likely_segments
    assert p.status == "OK"
    assert p.priority_hint == "high"


def test_preview_warns_missing_website_and_notes():
    row = {
        "company_name": "Unknown Office Buyer",
        "company_type": "Office Furniture Dealer",
    }
    p = preview_row(row)
    assert p.status == "WARN"
    assert "website or notes" in p.missing_fields


def test_split_contact_name():
    assert split_contact_name("Alex Rivera") == ("Alex", "Rivera")
    assert split_contact_name("Madonna")[0] == "Madonna"
