"""D7.4 Partner split and supplier confirmation smoke check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url

FORBIDDEN = (
    "supplier notified automatically",
    "production started",
    "shipment created",
    "inventory guaranteed",
    "certification guaranteed",
    "lead time guaranteed",
    "delivery guaranteed",
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


def _ensure_confirmed_order(client: httpx.Client, base: str, headers: dict[str, str]) -> tuple[str | None, str]:
    lr = client.get(f"{base}/api/v1/orders?status=confirmed&limit=20", headers=headers)
    if lr.status_code == 200:
        for item in lr.json().get("data", {}).get("items", []):
            return item["id"], item.get("order_number", item["id"][:8])

    pr = client.get(f"{base}/api/v1/products?limit=5", headers=headers)
    if pr.status_code != 200 or not pr.json().get("data", {}).get("items"):
        return None, "no product"
    product_id = pr.json()["data"]["items"][0]["id"]

    qr = client.get(f"{base}/api/v1/quotes?status=sent&limit=30", headers=headers)
    quote_id = None
    for item in qr.json().get("data", {}).get("items", []):
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
                "bill_to": {"company": "D7.4 Smoke Co", "address": "123 Test St"},
                "ship_to": {"company": "D7.4 Smoke Co", "address": "123 Test St"},
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
            json={"sent_channel": "email", "sent_to_name": "Smoke", "sent_to_company": "D7.4 Smoke Co"},
        )

    fr = client.post(f"{base}/api/v1/orders/from-quote", headers=headers, json={"quote_id": quote_id})
    if fr.status_code not in (200, 201):
        return None, f"from-quote HTTP {fr.status_code}"
    order_id = fr.json()["data"].get("id") or fr.json()["data"].get("order", {}).get("id")
    onum = fr.json()["data"].get("order_number", quote_id[:8])

    cf = client.post(
        f"{base}/api/v1/orders/{order_id}/confirm-customer",
        headers=headers,
        json={"confirmation_type": "email", "note": "D7.4 smoke customer confirmation"},
    )
    if cf.status_code != 200:
        return None, f"confirm-customer HTTP {cf.status_code}"
    return order_id, onum


def main() -> int:
    base = log_backend_base_url()
    print("D7.4 Partner Split & Supplier Confirmation Check")
    checks = [
        Check("find or create confirmed order"),
        Check("POST ensure partner splits"),
        Check("at least one split exists"),
        Check("split subtotal > 0"),
        Check("POST supplier confirmation"),
        Check("confirmation record exists"),
        Check("split supplier_confirmation_status updated"),
        Check("production_started=false"),
        Check("shipment_created=false"),
        Check("supplier_notified=false"),
        Check("timeline supplier_confirmation_added"),
        Check("no forbidden promises"),
    ]

    try:
        with httpx.Client(timeout=120.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1

            order_id, label = _ensure_confirmed_order(client, base, headers)
            if not order_id:
                for c in checks:
                    c.fail(label)
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1
            checks[0].pass_(label)

            er = client.post(f"{base}/api/v1/orders/{order_id}/partner-splits/ensure", headers=headers)
            if er.status_code != 200:
                for c in checks[1:]:
                    c.fail(f"HTTP {er.status_code}: {er.text[:200]}")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1
            checks[1].pass_()
            edata = er.json().get("data", {})
            splits = edata.get("splits") or edata.get("items") or []
            if not splits:
                lr = client.get(f"{base}/api/v1/orders/{order_id}/partner-splits", headers=headers)
                splits = lr.json().get("data", {}).get("items", [])

            if splits:
                checks[2].pass_(f"{len(splits)} split(s)")
                subtotal = float(splits[0].get("subtotal", 0))
                checks[3].pass_(str(subtotal)) if subtotal > 0 else checks[3].fail(str(subtotal))
                split_id = splits[0]["id"]
            else:
                checks[2].fail("empty")
                checks[3].fail("skipped")
                split_id = None

            safety = edata.get("safety", {})
            blob = er.text.lower()

            if split_id:
                sr = client.post(
                    f"{base}/api/v1/orders/{order_id}/partner-splits/{split_id}/supplier-confirmations",
                    headers=headers,
                    json={
                        "confirmation_status": "confirmed",
                        "production_capacity_confirmed": True,
                        "note": "D7.4 smoke supplier confirmation",
                    },
                )
                if sr.status_code in (200, 201):
                    checks[4].pass_()
                    sdata = sr.json().get("data", {})
                    conf = sdata.get("confirmation") or {}
                    checks[5].pass_(conf.get("confirmation_status", "ok"))
                    split_status = sdata.get("supplier_confirmation_status") or splits[0].get("supplier_confirmation_status")
                    if split_status == "confirmed" or conf.get("confirmation_status") == "confirmed":
                        checks[6].pass_(str(split_status or conf.get("confirmation_status")))
                    else:
                        detail = client.get(f"{base}/api/v1/orders/{order_id}/partner-splits/{split_id}", headers=headers)
                        st = detail.json().get("data", {}).get("supplier_confirmation_status")
                        checks[6].pass_(st) if st == "confirmed" else checks[6].fail(str(st))
                    safety = sdata.get("safety", safety)
                    blob += sr.text.lower()
                else:
                    checks[4].fail(f"HTTP {sr.status_code}")
                    for c in checks[5:7]:
                        c.fail("skipped")

            checks[7].pass_() if safety.get("production_started") is False else checks[7].fail(str(safety))
            checks[8].pass_() if safety.get("shipment_created") is False else checks[8].fail(str(safety))
            checks[9].pass_() if safety.get("supplier_notified") is False else checks[9].fail(str(safety))

            tr = client.get(f"{base}/api/v1/orders/{order_id}/timeline", headers=headers)
            types = [i.get("type") for i in tr.json().get("data", {}).get("items", [])]
            checks[10].pass_(",".join(types)) if "supplier_confirmation_added" in types else checks[10].fail(str(types))

            if any(p in blob for p in FORBIDDEN):
                checks[11].fail("forbidden text")
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
