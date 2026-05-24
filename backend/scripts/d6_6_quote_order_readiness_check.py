"""D6.6 Quote-to-order readiness smoke check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url

FORBIDDEN = (
    "order created",
    "production started",
    "shipment created",
    "inventory confirmed",
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


def main() -> int:
    base = log_backend_base_url()
    print("D6.6 Quote-to-Order Readiness Check")
    checks = [
        Check("find or create sent quote"),
        Check("pdf export exists"),
        Check("delivery log exists"),
        Check("GET order-readiness"),
        Check("readiness_status present"),
        Check("order_created=false"),
        Check("production_started=false"),
        Check("shipment_created=false"),
        Check("order input contract present"),
        Check("no forbidden promise text"),
    ]
    quote_id = None

    try:
        with httpx.Client(timeout=90.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1

            lr = client.get(f"{base}/api/v1/quotes?limit=30", headers=headers)
            if lr.status_code == 200:
                for item in lr.json()["data"]["items"]:
                    if item.get("status") == "sent":
                        quote_id = item["id"]
                        checks[0].pass_(item.get("quote_number", quote_id[:8]))
                        break

            if not quote_id:
                pr = client.get(f"{base}/api/v1/products?limit=1", headers=headers)
                product_id = pr.json()["data"]["items"][0]["id"] if pr.status_code == 200 and pr.json()["data"]["items"] else None
                if product_id:
                    cr = client.post(
                        f"{base}/api/v1/quotes",
                        headers=headers,
                        json={"line_items": [{"product_id": product_id, "quantity": 10}], "bill_to": {"company": "Readiness Co"}},
                    )
                    if cr.status_code == 201:
                        quote_id = cr.json()["data"]["id"]
                        st = cr.json()["data"]["status"]
                        if st == "internal_review":
                            client.post(f"{base}/api/v1/quotes/{quote_id}/mark-ready", headers=headers)
                        px = client.post(f"{base}/api/v1/quotes/{quote_id}/export-pdf", headers=headers, json={"export_type": "customer_pdf"})
                        export_id = px.json()["data"]["export_id"] if px.status_code == 201 else None
                        ms = client.post(
                            f"{base}/api/v1/quotes/{quote_id}/mark-sent",
                            headers=headers,
                            json={"sent_channel": "email", "pdf_export_id": export_id, "sent_to_company": "Readiness Co"},
                        )
                        if ms.status_code == 200:
                            checks[0].pass_(f"created {quote_id[:8]}")
                        else:
                            checks[0].fail(f"mark-sent HTTP {ms.status_code}")
                    else:
                        checks[0].fail(f"create HTTP {cr.status_code}")
                else:
                    checks[0].fail("no sent quote or product")

            if quote_id:
                er = client.get(f"{base}/api/v1/quotes/{quote_id}/pdf-exports", headers=headers)
                if er.status_code == 200 and er.json()["data"]["items"]:
                    checks[1].pass_()
                else:
                    px = client.post(f"{base}/api/v1/quotes/{quote_id}/export-pdf", headers=headers, json={"export_type": "customer_pdf"})
                    checks[1].pass_() if px.status_code == 201 else checks[1].fail(f"HTTP {px.status_code}")

                dr = client.get(f"{base}/api/v1/quotes/{quote_id}/delivery-logs", headers=headers)
                if dr.status_code == 200 and dr.json()["data"]["items"]:
                    checks[2].pass_()
                else:
                    ms = client.post(
                        f"{base}/api/v1/quotes/{quote_id}/mark-sent",
                        headers=headers,
                        json={"sent_channel": "email", "sent_to_company": "Readiness Co"},
                    )
                    checks[2].pass_() if ms.status_code == 200 else checks[2].fail(f"HTTP {ms.status_code}")

                rr = client.get(f"{base}/api/v1/quotes/{quote_id}/order-readiness", headers=headers)
                if rr.status_code == 200:
                    checks[3].pass_()
                    data = rr.json()["data"]
                    if data.get("readiness_status"):
                        checks[4].pass_(data["readiness_status"])
                    else:
                        checks[4].fail("missing status")
                    safety = data.get("safety") or {}
                    for idx, key in enumerate(("order_created", "production_started", "shipment_created"), start=5):
                        if safety.get(key) is False:
                            checks[idx].pass_()
                        else:
                            checks[idx].fail(str(safety))
                    if data.get("order_input_contract"):
                        checks[8].pass_()
                    else:
                        checks[8].fail("missing contract")
                    blob = rr.text.lower()
                    if not any(p in blob for p in FORBIDDEN):
                        checks[9].pass_()
                    else:
                        checks[9].fail("forbidden phrase")
                else:
                    checks[3].fail(f"HTTP {rr.status_code}")
                    for c in checks[4:]:
                        c.fail("readiness failed")

    except httpx.ConnectError:
        for c in checks:
            c.fail("backend unreachable")
        print("\n".join(c.line() for c in checks))
        print("Result: FAIL")
        return 1

    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
