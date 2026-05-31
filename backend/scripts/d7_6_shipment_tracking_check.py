"""D7.6 Shipment tracking foundation smoke check."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

os.environ.setdefault("BACKEND_BASE_URL", "http://127.0.0.1:8014")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url

FORBIDDEN = (
    "supplier notified automatically",
    "customer notified automatically",
    "carrier api",
    "webhook sent",
    "email sent",
    "order automatically shipped",
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


def _json(response: httpx.Response) -> dict:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _finish(checks: list[Check]) -> int:
    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def _login(client: httpx.Client, base: str) -> dict[str, str] | None:
    r = client.post(f"{base}/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    if r.status_code != 200:
        return None
    token = _json(r).get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else None


def _first_confirmed_order(client: httpx.Client, base: str, headers: dict[str, str]) -> tuple[str | None, str]:
    lr = client.get(f"{base}/api/v1/orders?status=confirmed&limit=20", headers=headers)
    for item in _json(lr).get("data", {}).get("items", []):
        return item["id"], item.get("order_number", item["id"][:8])
    return None, "no confirmed order"


def _first_pending_order(client: httpx.Client, base: str, headers: dict[str, str]) -> str | None:
    lr = client.get(f"{base}/api/v1/orders?status=pending_customer_confirmation&limit=20", headers=headers)
    items = _json(lr).get("data", {}).get("items", [])
    return items[0]["id"] if items else None


def main() -> int:
    base = log_backend_base_url()
    print("D7.6 Shipment Tracking Check")
    checks = [
        Check("find confirmed order"),
        Check("pending order POST is blocked"),
        Check("POST shipment plan"),
        Check("GET shipment plans"),
        Check("PATCH shipment status"),
        Check("cancel via PATCH status"),
        Check("timeline shipment events"),
        Check("safety shipment_created=false"),
        Check("safety supplier_notified=false"),
        Check("safety customer_notified=false"),
        Check("order status not auto shipped"),
        Check("no forbidden automation text"),
    ]

    try:
        with httpx.Client(timeout=120.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                return _finish(checks)

            order_id, label = _first_confirmed_order(client, base, headers)
            if not order_id:
                for c in checks:
                    c.fail(label)
                return _finish(checks)
            checks[0].pass_(label)

            pending_id = _first_pending_order(client, base, headers)
            if pending_id:
                blocked = client.post(
                    f"{base}/api/v1/orders/{pending_id}/shipment-plans",
                    headers=headers,
                    json={"shipment_method": "sea", "status": "planned"},
                )
                checks[1].pass_(f"HTTP {blocked.status_code}") if blocked.status_code == 400 else checks[1].fail(
                    f"HTTP {blocked.status_code}"
                )
            else:
                checks[1].pass_("no pending order to exercise")

            create = client.post(
                f"{base}/api/v1/orders/{order_id}/shipment-plans",
                headers=headers,
                json={
                    "shipment_method": "sea",
                    "incoterm": "FOB",
                    "origin": "Ningbo",
                    "destination": "New York",
                    "estimated_ship_date": "2026-06-15",
                    "estimated_arrival_date": "2026-07-20",
                    "tracking_number": "D76-SMOKE-TRACK",
                    "status": "planned",
                    "notes": "D7.6 smoke manual shipment plan",
                },
            )
            blob = create.text.lower()
            if create.status_code not in (200, 201):
                for c in checks[2:]:
                    c.fail(f"HTTP {create.status_code}: {create.text[:200]}")
                return _finish(checks)
            plan = _json(create).get("data", {})
            plan_id = plan.get("id")
            safety = plan.get("safety", {})
            checks[2].pass_(plan_id or "")

            listed = client.get(f"{base}/api/v1/orders/{order_id}/shipment-plans", headers=headers)
            blob += listed.text.lower()
            plans = _json(listed).get("data", {}).get("items", []) if listed.status_code == 200 else []
            checks[3].pass_(f"{len(plans)} plan(s)") if any(p.get("id") == plan_id for p in plans) else checks[3].fail(
                f"HTTP {listed.status_code}"
            )

            patched = client.patch(
                f"{base}/api/v1/orders/{order_id}/shipment-plans/{plan_id}",
                headers=headers,
                json={"status": "shipped", "tracking_number": "D76-SMOKE-SHIPPED"},
            )
            blob += patched.text.lower()
            pdata = _json(patched).get("data", {}) if patched.status_code == 200 else {}
            if patched.status_code == 200 and pdata.get("status") == "shipped":
                checks[4].pass_()
                safety = pdata.get("safety", safety)
            else:
                checks[4].fail(f"HTTP {patched.status_code}")

            cancelled = client.patch(
                f"{base}/api/v1/orders/{order_id}/shipment-plans/{plan_id}",
                headers=headers,
                json={"status": "cancelled"},
            )
            blob += cancelled.text.lower()
            cancelled_data = _json(cancelled).get("data", {}) if cancelled.status_code == 200 else {}
            if cancelled.status_code == 200 and cancelled_data.get("status") == "cancelled":
                checks[5].pass_()
            else:
                checks[5].fail(f"HTTP {cancelled.status_code}")

            tr = client.get(f"{base}/api/v1/orders/{order_id}/timeline", headers=headers)
            types = [i.get("type") for i in _json(tr).get("data", {}).get("items", [])]
            if "shipment_plan_created" in types and "shipment_status_changed" in types:
                checks[6].pass_()
            else:
                checks[6].fail(str(types))

            checks[7].pass_() if safety.get("shipment_created") is False else checks[7].fail(str(safety))
            checks[8].pass_() if safety.get("supplier_notified") is False else checks[8].fail(str(safety))
            checks[9].pass_() if safety.get("customer_notified") is False else checks[9].fail(str(safety))

            order = client.get(f"{base}/api/v1/orders/{order_id}", headers=headers)
            status = _json(order).get("data", {}).get("status")
            checks[10].pass_(status) if status not in ("shipped", "delivered") else checks[10].fail(status)

            checks[11].pass_() if not any(p in blob for p in FORBIDDEN) else checks[11].fail("forbidden text")

    except httpx.ConnectError:
        for c in checks:
            if not c.ok:
                c.fail("backend unreachable")

    return _finish(checks)


if __name__ == "__main__":
    sys.exit(main())
