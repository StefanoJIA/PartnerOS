"""D8.5 market response intelligence smoke check."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import FeedbackTicket, MarketIntelligenceItem, Product, User
from app.models.customer_orders import CustomerOrder, OrderLineItem
from app.models.customer_quotes import Quote, QuoteLineItem

FORBIDDEN = (
    "internal_cost",
    "margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "password_hash",
    "storage_key",
    "token",
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

    def all(self):
        return self.rows


class _Db:
    def __init__(self) -> None:
        quote_id = uuid4()
        order_id = uuid4()
        self.mapping = {
            FeedbackTicket: [
                SimpleNamespace(
                    id=uuid4(),
                    ticket_number="FB-2026-0001",
                    feedback_type="tracking",
                    subject="Delayed adjustable frame shipment",
                    message="Customer reports late shipment and missing tracking for adjustable desk frame.",
                    response_summary=None,
                    status="new",
                    priority="high",
                    order_id=order_id,
                    created_at=datetime(2026, 5, 29, tzinfo=timezone.utc),
                )
            ],
            Quote: [
                SimpleNamespace(id=quote_id, status="converted_to_order"),
                SimpleNamespace(id=uuid4(), status="expired"),
            ],
            QuoteLineItem: [
                SimpleNamespace(
                    quote_id=quote_id,
                    product_category="Adjustable Frames",
                    product_name="Dual motor adjustable desk frame",
                    description_customer="Height adjustable frame",
                    quantity=12,
                    total_price=Decimal("2400.00"),
                )
            ],
            CustomerOrder: [SimpleNamespace(id=order_id, source_quote_id=quote_id, status="confirmed")],
            OrderLineItem: [
                SimpleNamespace(
                    order_id=order_id,
                    product_category="Adjustable Frames",
                    product_name="Dual motor adjustable desk frame",
                    description_customer="Height adjustable frame",
                    quantity=12,
                    total_price=Decimal("2400.00"),
                )
            ],
            MarketIntelligenceItem: [
                SimpleNamespace(
                    id=uuid4(),
                    title="Demand for quiet height adjustable frames",
                    related_product_category="Adjustable Frames",
                    market_segment="US office retrofit",
                    content="Buyers ask for lower noise and BIFMA support.",
                    tags="adjustable,quiet",
                    importance="high",
                )
            ],
            Product: [
                SimpleNamespace(
                    id=uuid4(),
                    product_name="Dual motor adjustable desk frame",
                    product_category="Adjustable Frames",
                    dimensions=None,
                    load_capacity=None,
                    lifting_speed="35mm/s",
                    noise_level=None,
                    available_certifications=None,
                    moq=20,
                    sample_available=True,
                    target_us_price_range=None,
                )
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
        Check("feedback tags extracted"),
        Check("demand board includes adjustable frames"),
        Check("product gaps present"),
        Check("recommendations advisory"),
        Check("safety no automation"),
        Check("no forbidden fields"),
    ]

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(),
        email="d8_5_market@test.example",
        is_active=True,
    )
    app.dependency_overrides[get_db] = _fake_db

    with TestClient(app) as client:
        response = client.get("/api/v1/market/response-intelligence")

    if response.status_code == 200:
        checks[0].pass_("HTTP 200")
    else:
        checks[0].fail(response.text[:160])
        data = {}
    data = response.json().get("data", {}) if response.status_code == 200 else {}

    summary = data.get("summary") or {}
    if {"feedback_ticket_count", "market_signal_count", "quote_count", "product_gap_count"}.issubset(summary):
        checks[1].pass_(f"signals={summary.get('market_signal_count')}")
    else:
        checks[1].fail("missing summary keys")

    tag_counts = ((data.get("feedback") or {}).get("tag_counts") or {})
    checks[2].pass_("risk/logistics") if tag_counts.get("risk_or_issue") and tag_counts.get("logistics") else checks[2].fail(str(tag_counts))

    demand_items = ((data.get("demand") or {}).get("items") or [])
    frame_row = next((row for row in demand_items if row.get("category") == "Adjustable Frames"), None)
    checks[3].pass_("Adjustable Frames") if frame_row and frame_row.get("adjustable_frame_focus") else checks[3].fail("missing")

    gap_items = ((data.get("product_gaps") or {}).get("items") or [])
    checks[4].pass_(f"{len(gap_items)} gap row(s)") if gap_items else checks[4].fail("empty")

    recs = data.get("recommendations") or []
    if recs and all(rec.get("human_review_required") is True and rec.get("auto_execute") is False for rec in recs):
        checks[5].pass_(f"{len(recs)} recommendation(s)")
    else:
        checks[5].fail(str(recs[:1]))

    safety = data.get("safety") or {}
    if (
        safety.get("read_only") is True
        and safety.get("ai_suggestions_advisory") is True
        and safety.get("ai_executed") is False
        and safety.get("customer_notified") is False
        and safety.get("supplier_notified") is False
        and safety.get("quote_status_changed") is False
        and safety.get("order_status_changed") is False
    ):
        checks[6].pass_("advisory only")
    else:
        checks[6].fail(str(safety))

    blob = json.dumps(data, ensure_ascii=False).lower()
    leaked = next((marker for marker in FORBIDDEN if marker in blob), None)
    checks[7].pass_("clean") if leaked is None else checks[7].fail(leaked)

    print("D8.5 Market Response Intelligence Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
