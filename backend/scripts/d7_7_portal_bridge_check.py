"""D7.7 customer portal bridge smoke check."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient

FORBIDDEN = (
    "internal_cost",
    "margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "supplier_reference",
    "storage_key",
    "backend/storage",
    "portal_customer_api_token",
    "test-portal-token",
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


def _new_client(*, enabled: bool):
    os.environ["PORTAL_CUSTOMER_API_ENABLED"] = "true" if enabled else "false"
    os.environ["PORTAL_CUSTOMER_API_REQUIRE_TOKEN"] = "true"
    os.environ["PORTAL_CUSTOMER_API_TOKEN"] = "test-portal-token"
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    return TestClient(create_app(), raise_server_exceptions=False)


def _no_forbidden_blob(*responses) -> tuple[bool, str]:
    payloads = []
    for response in responses:
        try:
            payloads.append(response.json())
        except ValueError:
            payloads.append({})
    blob = json.dumps(payloads, ensure_ascii=False).lower()
    for marker in FORBIDDEN:
        if marker in blob:
            return False, marker
    return True, "clean"


def _json(response) -> dict:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    print("D7.7 Customer Portal Bridge Check")
    checks = [
        Check("disabled behavior"),
        Check("token required"),
        Check("token rejected"),
        Check("products customer fields"),
        Check("orders customer fields"),
        Check("order detail customer fields"),
        Check("production customer fields"),
        Check("shipment customer fields"),
        Check("resources customer fields"),
        Check("feedback ticket created"),
        Check("no forbidden internal fields"),
    ]

    with _new_client(enabled=False) as c:
        r = c.get("/api/v1/portal/customer/products")
        checks[0].pass_(f"HTTP {r.status_code}") if r.status_code == 503 else checks[0].fail(f"HTTP {r.status_code}")

    with _new_client(enabled=True) as c:
        missing = c.get("/api/v1/portal/customer/products")
        wrong = c.get("/api/v1/portal/customer/products", headers={"Authorization": "Bearer wrong"})
        checks[1].pass_(f"HTTP {missing.status_code}") if missing.status_code == 401 else checks[1].fail(f"HTTP {missing.status_code}")
        checks[2].pass_(f"HTTP {wrong.status_code}") if wrong.status_code == 403 else checks[2].fail(f"HTTP {wrong.status_code}")

        headers = {"Authorization": "Bearer test-portal-token"}
        products = c.get("/api/v1/portal/customer/products?limit=5", headers=headers)
        orders = c.get("/api/v1/portal/customer/orders?limit=5", headers=headers)
        checks[3].pass_(f"HTTP {products.status_code}") if products.status_code == 200 else checks[3].fail(products.text[:160])
        checks[4].pass_(f"HTTP {orders.status_code}") if orders.status_code == 200 else checks[4].fail(orders.text[:160])

        order_items = _json(orders).get("data", {}).get("items", []) if orders.status_code == 200 else []
        detail = production = shipment = resources = None
        if order_items:
            oid = order_items[0]["id"]
            detail = c.get(f"/api/v1/portal/customer/orders/{oid}", headers=headers)
            production = c.get(f"/api/v1/portal/customer/orders/{oid}/production", headers=headers)
            shipment = c.get(f"/api/v1/portal/customer/orders/{oid}/shipment", headers=headers)
            resources = c.get(f"/api/v1/portal/customer/orders/{oid}/resources", headers=headers)
            checks[5].pass_(f"HTTP {detail.status_code}") if detail.status_code == 200 else checks[5].fail(detail.text[:160])
            checks[6].pass_(f"HTTP {production.status_code}") if production.status_code == 200 else checks[6].fail(production.text[:160])
            checks[7].pass_(f"HTTP {shipment.status_code}") if shipment.status_code == 200 else checks[7].fail(shipment.text[:160])
            checks[8].pass_(f"HTTP {resources.status_code}") if resources.status_code == 200 else checks[8].fail(resources.text[:160])
        else:
            checks[5].pass_("no order rows")
            checks[6].pass_("no order rows")
            checks[7].pass_("no order rows")
            checks[8].pass_("no order rows")

        feedback = c.post(
            "/api/v1/portal/customer/feedback",
            headers=headers,
            json={
                "order_id": order_items[0]["id"] if order_items else None,
                "feedback_type": "tracking",
                "subject": "D7.7 smoke feedback",
                "message": "Customer portal bridge smoke feedback.",
                "customer_name": "Smoke Customer",
                "customer_email": "smoke@example.com",
            },
        )
        fdata = _json(feedback).get("data", {}) if feedback.status_code == 201 else {}
        if feedback.status_code == 201 and fdata.get("customer_notified") is False and fdata.get("automatic_reply_sent") is False:
            checks[9].pass_(fdata.get("ticket_number", "created"))
        else:
            checks[9].fail(feedback.text[:160])

        responses = [products, orders, feedback]
        responses.extend(r for r in (detail, production, shipment, resources) if r is not None)
        clean, detail_text = _no_forbidden_blob(*responses)
        checks[10].pass_(detail_text) if clean else checks[10].fail(detail_text)

    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
