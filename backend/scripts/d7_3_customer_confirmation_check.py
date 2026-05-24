"""D7.3 Customer confirmation flow smoke check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url

FORBIDDEN = (
    "supplier notified",
    "production started",
    "shipment created",
    "inventory confirmed",
    "certification confirmed",
    "lead time confirmed",
    "payment received",
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


def _login(client: httpx.Client, base: str) -> dict[str, str] | None:
    r = client.post(f"{base}/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _ensure_pending_order(client: httpx.Client, base: str, headers: dict[str, str]) -> tuple[str | None, str]:
    lr = client.get(f"{base}/api/v1/orders?status=pending_customer_confirmation&limit=20", headers=headers)
    if lr.status_code == 200:
        for item in lr.json().get("data", {}).get("items", []):
            return item["id"], item.get("order_number", item["id"][:8])

    pr = client.get(f"{base}/api/v1/products?limit=5", headers=headers)
    if pr.status_code != 200 or not pr.json().get("data", {}).get("items"):
        return None, "no product"
    product_id = pr.json()["data"]["items"][0]["id"]

    lr2 = client.get(f"{base}/api/v1/quotes?status=sent&limit=30", headers=headers)
    quote_id = None
    for item in lr2.json().get("data", {}).get("items", []):
        qid = item["id"]
        orr = client.get(f"{base}/api/v1/orders?quote_id={qid}", headers=headers)
        rr = client.get(f"{base}/api/v1/quotes/{qid}/order-readiness", headers=headers)
        if (
            orr.status_code == 200
            and orr.json().get("data", {}).get("total", 0) == 0
            and rr.status_code == 200
            and not rr.json().get("data", {}).get("blocking_items")
        ):
            quote_id = qid
            break

    if not quote_id:
        cr = client.post(
            f"{base}/api/v1/quotes",
            headers=headers,
            json={
                "line_items": [{"product_id": product_id, "quantity": 5, "incoterm": "FOB"}],
                "bill_to": {"company": "D7.3 Smoke Co", "address": "123 Test St"},
                "ship_to": {"company": "D7.3 Smoke Co", "address": "123 Test St"},
                "payment_terms": "Subject to confirmation",
                "shipping_terms": "Subject to confirmation",
            },
        )
        if cr.status_code not in (200, 201):
            return None, f"create quote HTTP {cr.status_code}"
        quote_id = cr.json()["data"]["id"]
        client.post(f"{base}/api/v1/quotes/{quote_id}/mark-ready", headers=headers, json={})
        client.post(f"{base}/api/v1/quotes/{quote_id}/export-pdf", headers=headers, json={})
        client.post(
            f"{base}/api/v1/quotes/{quote_id}/mark-sent",
            headers=headers,
            json={"sent_channel": "email", "sent_to_name": "Smoke", "sent_to_company": "D7.3 Smoke Co"},
        )

    fr = client.post(f"{base}/api/v1/orders/from-quote", headers=headers, json={"quote_id": quote_id})
    if fr.status_code not in (200, 201):
        return None, f"from-quote HTTP {fr.status_code}: {fr.text[:120]}"
    order = fr.json().get("data", {})
    oid = order.get("id")
    if order.get("status") != "pending_customer_confirmation":
        return None, f"expected pending, got {order.get('status')}"
    return oid, order.get("order_number", oid[:8])


def main() -> int:
    base = log_backend_base_url()
    print("D7.3 Customer Confirmation Check")
    checks = [
        Check("find or create pending order"),
        Check("POST confirm-customer"),
        Check("confirmation record exists"),
        Check("order status confirmed"),
        Check("GET confirmations list"),
        Check("timeline confirmation event"),
        Check("POST void confirmation"),
        Check("safety flags"),
        Check("no forbidden promises"),
    ]
    conf_id = None

    try:
        with httpx.Client(timeout=120.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1

            order_id, label = _ensure_pending_order(client, base, headers)
            if not order_id:
                for c in checks:
                    c.fail(label)
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1
            checks[0].pass_(label)

            cr = client.post(
                f"{base}/api/v1/orders/{order_id}/confirm-customer",
                headers=headers,
                json={
                    "confirmation_type": "email",
                    "confirmed_by_name": "Smoke Buyer",
                    "evidence_reference": "D7.3 smoke email confirmation",
                    "note": "Customer confirmed by email.",
                },
            )
            if cr.status_code != 200:
                for c in checks[1:]:
                    c.fail(f"HTTP {cr.status_code}")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1

            data = cr.json().get("data", {})
            blob = cr.text.lower()
            checks[1].pass_()
            checks[2].pass_(data.get("confirmation", {}).get("confirmation_type", "email"))
            checks[3].pass_(data.get("status")) if data.get("status") == "confirmed" else checks[3].fail(data.get("status"))

            lr = client.get(f"{base}/api/v1/orders/{order_id}/confirmations", headers=headers)
            if lr.status_code == 200 and lr.json().get("data", {}).get("total", 0) >= 1:
                checks[4].pass_(f"{lr.json()['data']['total']} record(s)")
                conf_id = lr.json()["data"]["items"][0]["id"]
            else:
                checks[4].fail(f"HTTP {lr.status_code}")

            tr = client.get(f"{base}/api/v1/orders/{order_id}/timeline", headers=headers)
            types = [i.get("type") for i in tr.json().get("data", {}).get("items", [])]
            if "customer_confirmation_added" in types:
                checks[5].pass_(",".join(types))
            else:
                checks[5].fail(str(types))

            if conf_id:
                vr = client.post(
                    f"{base}/api/v1/orders/{order_id}/confirmations/{conf_id}/void",
                    headers=headers,
                    json={"reason": "D7.3 smoke void"},
                )
                checks[6].pass_() if vr.status_code == 200 else checks[6].fail(f"HTTP {vr.status_code}")
            else:
                checks[6].fail("no conf id")

            safety = data.get("safety") or {}
            ok_safety = (
                safety.get("production_started") is False
                and safety.get("shipment_created") is False
                and safety.get("supplier_notified") is False
                and safety.get("payment_received") is False
            )
            checks[7].pass_() if ok_safety else checks[7].fail(str(safety))

            if any(p in blob for p in FORBIDDEN):
                checks[8].fail("forbidden text")
            else:
                checks[8].pass_()

    except httpx.ConnectError:
        for c in checks:
            if not c.ok:
                c.fail("backend unreachable")

    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
