"""Pure-function tests for A-domain lead intelligence scoring (D5 / D5.1)."""

from __future__ import annotations

from app.services.a_domain.intelligence_score import (
    IntelligenceScoreInput,
    compute_intelligence_score,
    infer_market_fit_segments,
)


def test_empty_input_low_score_suggests_contact_and_intel():
    r = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=False,
            market_intel_count=0,
            product_interest_tags=None,
            business_description=None,
            lead_product_interest=None,
            lead_priority=None,
            company_strategic_level=None,
        )
    )
    assert 0 <= r.score <= 100
    assert r.breakdown.get("primary_contact", 0) == 0
    assert r.market_fit_segments == []
    assert any("主联系人" in s for s in r.suggestions)
    assert any("市场情报" in s for s in r.suggestions)


def test_ergonomic_keywords_boost_score():
    sparse = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=True,
            market_intel_count=1,
            product_interest_tags="furniture",
            business_description="general importer",
            lead_product_interest="tables",
            lead_priority="medium",
            company_strategic_level=None,
        )
    )
    rich = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=True,
            market_intel_count=1,
            product_interest_tags="standing desk, height adjustable",
            business_description="electric desk frame distributor",
            lead_product_interest="lifting columns",
            lead_priority="medium",
            company_strategic_level=None,
        )
    )
    assert rich.score > sparse.score
    assert rich.breakdown["ergonomic_market_fit"] >= 8
    assert "lift_system_signal" in rich.market_fit_segments


def test_strategic_tier1_not_confused_with_tier3():
    r1 = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=False,
            market_intel_count=0,
            product_interest_tags=None,
            business_description=None,
            lead_product_interest=None,
            lead_priority="low",
            company_strategic_level="Tier 3 exploratory",
        )
    )
    r2 = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=False,
            market_intel_count=0,
            product_interest_tags=None,
            business_description=None,
            lead_product_interest=None,
            lead_priority="low",
            company_strategic_level="Tier 1 strategic",
        )
    )
    assert r2.breakdown["strategic_level"] > r1.breakdown["strategic_level"]


def test_segments_oem_odm_with_lift_context():
    blob = "odm lifting solution for height adjustable desk frames"
    assert "oem_odm_fit" in infer_market_fit_segments(blob)
    assert "lift_system_signal" in infer_market_fit_segments(blob)


def test_segments_medical_vertical():
    blob = "medical workstation distributor europe"
    segs = infer_market_fit_segments(blob)
    assert "medical_vertical" in segs
    assert "lift_system_signal" in segs
    assert "general_office_furniture_only" not in segs


def test_d51_general_office_only_no_lift():
    """5.1 — broad office furniture words only."""
    blob = "office furniture and contract furniture wholesaler"
    segs = infer_market_fit_segments(blob)
    assert "general_office_furniture_only" in segs
    assert "lift_system_signal" not in segs


def test_d51_office_furniture_plus_height_desk_no_general():
    """5.2 — lift signal wins; mutually exclusive with general_office_furniture_only."""
    blob = "office furniture dealer height adjustable desk programs"
    segs = infer_market_fit_segments(blob)
    assert "lift_system_signal" in segs
    assert "general_office_furniture_only" not in segs


def test_d51_contract_furniture_plus_lifting_column():
    """5.3"""
    blob = "contract furniture importer lifting column sourcing"
    segs = infer_market_fit_segments(blob)
    assert "lift_system_signal" in segs
    assert "general_office_furniture_only" not in segs


def test_d51_oem_word_alone_no_oem_segment():
    """5.4 — bare oem without frame/lift/desk/etc. context."""
    blob = "office furniture regional distributor oem brands portfolio"
    segs = infer_market_fit_segments(blob)
    assert "oem_odm_fit" not in segs
    assert "general_office_furniture_only" in segs


def test_d51_general_office_does_not_change_numeric_score():
    base = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=True,
            market_intel_count=0,
            product_interest_tags=None,
            business_description="tables and chairs",
            lead_product_interest=None,
            lead_priority="medium",
            company_strategic_level=None,
        )
    )
    with_weak = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=True,
            market_intel_count=0,
            product_interest_tags="contract furniture",
            business_description="tables and chairs",
            lead_product_interest=None,
            lead_priority="medium",
            company_strategic_level=None,
        )
    )
    assert "general_office_furniture_only" in with_weak.market_fit_segments
    assert with_weak.score == base.score


def test_d51_suggestion_includes_general_office_guidance():
    r = compute_intelligence_score(
        IntelligenceScoreInput(
            has_primary_contact=True,
            market_intel_count=0,
            product_interest_tags="commercial furniture",
            business_description="dealer",
            lead_product_interest=None,
            lead_priority="low",
            company_strategic_level=None,
        )
    )
    assert "general_office_furniture_only" in r.market_fit_segments
    assert any("一般办公家具相关" in s for s in r.suggestions)


def test_d521_healthcare_lab_medical_vertical():
    """D5.2.1 — UAT Healthcare Lab Workspace signals."""
    blob = (
        "medical furniture and lab bench provider with medical-grade precision. "
        "healthcare workstation hospital furniture"
    )
    segs = infer_market_fit_segments(blob)
    assert "medical_vertical" in segs
    assert "general_office_furniture_only" not in segs


def test_d521_contract_project_segment():
    """D5.2.1 — UAT Contract Project Interiors signals."""
    blob = (
        "project furniture contractor for commercial interiors and installation. "
        "workplace project FF&E procurement"
    )
    segs = infer_market_fit_segments(blob)
    assert "project_based_furniture" in segs
    assert "general_office_furniture_only" not in segs


def test_d521_plain_office_dealer_unchanged():
    """Office dealer without medical/project cues stays general-only."""
    blob = "office furniture dealer commercial furniture workplace furniture"
    segs = infer_market_fit_segments(blob)
    assert "general_office_furniture_only" in segs
    assert "medical_vertical" not in segs
    assert "project_based_furniture" not in segs
