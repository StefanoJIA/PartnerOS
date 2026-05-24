"""D7.5 Production milestone foundation smoke check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url

FORBIDDEN = (
    "shipment created",
    "supplier notified automatically",
    "customer notified automatically",
    "lead time guaranteed",
    "delivery guaranteed",
    "production automatically started",
    "shipment booked",
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


def _setup_order_with_split(client: httpx.Client, base: str, headers: dict[str, str]) -> tuple[str | None, str | None, str]:
    lr = client.get(f"{base}/api/v1/orders?status=confirmed&limit=20", headers=headers)
    order_id = None
    for item in lr.json().get("data", {}).get("items", []):
        oid = item["id"]
        sr = client.get(f"{base}/api/v1/orders/{oid}/partner-splits", headers=headers)
        if sr.status_code == 200 and sr.json().get("data", {}).get("total", 0) > 0:
            return oid, sr.json()["data"]["items"][0]["id"], item.get("order_number", oid[:8])

    pr = client.get(f"{base}/api/v1/products?limit=5", headers=headers)
    if pr.status_code != 200 or not pr.json().get("data", {}).get("items"):
        return None, None, "no product"
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
                "bill_to": {"company": "D7.5 Smoke Co", "address": "123 Test St"},
                "ship_to": {"company": "D7.5 Smoke Co", "address": "123 Test St"},
                "payment_terms": "Subject to confirmation",
                "shipping_terms": "Subject to confirmation",
            },
        )
        if cr.status_code not in (200, 201):
            return None, None, f"create quote HTTP {cr.status_code}"
        quote_id = cr.json()["data"]["id"]
        client.post(f"{base}/api/v1/quotes/{quote_id}/mark-ready", headers=headers, json={})
        client.post(f"{base}/api/v1/quotes/{quote_id}/export-pdf", headers=headers, json={})
        client.post(
            f"{base}/api/v1/quotes/{quote_id}/mark-sent",
            headers=headers,
            json={"sent_channel": "email", "sent_to_name": "Smoke", "sent_to_company": "D7.5 Smoke Co"},
        )

    fr = client.post(f"{base}/api/v1/orders/from-quote", headers=headers, json={"quote_id": quote_id})
    if fr.status_code not in (200, 201):
        return None, None, f"from-quote HTTP {fr.status_code}"
    order_id = fr.json()["data"].get("id")
    onum = fr.json()["data"].get("order_number", quote_id[:8])

    client.post(
        f"{base}/api/v1/orders/{order_id}/confirm-customer",
        headers=headers,
        json={"confirmation_type": "email", "note": "D7.5 smoke"},
    )
    client.post(f"{base}/api/v1/orders/{order_id}/partner-splits/ensure", headers=headers, json={})
    sr = client.get(f"{base}/api/v1/orders/{order_id}/partner-splits", headers=headers)
    splits = sr.json().get("data", {}).get("items", [])
    if not splits:
        return None, None, "no splits"
    split_id = splits[0]["id"]
    client.post(
        f"{base}/api/v1/orders/{order_id}/partner-splits/{split_id}/supplier-confirmations",
        headers=headers,
        json={"confirmation_status": "confirmed", "production_capacity_confirmed": True},
    )
    return order_id, split_id, onum


def main() -> int:
    base = log_backend_base_url()
    print("D7.5 Production Milestone Check")
    checks = [
        Check("find or create order with split"),
        Check("POST ensure production milestones"),
        Check("milestones created"),
        Check("PATCH milestone in_progress"),
        Check("PATCH milestone completed"),
        Check("timeline production_milestone_updated"),
        Check("shipment_created=false"),
        Check("supplier_notified=false"),
        Check("customer_notified=false"),
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

            order_id, split_id, label = _setup_order_with_split(client, base, headers)
            if not order_id or not split_id:
                for c in checks:
                    c.fail(label)
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1
            checks[0].pass_(label)

            er = client.post(
                f"{base}/api/v1/orders/{order_id}/partner-splits/{split_id}/production-milestones/ensure",
                headers=headers,
            )
            if er.status_code != 200:
                for c in checks[1:]:
                    c.fail(f"HTTP {er.status_code}: {er.text[:200]}")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1
            checks[1].pass_()
            edata = er.json().get("data", {})
            milestones = edata.get("milestones") or []
            safety = edata.get("safety", {})
            blob = er.text.lower()

            if milestones:
                checks[2].pass_(f"{len(milestones)} milestone(s)")
                mid1 = milestones[0]["id"]
                mid2 = milestones[1]["id"] if len(milestones) > 1 else mid1
            else:
                lr = client.get(
                    f"{base}/api/v1/orders/{order_id}/partner-splits/{split_id}/production-milestones",
                    headers=headers,
                )
                milestones = lr.json().get("data", {}).get("items", [])
                checks[2].pass_(f"{len(milestones)} milestone(s)") if milestones else checks[2].fail("empty")
                mid1 = milestones[0]["id"] if milestones else None
                mid2 = milestones[1]["id"] if len(milestones) > 1 else mid1

            if mid1:
                u1 = client.patch(
                    f"{base}/api/v1/orders/{order_id}/production-milestones/{mid1}",
                    headers=headers,
                    json={"status": "in_progress", "notes": "D7.5 smoke in progress"},
                )
                checks[3].pass_() if u1.status_code == 200 else checks[3].fail(f"HTTP {u1.status_code}")
                safety = u1.json().get("data", {}).get("safety", safety)
                blob += u1.text.lower()

                u2 = client.patch(
                    f"{base}/api/v1/orders/{order_id}/production-milestones/{mid2}",
                    headers=headers,
                    json={"status": "completed"},
                )
                checks[4].pass_() if u2.status_code == 200 else checks[4].fail(f"HTTP {u2.status_code}")
                safety = u2.json().get("data", {}).get("safety", safety)
                blob += u2.text.lower()
            else:
                checks[3].fail("no milestone")
                checks[4].fail("skipped")

            tr = client.get(f"{base}/api/v1/orders/{order_id}/timeline", headers=headers)
            types = [i.get("type") for i in tr.json().get("data", {}).get("items", [])]
            if any(t in types for t in ("production_milestone_updated", "production_milestone_completed", "production_milestones_created")):
                checks[5].pass_(",".join(types))
            else:
                checks[5].fail(str(types))

            checks[6].pass_() if safety.get("shipment_created") is False else checks[6].fail(str(safety))
            checks[7].pass_() if safety.get("supplier_notified") is False else checks[7].fail(str(safety))
            checks[8].pass_() if safety.get("customer_notified") is False else checks[8].fail(str(safety))

            if any(p in blob for p in FORBIDDEN):
                checks[9].fail("forbidden text")
            else:
                checks[9].pass_()

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
