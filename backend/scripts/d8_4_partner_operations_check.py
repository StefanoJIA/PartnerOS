"""D8.4 partner operations dashboard smoke check."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import ManufacturingPartner, User
from app.models.customer_orders import OrderPartnerSplit, OrderProductionMilestone, ShipmentPlan

FORBIDDEN = (
    "internal_cost",
    "margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "supplier_reference",
    "storage_key",
    "password_hash",
)


class Check:
    def __init__(self, label: str) -> None:
        self.label = label
        self.ok = False
        self.detail = ""

    def pass_(self, detail: str = "") -> None:
        self.ok = True
        self.detail = detail

    def fail(self, detail: str) -> None:
        self.ok = False
        self.detail = detail

    def line(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{status}] {self.label}{suffix}"


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):  # noqa: ARG002
        return self

    def all(self):
        return self.rows


class _Db:
    def __init__(self) -> None:
        partner_id = uuid4()
        split_id = uuid4()
        order_id = uuid4()
        self.mapping = {
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

    def query(self, model):
        return _Query(self.mapping.get(model, []))


def _fake_db():
    yield _Db()


def main() -> int:
    checks = [
        Check("route returns 200"),
        Check("summary present"),
        Check("partner rows present or empty-safe"),
        Check("safety read-only"),
        Check("no forbidden fields"),
    ]

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(),
        email="d8_4_ops@test.example",
        is_active=True,
    )
    app.dependency_overrides[get_db] = _fake_db

    with TestClient(app) as client:
        response = client.get("/api/v1/operations/partner-dashboard")

    if response.status_code == 200:
        checks[0].pass_("HTTP 200")
    else:
        checks[0].fail(response.text[:160])
        data = {}
    data = response.json().get("data", {}) if response.status_code == 200 else {}

    summary = data.get("summary") or {}
    if {"partner_count", "split_count", "order_count"}.issubset(summary):
        checks[1].pass_(f"partners={summary.get('partner_count')}")
    else:
        checks[1].fail("missing summary counts")

    items = data.get("items")
    if isinstance(items, list):
        checks[2].pass_(f"{len(items)} partner row(s)")
    else:
        checks[2].fail("items is not a list")

    safety = data.get("safety") or {}
    if (
        safety.get("read_only") is True
        and safety.get("supplier_notified") is False
        and safety.get("customer_notified") is False
        and safety.get("shipment_created") is False
        and safety.get("order_status_changed") is False
    ):
        checks[3].pass_("no mutations")
    else:
        checks[3].fail(str(safety))

    blob = json.dumps(data, ensure_ascii=False).lower()
    leaked = next((marker for marker in FORBIDDEN if marker in blob), None)
    checks[4].pass_("clean") if leaked is None else checks[4].fail(leaked)

    print("D8.4 Partner Operations Dashboard Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
