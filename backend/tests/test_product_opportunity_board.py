"""Tests for product opportunity board aggregation (D5.13)."""

from __future__ import annotations

from app.services.a_domain.product_fit_board import (
    PRODUCT_OPPORTUNITY_SAFETY,
    build_product_opportunity_board_degraded,
    summarize_missing_info,
    summarize_product_opportunity_board,
)


def _row(**kwargs):
    base = {
        "lead_id": "1",
        "company_name": "Demo Co",
        "project_opportunity_score": 70,
        "opportunity_level": "promising",
        "project_type": "project_based",
        "quote_readiness": "almost_ready",
        "sample_readiness": "needs_specs",
        "recommended_product_focus": ["project_supply", "hosun_lifting_systems"],
        "missing_quote_info": ["quantity_or_volume", "project_timeline"],
    }
    base.update(kwargs)
    return base


def test_summary_counts_high_opportunity():
    rows = [_row(opportunity_level="high_opportunity", project_opportunity_score=85)]
    summary = summarize_product_opportunity_board(rows)
    assert summary["high_opportunity"] == 1
    assert summary["total"] == 1


def test_summary_quote_ready_and_almost():
    rows = [
        _row(quote_readiness="ready"),
        _row(quote_readiness="almost_ready"),
    ]
    summary = summarize_product_opportunity_board(rows)
    assert summary["quote_ready"] == 1
    assert summary["almost_quote_ready"] == 1
    assert summary["almost_ready"] == 1


def test_summary_lifting_and_project_fit():
    rows = [
        _row(recommended_product_focus=["hosun_lifting_systems", "adjustable_desk_frames"]),
        _row(recommended_product_focus=["project_supply"]),
    ]
    summary = summarize_product_opportunity_board(rows)
    assert summary["lifting_system_fit"] == 1
    assert summary["project_supply_fit"] == 1


def test_summary_education_medical_oem():
    rows = [
        _row(recommended_product_focus=["jooboo_education_furniture"]),
        _row(recommended_product_focus=["medical_workspace"]),
        _row(recommended_product_focus=["oem_odm_components"]),
    ]
    summary = summarize_product_opportunity_board(rows)
    assert summary["education_fit"] == 1
    assert summary["medical_fit"] == 1
    assert summary["oem_odm_fit"] == 1
    assert summary["oem_odm_potential"] == 1


def test_missing_info_summary():
    rows = [
        _row(missing_quote_info=["quantity_or_volume", "project_timeline"]),
        _row(missing_quote_info=["quantity_or_volume", "contact_email_or_linkedin"]),
    ]
    missing = summarize_missing_info(rows)
    assert missing["quantity_or_volume"] == 2
    assert missing["project_timeline"] == 1


def test_safety_flags_false():
    assert PRODUCT_OPPORTUNITY_SAFETY["automatic_quote_creation"] is False
    assert PRODUCT_OPPORTUNITY_SAFETY["automatic_sending_enabled"] is False
    assert PRODUCT_OPPORTUNITY_SAFETY["price_promises_enabled"] is False
    assert PRODUCT_OPPORTUNITY_SAFETY["inventory_promises_enabled"] is False


def test_degraded_response_readable():
    raw = build_product_opportunity_board_degraded("DB unavailable")
    assert raw["degraded"] is True
    assert raw["rows"] == []
    assert raw["summary"]["total"] == 0
    assert "DB unavailable" in raw["warnings"][0]
    assert raw["safety"]["automatic_quote_creation"] is False


def test_empty_data_safe():
    summary = summarize_product_opportunity_board([])
    assert summary["total"] == 0
    assert summarize_missing_info([]) == {}
