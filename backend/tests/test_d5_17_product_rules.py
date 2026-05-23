"""D5.17 product rule tuning tests."""

from __future__ import annotations

from app.services.a_domain.outreach_templates import LINKEDIN_MAX
from app.services.a_domain.product_aware_outreach import ProductAwareDraftInput, generate_product_aware_draft
from app.services.a_domain.product_fit import ProductFitInput, compute_product_fit

FORBIDDEN = (
    "guaranteed price",
    "lowest price guaranteed",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
)


def _base(**kwargs) -> ProductFitInput:
    defaults = dict(
        lead_id="test-lead",
        company_name="Test Co",
        contact_name="Sam Lee",
        contact_email="sam@test.example",
        contact_title="VP Procurement",
        completeness_score=82,
        enrichment_status="completed",
        touch_count=2,
        follow_up_date_set=True,
    )
    defaults.update(kwargs)
    return ProductFitInput(**defaults)


def test_jefferson_project_before_jooboo_cross_sell():
    result = compute_product_fit(
        _base(
            company_name="Jefferson Group",
            company_type="Interior Design Firm",
            segments=["education_vertical", "project_based_furniture"],
            lead_notes="FF&E project quote; also JOOBOO education furniture line",
            lead_product_interest="project quote, education furniture",
        )
    )
    focus = result["recommended_product_focus"]
    assert focus[0] == "project_supply"
    assert "jooboo_education_furniture" not in focus


def test_office_dealer_jooboo_cross_sell_not_primary_education():
    result = compute_product_fit(
        _base(
            company_name="SWC Office Furniture",
            company_type="Office Furniture Dealer",
            segments=["lift_system_signal", "education_vertical", "project_based_furniture"],
            lead_notes="dealer; discussed HOSUN lifting and JOOBOO education catalog",
            business_description="Office furniture dealer supply.",
        )
    )
    assert "jooboo_education_furniture" not in result["recommended_product_focus"]
    assert "hosun_lifting_systems" in result["recommended_product_focus"]


def test_strong_school_lead_gets_jooboo_primary():
    result = compute_product_fit(
        _base(
            company_type="Education Furniture Company",
            industry="Education furniture",
            segments=["education_vertical"],
            business_description="School district classroom furniture procurement RFP.",
            lead_product_interest="classroom desks",
        )
    )
    assert "jooboo_education_furniture" in result["recommended_product_focus"]
    assert result["project_type"] == "education_project"


def test_lift_dealer_gets_hosun_and_frames():
    result = compute_product_fit(
        _base(
            segments=["lift_system_signal"],
            business_description="Height adjustable desk frames for dealer catalog.",
        )
    )
    focus = result["recommended_product_focus"]
    assert "hosun_lifting_systems" in focus
    assert "adjustable_desk_frames" in focus


def test_desk_legs_text_returns_desk_legs_focus():
    result = compute_product_fit(
        _base(
            segments=["lift_system_signal"],
            lead_product_interest="adjustable desk legs for OEM project",
        )
    )
    assert "desk_legs" in result["recommended_product_focus"]


def test_lifting_columns_text_returns_columns_focus():
    result = compute_product_fit(
        _base(
            segments=["lift_system_signal"],
            lead_product_interest="electric lifting columns",
        )
    )
    assert "lifting_columns" in result["recommended_product_focus"]


def test_oem_lifting_columns_returns_oem_focus():
    result = compute_product_fit(
        _base(
            segments=["oem_odm_fit", "lift_system_signal"],
            business_description="OEM private label lifting columns and control systems.",
        )
    )
    focus = result["recommended_product_focus"]
    assert "oem_odm_components" in focus
    assert focus.index("oem_odm_components") <= focus.index("lifting_columns") if "lifting_columns" in focus else True


def test_heavy_duty_raises_opportunity_score():
    normal = compute_product_fit(
        _base(
            segments=["lift_system_signal"],
            business_description="Adjustable desk frames.",
        )
    )
    heavy = compute_product_fit(
        _base(
            segments=["lift_system_signal", "heavy_duty_fit"],
            business_description="Heavy-duty industrial workstation lifting system 300kg load.",
        )
    )
    assert heavy["project_opportunity_score"] > normal["project_opportunity_score"]
    assert "heavy_duty_lifting_systems" in heavy["recommended_product_focus"]


def test_missing_quote_info_respects_not_ready_limit():
    result = compute_product_fit(
        ProductFitInput(
            company_name="Transfer Enterprises",
            segments=["general_office_furniture_only"],
        )
    )
    assert result["quote_readiness"] == "not_ready"
    assert len(result["missing_quote_info"]) <= 4


def test_missing_quote_info_almost_ready_limit():
    result = compute_product_fit(
        _base(
            segments=["lift_system_signal"],
            lead_product_interest=None,
            expected_timeline=None,
        )
    )
    assert result["quote_readiness"] in ("almost_ready", "not_ready")
    assert len(result["missing_quote_info"]) <= 6


def test_general_office_no_certification_requirement():
    result = compute_product_fit(
        _base(
            segments=["general_office_furniture_only"],
            business_description="Office furniture dealer.",
            lead_product_interest="office chairs and desks",
        )
    )
    assert "certification_requirement" not in result["missing_quote_info"]


def test_education_no_load_capacity_without_lifting():
    result = compute_product_fit(
        _base(
            company_type="Education Furniture Company",
            segments=["education_vertical"],
            business_description="Campus classroom furniture procurement for school district.",
            lead_product_interest="classroom tables",
        )
    )
    assert "load_capacity_requirement" not in result["missing_quote_info"]


def test_discovery_questions_max_four():
    result = compute_product_fit(
        _base(segments=["lift_system_signal", "project_based_furniture", "oem_odm_fit"])
    )
    assert len(result["recommended_discovery_questions"]) <= 4


def test_linkedin_draft_questions_max_two():
    result = generate_product_aware_draft(
        ProductAwareDraftInput(
            company_name="Ergo Co",
            channel="linkedin_followup",
            draft_purpose="product_discovery",
            recommended_product_focus=["hosun_lifting_systems", "adjustable_desk_frames"],
        )
    )
    assert len(result["questions"]) <= 2


def test_linkedin_connect_under_300_chars():
    result = generate_product_aware_draft(
        ProductAwareDraftInput(
            company_name="Ergo Co",
            contact_name="Alex Lee",
            channel="linkedin_connect",
            recommended_product_focus=["hosun_lifting_systems"],
        )
    )
    assert result["linkedin_note"]
    assert len(result["linkedin_note"]) <= LINKEDIN_MAX


def test_no_forbidden_promise_words_in_draft():
    result = generate_product_aware_draft(
        ProductAwareDraftInput(
            company_name="Ergo Co",
            channel="email_intro",
            recommended_product_focus=["hosun_lifting_systems"],
        )
    )
    blob = ((result.get("subject") or "") + (result.get("body") or "")).lower()
    for phrase in FORBIDDEN:
        assert phrase not in blob


def test_lift_dealer_can_reach_promising_or_high():
    result = compute_product_fit(
        _base(
            company_name="SWC Office Furniture",
            segments=["lift_system_signal"],
            business_description="Adjustable desk frames and lifting columns for dealer supply.",
            lead_product_interest="adjustable desk frames",
            next_action="Send catalog and ask about lifting column needs",
        )
    )
    assert result["opportunity_level"] in ("high_opportunity", "promising")
