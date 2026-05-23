"""Tests for soft quote handoff brief (D5.18)."""

from __future__ import annotations

from app.services.a_domain.product_fit import (
    PRODUCT_FOCUS_EDUCATION,
    PRODUCT_FOCUS_FRAMES,
    PRODUCT_FOCUS_HOSUN,
    PRODUCT_FOCUS_OEM,
    PRODUCT_FOCUS_PROJECT,
)
from app.services.a_domain.quote_handoff import (
    FORBIDDEN_HANDOFF_PHRASES,
    QuoteHandoffInput,
    assert_no_forbidden_handoff_phrases,
    build_quote_handoff_brief,
)


def _inp(**kwargs) -> QuoteHandoffInput:
    defaults = dict(
        lead_id="lead-1",
        company_name="SWC Office Furniture",
        company_type="Office Furniture Dealer",
        quote_readiness="almost_ready",
        sample_readiness="needs_specs",
        opportunity_score=72,
        opportunity_level="promising",
        project_type="dealer_supply",
        recommended_product_focus=[PRODUCT_FOCUS_HOSUN, PRODUCT_FOCUS_FRAMES],
        missing_quote_info=["quantity_or_volume", "project_timeline", "delivery_location"],
        recommended_discovery_questions=[
            "Are you looking for complete adjustable desk frames, desk legs, or lifting columns?"
        ],
        has_contact_method=True,
        notes_blob="adjustable desk frames dealer supply quote discussion",
    )
    defaults.update(kwargs)
    return QuoteHandoffInput(**defaults)


def test_lifting_lead_returns_hosun_route():
    result = build_quote_handoff_brief(_inp())
    assert "hosun_lifting_systems" in result["recommended_partner_route"]
    assert PRODUCT_FOCUS_FRAMES in result["recommended_product_scope"]


def test_education_lead_returns_jooboo_route():
    result = build_quote_handoff_brief(
        _inp(
            company_name="Campus Learning Co",
            company_type="Education Furniture Company",
            recommended_product_focus=[PRODUCT_FOCUS_EDUCATION],
            project_type="education_project",
            notes_blob="school district classroom furniture procurement RFP",
        )
    )
    assert "jooboo_education_furniture" in result["recommended_partner_route"]


def test_project_lead_returns_project_route():
    result = build_quote_handoff_brief(
        _inp(
            recommended_product_focus=[PRODUCT_FOCUS_PROJECT, PRODUCT_FOCUS_HOSUN],
            project_type="project_based",
            notes_blob="FF&E office buildout project procurement",
        )
    )
    assert "project_supply" in result["recommended_partner_route"]


def test_oem_lead_returns_oem_route():
    result = build_quote_handoff_brief(
        _inp(
            recommended_product_focus=[PRODUCT_FOCUS_OEM, PRODUCT_FOCUS_HOSUN],
            project_type="oem_odm",
            notes_blob="OEM private label lifting columns",
        )
    )
    assert "oem_odm_components" in result["recommended_partner_route"]


def test_ready_status_when_quote_ready_and_few_missing():
    result = build_quote_handoff_brief(
        _inp(
            quote_readiness="ready",
            missing_quote_info=["delivery_location"],
            notes_blob="quote for 500 adjustable desk frames project timeline Q3",
        )
    )
    assert result["handoff_status"] == "ready_for_manual_quote_prep"


def test_needs_clarification_when_almost_ready():
    result = build_quote_handoff_brief(_inp(quote_readiness="almost_ready"))
    assert result["handoff_status"] == "needs_customer_clarification"


def test_not_ready_without_contact():
    result = build_quote_handoff_brief(
        _inp(has_contact_method=False, quote_readiness="not_ready", recommended_product_focus=[])
    )
    assert result["handoff_status"] == "not_ready"


def test_missing_customer_info_max_six():
    result = build_quote_handoff_brief(
        _inp(
            missing_quote_info=[
                "quantity_or_volume",
                "project_timeline",
                "delivery_location",
                "product_type",
                "load_capacity_requirement",
                "color_or_finish",
                "decision_maker_role",
            ]
        )
    )
    assert len(result["missing_customer_info"]) <= 6


def test_known_context_does_not_invent_quantity():
    result = build_quote_handoff_brief(_inp())
    blob = " ".join(result["known_context"]).lower()
    assert "confirmed budget" not in blob
    assert "confirmed quantity" not in blob


def test_supplier_notes_no_price_promises():
    result = build_quote_handoff_brief(_inp())
    blob = " ".join(result["supplier_preparation_notes"]).lower()
    for phrase in FORBIDDEN_HANDOFF_PHRASES:
        assert phrase not in blob


def test_safety_flags_false():
    result = build_quote_handoff_brief(_inp())
    safety = result["safety"]
    assert safety["quote_created"] is False
    assert safety["pricing_generated"] is False
    assert safety["automatic_sending_enabled"] is False


def test_brief_text_no_forbidden_promises():
    result = build_quote_handoff_brief(_inp())
    assert_no_forbidden_handoff_phrases(result["quote_handoff_brief_text"])


def test_customer_questions_max_five():
    result = build_quote_handoff_brief(_inp())
    assert len(result["customer_clarification_questions"]) <= 5


def test_empty_data_safe():
    result = build_quote_handoff_brief(QuoteHandoffInput())
    assert result["handoff_status"] == "not_ready"
    assert result["safety"]["quote_created"] is False
    assert result["quote_handoff_brief_text"]
