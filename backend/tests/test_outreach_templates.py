"""Tests for outreach draft templates (D5.2.4)."""

from __future__ import annotations

from app.services.a_domain.outreach_templates import LINKEDIN_MAX, generate_outreach_draft


def test_linkedin_connect_under_limit():
    d = generate_outreach_draft(
        company_name="Ergo Sit Stand Workspace",
        segments=["lift_system_signal"],
        contact_name="Alex Lee",
        channel="linkedin_connect",
        product_focus="hosun_lifting",
    )
    assert d.linkedin_connect_note
    assert len(d.linkedin_connect_note) <= LINKEDIN_MAX
    assert "intelliOffice" in d.linkedin_connect_note
    assert d.suggested_touchpoint_type == "linkedin_connect_note"


def test_email_intro_medical():
    d = generate_outreach_draft(
        company_name="Healthcare Lab Workspace",
        segments=["medical_vertical"],
        channel="email_intro",
        product_focus="medical_workspace",
    )
    assert d.email_subject
    assert d.email_body
    assert "pricing" not in d.email_body.lower() or "no stock" in d.email_body.lower() or "no pricing" in d.email_body.lower()


def test_education_focus_jooboo():
    d = generate_outreach_draft(
        company_name="Campus Learning Furniture",
        segments=["education_vertical"],
        channel="email_intro",
        product_focus="jooboo_education",
    )
    assert "JOOBOO" in d.email_body or "education" in d.email_body.lower()


def test_draft_avoids_false_promise_phrases():
    d = generate_outreach_draft(
        company_name="Example Co",
        segments=["lift_system_signal"],
        channel="email_intro",
        product_focus="hosun_lifting",
    )
    blob = (d.email_body or "").lower()
    assert "guaranteed delivery" not in blob
    assert "guaranteed lowest price" not in blob
    assert "no stock or lead-time promises" in blob or "no pricing" in blob
