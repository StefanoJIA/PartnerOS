"""Tests for pre-quote and sample prep brief (D5.14)."""

from __future__ import annotations

from app.services.a_domain.pre_quote_prep import (
    FORBIDDEN_BRIEF_PHRASES,
    PRE_QUOTE_SAFETY,
    PreQuotePrepInput,
    build_pre_quote_brief,
    build_pre_quote_brief_from_product_fit,
)


def _lifting_fit(**kwargs):
    base = {
        "lead_id": "lift-1",
        "company_name": "Ergo Sit Stand Workspace",
        "recommended_product_focus": ["hosun_lifting_systems", "adjustable_desk_frames"],
        "project_opportunity_score": 78,
        "opportunity_level": "promising",
        "project_type": "dealer_supply",
        "quote_readiness": "almost_ready",
        "sample_readiness": "needs_specs",
        "missing_quote_info": ["quantity_or_volume", "project_timeline"],
        "recommended_discovery_questions": [
            "Are you currently sourcing adjustable desk frames or lifting columns?"
        ],
        "recommended_next_product_action": "Ask for quantity before quote.",
        "sales_angle": "Position HOSUN lifting systems.",
    }
    base.update(kwargs)
    return base


def test_hosun_lifting_gets_lifting_checklist():
    result = build_pre_quote_brief_from_product_fit(
        _lifting_fit(),
        company_type="Office Furniture Dealer",
        business_description="Height adjustable desk frames and lifting columns.",
    )
    checklist = " ".join(result["quote_preparation_checklist"]).lower()
    assert "lifting column" in checklist or "desk legs" in checklist
    assert "load capacity" in checklist


def test_education_lead_gets_education_checklist():
    result = build_pre_quote_brief_from_product_fit(
        _lifting_fit(
            recommended_product_focus=["jooboo_education_furniture"],
            project_type="education_project",
        ),
        business_description="Campus classroom furniture procurement.",
    )
    checklist = " ".join(result["quote_preparation_checklist"]).lower()
    assert "classroom" in checklist or "campus" in checklist


def test_project_lead_gets_project_checklist():
    result = build_pre_quote_brief_from_product_fit(
        _lifting_fit(
            recommended_product_focus=["project_supply", "hosun_lifting_systems"],
            project_type="project_based",
        ),
        business_description="FF&E office buildout project.",
    )
    checklist = " ".join(result["quote_preparation_checklist"]).lower()
    assert "ff&e" in checklist or "buildout" in checklist


def test_oem_lead_gets_oem_checklist():
    result = build_pre_quote_brief_from_product_fit(
        _lifting_fit(
            recommended_product_focus=["oem_odm_components", "lifting_columns"],
            project_type="oem_odm",
        ),
    )
    checklist = " ".join(result["quote_preparation_checklist"]).lower()
    assert "private label" in checklist or "component" in checklist


def test_quote_readiness_levels():
    ready = build_pre_quote_brief(
        PreQuotePrepInput(company_name="Co", quote_readiness="ready", sample_readiness="ready")
    )
    assert ready["quote_readiness"] == "ready"
    almost = build_pre_quote_brief(
        PreQuotePrepInput(company_name="Co", quote_readiness="almost_ready", sample_readiness="needs_specs")
    )
    assert almost["sample_readiness"] == "needs_specs"


def test_sample_readiness_not_ready():
    result = build_pre_quote_brief(
        PreQuotePrepInput(company_name="Co", quote_readiness="not_ready", sample_readiness="not_ready")
    )
    assert result["sample_readiness"] == "not_ready"
    assert len(result["sample_preparation_checklist"]) >= 3


def test_brief_masks_email():
    result = build_pre_quote_brief_from_product_fit(
        _lifting_fit(),
        contact_email="buyer@secret-client.example",
        business_description="Contact buyer@secret-client.example for specs.",
    )
    assert "buyer@secret-client.example" not in result["pre_quote_brief_text"]
    assert "[contact on file]" in result["pre_quote_brief_text"]


def test_safety_flags_all_false():
    result = build_pre_quote_brief_from_product_fit(_lifting_fit())
    assert result["safety"] == PRE_QUOTE_SAFETY
    assert result["safety"]["quote_created"] is False
    assert result["safety"]["pricing_generated"] is False


def test_no_price_inventory_cert_leadtime_promises():
    result = build_pre_quote_brief_from_product_fit(_lifting_fit())
    blob = (
        result["pre_quote_brief_text"]
        + result["sample_discussion_brief_text"]
        + " ".join(result["warnings"])
    ).lower()
    for phrase in FORBIDDEN_BRIEF_PHRASES:
        assert phrase not in blob


def test_empty_data_safe():
    result = build_pre_quote_brief(PreQuotePrepInput())
    assert result["quote_readiness"] == "not_ready"
    assert result["pre_quote_brief_text"]
    assert len(result["warnings"]) >= 1
