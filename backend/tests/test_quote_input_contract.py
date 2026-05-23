"""Tests for quote input contract (D5.19)."""

from __future__ import annotations

import json

import pytest

from app.services.a_domain.quote_input_contract import (
    QuoteInputContractInput,
    assert_no_forbidden_contract_phrases,
    build_quote_input_contract,
)


def _handoff(**kwargs) -> dict:
    defaults = {
        "handoff_status": "needs_customer_clarification",
        "quote_readiness": "almost_ready",
        "sample_readiness": "needs_specs",
        "recommended_partner_route": ["hosun_lifting_systems"],
        "recommended_product_scope": ["adjustable_desk_frames", "lifting_columns"],
        "known_context": ["Office furniture dealer / project-relevant lead."],
        "missing_customer_info": [
            "quantity_or_volume",
            "product_type",
            "project_timeline",
            "delivery_location",
        ],
        "customer_clarification_questions": [
            "What quantity range and timeline should we consider?",
            "What delivery location should be used for planning?",
        ],
        "supplier_preparation_notes": [
            "Prepare adjustable desk frame overview.",
            "Do not prepare formal pricing until quantity is confirmed.",
        ],
    }
    defaults.update(kwargs)
    return defaults


def _fit(**kwargs) -> dict:
    defaults = {
        "recommended_product_focus": ["adjustable_desk_frames", "lifting_systems"],
        "project_type": "dealer_project",
        "quote_readiness": "almost_ready",
        "sample_readiness": "needs_specs",
    }
    defaults.update(kwargs)
    return defaults


def _inp(**kwargs) -> QuoteInputContractInput:
    defaults = {
        "lead_id": "lead-1",
        "company_name": "SWC Office Furniture",
        "contact_name": "Alex",
        "has_contact_method": True,
        "handoff": _handoff(),
        "product_fit": _fit(),
        "notes_blob": "office furniture adjustable desk frame lifting column",
    }
    defaults.update(kwargs)
    return QuoteInputContractInput(**defaults)


def test_build_contract_structure():
    result = build_quote_input_contract(_inp())
    assert result["lead_id"] == "lead-1"
    assert result["quote_module_readiness"] in (
        "ready_for_phase2_quote_draft",
        "needs_more_customer_info",
        "not_quote_ready",
    )
    assert result["quote_input_fields"]["customer"]["company_name"] == "SWC Office Furniture"
    assert result["safety"]["quote_created"] is False
    assert result["safety"]["pricing_generated"] is False


def test_readiness_needs_more_customer_info():
    result = build_quote_input_contract(_inp())
    assert result["quote_module_readiness"] == "needs_more_customer_info"


def test_readiness_ready_for_phase2():
    result = build_quote_input_contract(
        _inp(
            handoff=_handoff(
                handoff_status="ready_for_manual_quote_prep",
                missing_customer_info=["quantity_or_volume"],
            ),
            notes_blob="adjustable desk frame 50 units ship to california",
            lead_product_interest="adjustable desk frames",
        )
    )
    assert result["quote_module_readiness"] == "ready_for_phase2_quote_draft"


def test_readiness_not_quote_ready():
    result = build_quote_input_contract(
        _inp(
            handoff=_handoff(
                handoff_status="not_ready",
                recommended_partner_route=[],
                recommended_product_scope=[],
                missing_customer_info=["contact", "product_focus"],
            ),
            product_fit=_fit(recommended_product_focus=[]),
            has_contact_method=False,
        )
    )
    assert result["quote_module_readiness"] == "not_quote_ready"


def test_known_requirements_no_fabrication():
    result = build_quote_input_contract(_inp(notes_blob="general office furniture inquiry"))
    known = result["quote_input_fields"]["known_requirements"]
    assert known["quantity_or_volume"] is None
    assert known["delivery_location"] is None
    assert known["certification_requirement"] is None


def test_known_requirements_explicit_only():
    result = build_quote_input_contract(
        _inp(
            notes_blob="need 120 units adjustable desk frame ship to chicago ul certification",
            expected_timeline="Q3 2026",
        )
    )
    known = result["quote_input_fields"]["known_requirements"]
    assert known["quantity_or_volume"] is not None
    assert known["project_timeline"] == "Q3 2026"


def test_copyable_json_valid():
    result = build_quote_input_contract(_inp())
    parsed = json.loads(result["copyable_json"])
    assert parsed["lead_id"] == "lead-1"
    assert "quote_input_fields" in parsed
    assert "copyable_handoff_summary" not in parsed


def test_copyable_handoff_summary_content():
    result = build_quote_input_contract(_inp())
    summary = result["copyable_handoff_summary"]
    assert "Quote Input Contract — SWC Office Furniture" in summary
    assert "Safety:" in summary
    assert_no_forbidden_contract_phrases(summary)


def test_no_forbidden_phrases_in_contract():
    result = build_quote_input_contract(_inp())
    blob = json.dumps(result) + result["copyable_handoff_summary"]
    assert_no_forbidden_contract_phrases(blob)
