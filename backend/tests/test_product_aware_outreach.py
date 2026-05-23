"""Tests for product-aware outreach drafts (D5.15)."""

from __future__ import annotations

from app.services.a_domain.outreach_templates import LINKEDIN_MAX
from app.services.a_domain.product_aware_outreach import (
    FORBIDDEN_PHRASES,
    ProductAwareDraftInput,
    generate_product_aware_draft,
)


def _inp(**kwargs) -> ProductAwareDraftInput:
    base = dict(
        company_name="Ergo Sit Stand Workspace",
        contact_name="Alex Lee",
        recommended_product_focus=["hosun_lifting_systems", "adjustable_desk_frames"],
        quote_readiness="almost_ready",
        sample_readiness="needs_specs",
        missing_quote_info=["quantity_or_volume", "project_timeline"],
        recommended_customer_questions=[
            "Are you currently sourcing adjustable desk frames or lifting columns?"
        ],
        recommended_next_action="Ask for quantity before quote.",
    )
    base.update(kwargs)
    return ProductAwareDraftInput(**base)


def test_lifting_lead_generates_lifting_focused_draft():
    result = generate_product_aware_draft(_inp(channel="email_intro", draft_purpose="product_discovery"))
    blob = (result["subject"] or "") + (result["body"] or "")
    assert "lifting" in blob.lower() or "adjustable desk" in blob.lower()
    assert result["subject"]


def test_project_lead_generates_project_focused_draft():
    result = generate_product_aware_draft(
        _inp(
            recommended_product_focus=["project_supply"],
            draft_purpose="project_discovery",
        )
    )
    assert "project" in (result["subject"] or "").lower()


def test_education_lead_generates_education_draft():
    result = generate_product_aware_draft(
        _inp(
            recommended_product_focus=["jooboo_education_furniture"],
            draft_purpose="product_discovery",
        )
    )
    assert "education" in (result["subject"] or "").lower()


def test_oem_lead_generates_component_draft():
    result = generate_product_aware_draft(
        _inp(
            recommended_product_focus=["oem_odm_components"],
            draft_purpose="oem_odm_discovery",
        )
    )
    blob = (result["body"] or "").lower()
    assert "component" in blob or "oem" in blob


def test_quote_readiness_includes_missing_questions():
    result = generate_product_aware_draft(
        _inp(draft_purpose="quote_readiness", channel="email_intro")
    )
    assert len(result["questions"]) >= 1
    assert "quote" in (result["subject"] or "").lower() or "scope" in (result["body"] or "").lower()


def test_sample_discussion_includes_sample_questions():
    result = generate_product_aware_draft(
        _inp(draft_purpose="sample_discussion", channel="email_intro")
    )
    assert any("sample" in q.lower() for q in result["questions"])


def test_linkedin_connect_under_300_chars():
    result = generate_product_aware_draft(_inp(channel="linkedin_connect"))
    assert result["linkedin_note"]
    assert len(result["linkedin_note"]) <= LINKEDIN_MAX


def test_email_subject_and_body_present():
    result = generate_product_aware_draft(_inp(channel="email_intro"))
    assert result["subject"]
    assert result["body"]
    assert "intelliOffice" in result["body"]


def test_no_forbidden_promise_words():
    result = generate_product_aware_draft(_inp())
    blob = (
        (result.get("subject") or "")
        + (result.get("body") or "")
        + (result.get("linkedin_note") or "")
    ).lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in blob


def test_safety_flags_false():
    result = generate_product_aware_draft(_inp())
    assert result["safety"]["quote_created"] is False
    assert result["safety"]["pricing_generated"] is False
    assert result["safety"]["automatic_sending_enabled"] is False


def test_empty_product_fit_safe_fallback():
    result = generate_product_aware_draft(ProductAwareDraftInput(company_name="Unknown Co"))
    assert result["body"] or result["linkedin_note"]
    assert result["questions"]
