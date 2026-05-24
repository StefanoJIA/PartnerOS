"""D7.2 Order CRUD MVP smoke check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url

FORBIDDEN = (
    "production started",
    "shipment created",
    "shipment booked",
    "supplier notified automatically",
    "inventory confirmed",
    "certification confirmed",
    "lead time confirmed",
    "delivery guaranteed",
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


def _ensure_sent_quote(client: httpx.Client, base: str, headers: dict[str, str]) -> tuple[str | None, str]:
    lr = client.get(f"{base}/api/v1/quotes?status=sent&limit=30", headers=headers)
    if lr.status_code != 200:
        return None, "list quotes failed"
    for item in lr.json().get("data", {}).get("items", []):
        qid = item["id"]
        orr = client.get(f"{base}/api/v1/orders?quote_id={qid}", headers=headers)
        if orr.status_code == 200 and orr.json().get("data", {}).get("total", 0) == 0:
            rr = client.get(f"{base}/api/v1/quotes/{qid}/order-readiness", headers=headers)
            if rr.status_code == 200 and not rr.json().get("data", {}).get("blocking_items"):
                return qid, item.get("quote_number", qid[:8])

    pr = client.get(f"{base}/api/v1/products?limit=5", headers=headers)
    if pr.status_code != 200 or not pr.json().get("data", {}).get("items"):
        return None, "no product for new quote"
    product_id = pr.json()["data"]["items"][0]["id"]

    cr = client.post(
        f"{base}/api/v1/quotes",
        headers=headers,
        json={
            "line_items": [{"product_id": product_id, "quantity": 5, "incoterm": "FOB"}],
            "bill_to": {"name": "Smoke Buyer", "company": "D7.2 Smoke Co", "address": "123 Test St, Shanghai"},
            "ship_to": {"name": "Smoke Buyer", "company": "D7.2 Smoke Co", "address": "123 Test St, Shanghai"},
            "payment_terms": "Subject to confirmation",
            "shipping_terms": "Subject to confirmation",
        },
    )
    if cr.status_code not in (200, 201):
        return None, f"create quote HTTP {cr.status_code}"
    qid = cr.json()["data"]["id"]
    client.post(f"{base}/api/v1/quotes/{qid}/mark-ready", headers=headers, json={})
    client.post(f"{base}/api/v1/quotes/{qid}/export-pdf", headers=headers, json={})
    client.post(
        f"{base}/api/v1/quotes/{qid}/mark-sent",
        headers=headers,
        json={"sent_channel": "email", "sent_to_name": "Smoke", "sent_to_company": "D7.2 Smoke Co"},
    )
    rr = client.get(f"{base}/api/v1/quotes/{qid}/order-readiness", headers=headers)
    if rr.status_code != 200 or rr.json().get("data", {}).get("blocking_items"):
        return None, "new quote not readiness-ready"
    return qid, cr.json()["data"].get("quote_number", qid[:8])


def main() -> int:
    base = log_backend_base_url()
    print("D7.2 Order CRUD Check")
    checks = [
        Check("find or prepare sent quote"),
        Check("POST from-quote pending"),
        Check("order_number format"),
        Check("line items copied"),
        Check("order_created=true"),
        Check("production_started=false"),
        Check("shipment_created=false"),
        Check("supplier_notified=false"),
        Check("confirm customer"),
        Check("status confirmed"),
        Check("timeline events"),
        Check("no forbidden promises"),
    ]
    order_id = None

    try:
        with httpx.Client(timeout=120.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1

            quote_id, qnum = _ensure_sent_quote(client, base, headers)
            if not quote_id:
                for c in checks:
                    c.fail(qnum)
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1
            checks[0].pass_(qnum)

            fr = client.post(
                f"{base}/api/v1/orders/from-quote",
                headers=headers,
                json={"quote_id": quote_id},
            )
            if fr.status_code not in (200, 201):
                for c in checks[1:]:
                    c.fail(f"HTTP {fr.status_code}: {fr.text[:200]}")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1

            blob = fr.text.lower()
            data = fr.json().get("data", {})
            order = data.get("order", {})
            safety = data.get("safety", {})
            order_id = order.get("id")

            if order.get("status") == "pending_customer_confirmation":
                checks[1].pass_()
            else:
                checks[1].fail(order.get("status"))

            onum = order.get("order_number", "")
            if onum.startswith("O-") and len(onum.split("-")) == 3:
                checks[2].pass_(onum)
            else:
                checks[2].fail(onum)

            lines = data.get("line_items") or order.get("line_items") or []
            checks[3].pass_(f"{len(lines)} line(s)") if lines else checks[3].fail("empty")

            checks[4].pass_() if safety.get("order_created") is True else checks[4].fail(str(safety))
            checks[5].pass_() if safety.get("production_started") is False else checks[5].fail(str(safety))
            checks[6].pass_() if safety.get("shipment_created") is False else checks[6].fail(str(safety))
            checks[7].pass_() if safety.get("supplier_notified") is False else checks[7].fail(str(safety))

            if order_id:
                cf = client.post(
                    f"{base}/api/v1/orders/{order_id}/confirm-customer",
                    headers=headers,
                    json={"confirmation_type": "email", "note": "D7.2 smoke confirmation"},
                )
                if cf.status_code == 200:
                    checks[8].pass_()
                    confirmed = cf.json().get("data", {}).get("status")
                    checks[9].pass_() if confirmed == "confirmed" else checks[9].fail(confirmed)
                    tr = client.get(f"{base}/api/v1/orders/{order_id}/timeline", headers=headers)
                    types = [i.get("type") for i in tr.json().get("data", {}).get("items", [])]
                    if "order_created" in types and "customer_confirmed" in types:
                        checks[10].pass_(",".join(types))
                    else:
                        checks[10].fail(str(types))
                else:
                    checks[8].fail(f"HTTP {cf.status_code}")
                    checks[9].fail("skipped")
                    checks[10].fail("skipped")

            if any(p in blob for p in FORBIDDEN):
                checks[11].fail("forbidden text in response")
            else:
                checks[11].pass_()

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
