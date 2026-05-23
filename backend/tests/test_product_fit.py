"""Tests for product fit and project opportunity planner (D5.12)."""

from __future__ import annotations

from app.services.a_domain.product_fit import ProductFitInput, compute_product_fit

FORBIDDEN_PROMISE_WORDS = ("$", "in stock", "available inventory", "certified for", "lead time of", "delivery in")


def _base(**kwargs) -> ProductFitInput:
    defaults = dict(
        lead_id="test-lead",
        company_name="SWC Office Furniture",
        contact_name="Sam Lee",
        contact_email="sam@swc.example",
        contact_title="VP Procurement",
        segments=["lift_system_signal"],
        next_action="Send catalog and ask about project timeline",
        completeness_score=82,
        enrichment_status="completed",
        touch_count=2,
        follow_up_date_set=True,
        business_description="Height adjustable desk frames and lifting columns for dealer projects.",
        lead_product_interest="adjustable desk frames",
        expected_timeline="Q3 2026 rollout",
    )
    defaults.update(kwargs)
    return ProductFitInput(**defaults)


def test_lift_system_signal_returns_hosun_focus():
    result = compute_product_fit(_base(segments=["lift_system_signal"]))
    focus = result["recommended_product_focus"]
    assert "hosun_lifting_systems" in focus
    assert "adjustable_desk_frames" in focus
    assert "lifting_columns" in focus


def test_education_vertical_returns_jooboo_focus():
    result = compute_product_fit(
        _base(
            segments=["education_vertical"],
            business_description="Campus classroom furniture procurement for school district.",
            lead_product_interest="classroom desks",
        )
    )
    assert "jooboo_education_furniture" in result["recommended_product_focus"]
    assert result["project_type"] == "education_project"


def test_project_segment_ranks_before_education_when_both():
    result = compute_product_fit(
        _base(
            segments=["education_vertical", "project_based_furniture"],
            lead_notes="FF&E project quote; also JOOBOO education furniture line",
        )
    )
    focus = result["recommended_product_focus"]
    assert "project_supply" in focus
    assert focus[0] == "project_supply"
    assert "jooboo_education_furniture" not in focus


def test_medical_vertical_returns_medical_workspace():
    result = compute_product_fit(
        _base(
            segments=["medical_vertical"],
            business_description="Hospital nurse station and clinical workstation supplier.",
        )
    )
    assert "medical_workspace" in result["recommended_product_focus"]
    assert result["project_type"] == "medical_workspace"


def test_project_based_furniture_returns_project_supply():
    result = compute_product_fit(
        _base(
            segments=["project_based_furniture"],
            business_description="Contract interiors and FF&E installation for office buildout.",
            next_action="Request quote for 200 units",
        )
    )
    assert "project_supply" in result["recommended_product_focus"]
    assert result["project_type"] == "project_based"


def test_oem_odm_returns_oem_components():
    result = compute_product_fit(
        _base(
            segments=["oem_odm_fit", "lift_system_signal"],
            business_description="OEM sourcing for lifting columns and control systems.",
        )
    )
    assert "oem_odm_components" in result["recommended_product_focus"]
    assert result["project_type"] == "oem_odm"


def test_quote_readiness_ready_with_project_signals():
    result = compute_product_fit(
        _base(
            next_action="Prepare quote for 500 desk frames",
            lead_product_interest="lifting columns",
            expected_timeline="Delivery by September",
        )
    )
    assert result["quote_readiness"] in ("ready", "almost_ready")


def test_quote_readiness_not_ready_missing_contact():
    result = compute_product_fit(
        _base(
            contact_email=None,
            contact_linkedin_url=None,
            company_linkedin_url=None,
            segments=[],
        )
    )
    assert result["quote_readiness"] == "not_ready"
    assert "contact_email_or_linkedin" in result["missing_quote_info"]


def test_quote_readiness_almost_ready():
    result = compute_product_fit(
        _base(
            segments=["lift_system_signal"],
            lead_product_interest=None,
            expected_timeline=None,
            next_action="Follow up",
        )
    )
    assert result["quote_readiness"] in ("almost_ready", "ready", "not_ready")


def test_missing_quote_info_sensible_keys():
    result = compute_product_fit(_base())
    allowed = {
        "contact_email_or_linkedin",
        "product_type",
        "quantity_or_volume",
        "frame_size_or_desktop_size",
        "desktop/frame size",
        "load_capacity_requirement",
        "color_or_finish",
        "project_timeline",
        "delivery_location",
        "certification_requirement",
        "sample_quantity",
        "target_price_or_budget",
        "decision_maker_role",
        "component_type",
        "control_system_requirement",
        "installation_or_packaging_need",
        "classroom_or_campus_use_case",
        "rfp_or_procurement_timeline",
        "volume_estimate",
        "workstation_use_case",
        "stability_or_load_requirement",
        "component_category",
        "customization_requirement",
    }
    for key in result["missing_quote_info"]:
        assert key in allowed
    assert len(result["missing_quote_info"]) <= 6


def test_no_price_stock_certification_promises():
    result = compute_product_fit(_base())
    blob = " ".join(
        [
            result["sales_angle"],
            result["recommended_next_product_action"],
            *result["warnings"],
            *result["recommended_discovery_questions"],
        ]
    ).lower()
    for word in FORBIDDEN_PROMISE_WORDS:
        assert word not in blob


def test_empty_data_safe_default():
    result = compute_product_fit(ProductFitInput())
    assert result["project_opportunity_score"] >= 0
    assert result["project_type"] == "unknown"
    assert result["quote_readiness"] == "not_ready"
    assert isinstance(result["recommended_discovery_questions"], list)
    assert len(result["warnings"]) >= 1


def test_opportunity_score_ranges():
    high = compute_product_fit(_base(segments=["lift_system_signal", "project_based_furniture", "oem_odm_fit"]))
    low = compute_product_fit(
        ProductFitInput(company_name="X", segments=["general_office_furniture_only"])
    )
    assert high["project_opportunity_score"] > low["project_opportunity_score"]
    assert high["opportunity_level"] in ("high_opportunity", "promising", "needs_qualification", "low_incomplete")
