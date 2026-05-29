"""Tests for D8.4 partner operations dashboard aggregation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.models import ManufacturingPartner
from app.models.customer_orders import OrderPartnerSplit, OrderProductionMilestone, ShipmentPlan
from app.services.orders.partner_operations_dashboard import build_partner_operations_dashboard


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):  # noqa: ARG002
        return self

    def all(self):
        return self.rows


class _Db:
    def __init__(self, mapping):
        self.mapping = mapping

    def query(self, model):
        return _Query(self.mapping.get(model, []))


def test_partner_operations_dashboard_counts_risk_flags():
    partner_id = uuid4()
    split_id = uuid4()
    order_id = uuid4()
    db = _Db(
        {
            OrderPartnerSplit: [
                SimpleNamespace(
                    id=split_id,
                    order_id=order_id,
                    partner_id=partner_id,
                    supplier_confirmation_status="pending",
                    split_status="production_pending",
                    line_item_count=2,
                    subtotal=Decimal("1200.00"),
                    currency="USD",
                    expected_ready_date=date(2026, 6, 20),
                )
            ],
            ManufacturingPartner: [
                SimpleNamespace(id=partner_id, partner_name="Demo Partner", brand_name=None, partner_type="Factory")
            ],
            OrderProductionMilestone: [
                SimpleNamespace(
                    partner_id=partner_id,
                    partner_split_id=split_id,
                    milestone_type="assembly",
                    status="delayed",
                )
            ],
            ShipmentPlan: [
                SimpleNamespace(partner_split_id=split_id, status="planned"),
            ],
        }
    )

    data = build_partner_operations_dashboard(db)
    row = data["items"][0]

    assert data["summary"]["partner_count"] == 1
    assert data["summary"]["supplier_open_split_count"] == 1
    assert data["summary"]["delayed_milestone_count"] == 1
    assert row["partner_name"] == "Demo Partner"
    assert row["subtotal_by_currency"] == {"USD": "1200.00"}
    assert row["risk_flags"] == ["supplier_confirmation_open", "production_delayed"]
    assert data["safety"]["read_only"] is True
    assert data["safety"]["supplier_notified"] is False
