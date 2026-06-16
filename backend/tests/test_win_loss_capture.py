from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.services import growth_operations


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
