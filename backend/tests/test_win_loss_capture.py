from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.services import business_execution, growth_operations
from app.services.quotes.quote_learning import build_quote_playbook


def test_opportunity_win_loss_capture_does_not_auto_change_stage(monkeypatch):
    opportunity_id = uuid4()
    row = SimpleNamespace(
        id=opportunity_id,
        opportunity_name="HOSUN lifting systems quote",
        company=SimpleNamespace(company_name="Target Account"),
        customer_segment="project buyer",
        quote=SimpleNamespace(quote_number="Q-HOSUN-001"),
        partner_focus="HOSUN",
        product_focus=["lifting systems", "desk frames"],
        estimated_value=None,
        competition="",
        risk="",
        notes="",
        status="open",
        decision_stage="negotiation",
        probability=65,
        outcome_status=None,
        outcome_reason_category=None,
        customer_decision_factors=None,
        product_factors=None,
        partner_factors=None,
        outcome_recorded_at=None,
        won_reason=None,
        lost_reason=None,
        next_action=None,
        owner="sales",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    db = MagicMock()
    actor = SimpleNamespace(id=uuid4())
    payload = SimpleNamespace(
        model_dump=lambda exclude_unset=True: {
            "outcome": "lost",
            "reason_category": "certification",
            "lost_reason": "Customer required certification proof before award.",
            "competitor_signal": "Competitor claimed faster certification package.",
            "customer_decision_factors": ["certification", "delivery"],
            "product_dimensions": ["load", "noise", "warranty"],
            "product_factors": ["certification", "warranty"],
            "partner_factors": ["certification support"],
            "next_action": "Prepare certification evidence before next quote.",
            "owner": "sales",
            "notes": "Manual outcome capture only.",
        }
    )
    monkeypatch.setattr(growth_operations, "get_sales_opportunity", lambda db_arg, oid: row)
    monkeypatch.setattr(growth_operations, "_opportunity_path", lambda item: "/growth-operations")

    record = growth_operations.record_opportunity_win_loss(db, opportunity_id, payload, actor)

    assert row.status == "open"
    assert row.decision_stage == "negotiation"
    assert row.probability == 65
    assert row.outcome_status == "lost"
    assert row.outcome_reason_category == "certification"
    assert row.customer_decision_factors == ["certification", "delivery"]
    assert row.product_factors == ["certification", "warranty"]
    assert row.partner_factors == ["certification support"]
    assert record["outcome"] == "lost"
    assert record["reason_category"] == "certification"
    assert record["product_factors"] == ["certification", "warranty"]
    assert record["partner_factors"] == ["certification support"]
    assert record["safety"]["quote_status_changed"] is False
    assert record["safety"]["order_status_changed"] is False
    db.commit.assert_called_once()


def test_quote_playbook_reuses_manual_win_loss_learning_without_customer_exposure():
    quote = SimpleNamespace(
        id=uuid4(),
        company_id=None,
        learning_records=[
            SimpleNamespace(
                outcome_status="won",
                won_reason="Customer trusted stability and load proof.",
                lost_reason=None,
                customer_objection=None,
                reason_category="product_fit",
                customer_decision_factors=["stability", "project demand"],
                product_factors=["load", "noise", "certification"],
                product_dimensions=["load", "stability", "noise"],
                partner_factors=["delivery support"],
                delivery_feedback="delivery window accepted",
            ),
            SimpleNamespace(
                outcome_status="lost",
                won_reason=None,
                lost_reason="Certification evidence was not ready.",
                customer_objection="warranty and certification proof needed",
                reason_category="certification",
                customer_decision_factors=["certification", "warranty"],
                product_factors=["warranty", "test cycle"],
                product_dimensions=["warranty", "certification"],
                partner_factors=["certification support", "partner capacity"],
                delivery_feedback="delivery risk before project award",
            ),
        ],
        line_items=[
            SimpleNamespace(product_name="HOSUN heavy-duty lifting systems", product_category="desk frames", manual_product_name=None)
        ],
        partner_allocations=[],
        partner_splits=[SimpleNamespace(partner=SimpleNamespace(name="HOSUN"))],
        supplier_confirmations=[],
        metadata={},
        partner_focus="HOSUN",
    )

    playbook = build_quote_playbook(None, quote)

    assert playbook["recommendation_type"] == "internal_quote_playbook"
    assert playbook["evidence_count"] == 2
    assert playbook["won_count"] == 1
    assert playbook["lost_count"] == 1
    assert "load" in playbook["product_factors"]
    assert "certification" in playbook["customer_safe_wording_needed"]
    assert "partner capacity" in playbook["avoid_or_validate_before_sending"]
    assert playbook["safety"]["customer_notified"] is False
    assert playbook["safety"]["quote_status_changed"] is False
    assert "Internal recommendation only" in playbook["customer_safe_boundary"]


def test_repeat_business_recommendation_is_internal_manual_action():
    learning_won = [
        SimpleNamespace(
            won_reason="Project buyer accepted classroom deployment proof.",
            customer_decision_factors=["durability", "delivery consistency"],
            product_factors=["education furniture", "school desks/chairs"],
            product_dimensions=["durability", "procurement cycle"],
            partner_factors=["delivery support"],
        )
    ]
    learning_lost = [
        SimpleNamespace(
            lost_reason="Procurement cycle moved to next semester.",
            customer_objection="delivery consistency evidence needed",
            reason_category="timing",
            customer_decision_factors=["procurement cycle"],
            product_factors=["delivery consistency"],
            partner_factors=["partner capacity"],
        )
    ]

    recommendation = business_execution._repeat_business_recommendation(
        orders=[SimpleNamespace(id=uuid4())],
        open_feedback=[],
        open_quotes=[],
        opportunities=[],
        won_learning=learning_won,
        lost_learning=learning_lost,
        product_focus=["education furniture", "project furniture"],
        partner_focus=["JOOBOO"],
        value_tier="growth_account",
        next_motion={
            "owner": "account owner",
            "reason": "Order and won learning exist without open feedback.",
            "next_action": "Review delivery outcome before repeat follow-up.",
        },
    )

    assert recommendation["recommendation_type"] == "internal_repeat_business_recommendation"
    assert recommendation["repeat_potential"] == "high"
    assert "education furniture" in recommendation["recommended_product_family"]
    assert recommendation["manual_only"] is True
    assert recommendation["safety"]["external_message_sent"] is False
    assert "delivery support" in recommendation["quote_playbook_inputs"]["partner_factors_to_validate"]
    assert "Procurement cycle moved to next semester." in recommendation["quote_playbook_inputs"]["loss_factors_to_avoid"]


def test_product_commercial_playbook_promotes_product_family_learning_without_external_action():
    playbook = business_execution._product_commercial_playbook(
        {
            "partner_focus": "HOSUN",
            "product_focus": ["lifting systems", "desk frames", "heavy-duty supply"],
            "fit_status": "order_validated",
            "purchase_factors": ["load", "stability", "noise", "warranty"],
            "buying_factors_ranked": [{"factor": "certification", "losses": 1}],
            "customer_objections": ["packaging proof needed"],
            "validated_buying_factors": ["project demand"],
            "evidence_counts": {"wins": 2, "losses": 1, "orders": 1, "feedback": 1},
            "next_action": "Reuse load and stability proof before the next HOSUN quote.",
        }
    )

    assert playbook["recommendation_type"] == "internal_product_commercial_playbook"
    assert playbook["partner_focus"] == "HOSUN"
    assert "heavy-duty supply" in playbook["product_family"]
    assert "load" in playbook["quote_emphasis_suggestions"]
    assert "certification" in playbook["risk_before_next_quote"]
    assert playbook["repeat_business_potential"] == "strong_repeat_candidate"
    assert playbook["manual_only"] is True
    assert playbook["safety"]["external_message_sent"] is False
    assert "Internal product commercial playbook only" in playbook["customer_safe_boundary"]


def test_partner_commercial_playbook_keeps_partners_parallel_and_manual():
    playbook = business_execution._partner_commercial_playbook(
        {
            "partner_id": "partner-jooboo",
            "partner_name": "JOOBOO",
            "product_focus": ["education furniture", "school desks/chairs", "project furniture"],
            "risk_signals": ["resource needs"],
            "missing_inputs": ["procurement cycle wording"],
            "quote_support_count": 3,
            "order_count": 1,
            "win_rate": 0.66,
            "pilot_fit": "pilot_candidate",
            "allocation_fit": "allocate_next_quotes",
            "next_allocation_action": "Use JOOBOO for the next education furniture project quote.",
        }
    )

    assert playbook["recommendation_type"] == "internal_partner_commercial_playbook"
    assert playbook["partner_name"] == "JOOBOO"
    assert "school desks/chairs" in playbook["supported_product_families"]
    assert "education furniture" in playbook["common_win_contribution"]
    assert "resource needs" in playbook["common_risk_factors"]
    assert playbook["pilot_suitability"] == "pilot_risk_review_needed"
    assert playbook["manual_only"] is True
    assert playbook["safety"]["quote_status_changed"] is False


def test_product_partner_playbook_refs_match_quote_or_opportunity_context(monkeypatch):
    monkeypatch.setattr(
        business_execution,
        "build_product_market_fit_intelligence",
        lambda db, limit=80: {
            "items": [
                {
                    "partner_focus": "HOSUN",
                    "product_focus": ["lifting systems", "desk legs"],
                    "commercial_playbook": {
                        "recommendation_type": "internal_product_commercial_playbook",
                        "partner_focus": "HOSUN",
                        "product_family": ["lifting systems", "desk legs"],
                        "quote_emphasis_suggestions": ["load", "stability"],
                        "risk_before_next_quote": ["noise", "certification"],
                        "manual_only": True,
                    },
                }
            ]
        },
    )
    monkeypatch.setattr(
        business_execution,
        "build_partner_performance_intelligence",
        lambda db, limit=80: {
            "items": [
                {
                    "partner_name": "HOSUN",
                    "product_coverage": ["lifting systems", "heavy-duty supply"],
                    "commercial_playbook": {
                        "recommendation_type": "internal_partner_commercial_playbook",
                        "partner_name": "HOSUN",
                        "common_win_contribution": ["delivery support"],
                        "common_risk_factors": ["certification support"],
                        "manual_only": True,
                    },
                }
            ]
        },
    )

    refs = business_execution.build_product_partner_playbook_refs(
        MagicMock(),
        partner_focus="HOSUN",
        product_focus=["lifting systems"],
    )

    assert refs["recommendation_type"] == "internal_product_partner_playbook_refs"
    assert refs["product_playbooks"][0]["quote_emphasis_suggestions"] == ["load", "stability"]
    assert refs["partner_playbooks"][0]["common_risk_factors"] == ["certification support"]
    assert refs["manual_only"] is True
    assert refs["safety"]["external_message_sent"] is False
    assert "Internal playbook references only" in refs["customer_safe_boundary"]
