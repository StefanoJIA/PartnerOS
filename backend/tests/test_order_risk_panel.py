"""Order risk panel rule output shape (no DB)."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from app.models.enums import RiskLevel
from app.services.order_risk import build_order_risk_panel


def test_order_risk_panel_has_expected_fields():
    oid = uuid4()
    order = SimpleNamespace(
        id=oid,
        risk_level=RiskLevel.high.value,
        target_delivery_date=date(2026, 1, 10),
    )
    ms = SimpleNamespace(
        milestone_name="Cutting",
        planned_date=date(2025, 12, 1),
        actual_date=None,
        status="pending",
    )
    panel = build_order_risk_panel(order, [ms], [], today=date(2026, 5, 1))
    assert panel.overall_severity in ("low", "medium", "high")
    assert len(panel.items) >= 1
    first = panel.items[0]
    assert first.risk_level
    assert first.risk_reason
    assert first.recommended_action
