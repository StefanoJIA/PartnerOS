"""D6.5 Quote send tracking smoke check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url

FORBIDDEN = (
    "email sent automatically",
    "linkedin sent automatically",
    "guaranteed price",
    "in stock",
    "delivery guaranteed",
    "lead time confirmed",
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
    print("D6.5 Quote Send Tracking Check")
    checks = [
        Check("ready_to_send quote"),
        Check("pdf export exists"),
        Check("mark-sent email"),
        Check("quote status sent"),
        Check("delivery log exists"),
        Check("not converted to order"),
        Check("no automatic sending flags"),
        Check("timeline manual sent"),
        Check("no forbidden promises"),
    ]
    quote_id = None
    export_id = None

    try:
        with httpx.Client(timeout=90.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1

            lr = client.get(f"{base}/api/v1/quotes?limit=20", headers=headers)
            quote_id = None
            if lr.status_code == 200:
                for item in lr.json()["data"]["items"]:
                    if item.get("status") == "ready_to_send" and not item.get("derived_expired"):
                        quote_id = item["id"]
                        checks[0].pass_(item.get("quote_number", quote_id[:8]))
                        break

            if not quote_id:
                pr = client.get(f"{base}/api/v1/quotes?limit=1", headers=headers)
                product_id = None
                pr2 = client.get(f"{base}/api/v1/products?limit=5", headers=headers)
                if pr2.status_code == 200 and pr2.json()["data"]["items"]:
                    product_id = pr2.json()["data"]["items"][0]["id"]
                if product_id:
                    cr = client.post(
                        f"{base}/api/v1/quotes",
                        headers=headers,
                        json={
                            "line_items": [{"product_id": product_id, "quantity": 10}],
                            "bill_to": {"company": "Send Track Co", "name": "Tester"},
                        },
                    )
                    if cr.status_code == 201:
                        quote_id = cr.json()["data"]["id"]
                        st = cr.json()["data"]["status"]
                        if st == "internal_review":
                            client.post(f"{base}/api/v1/quotes/{quote_id}/mark-ready", headers=headers)
                        checks[0].pass_(quote_id[:8])
                    else:
                        checks[0].fail(f"create HTTP {cr.status_code}")
                else:
                    checks[0].fail("no ready quote or product")

            if quote_id:
                er = client.get(f"{base}/api/v1/quotes/{quote_id}/pdf-exports", headers=headers)
                if er.status_code == 200 and er.json()["data"]["items"]:
                    export_id = er.json()["data"]["items"][0]["export_id"]
                    checks[1].pass_("existing export")
                else:
                    px = client.post(
                        f"{base}/api/v1/quotes/{quote_id}/export-pdf",
                        headers=headers,
                        json={"export_type": "customer_pdf"},
                    )
                    if px.status_code == 201:
                        export_id = px.json()["data"]["export_id"]
                        checks[1].pass_("generated")
                    else:
                        checks[1].fail(f"HTTP {px.status_code}")

                payload = {
                    "sent_channel": "email",
                    "sent_to_name": "Smoke Tester",
                    "sent_to_company": "Send Track Co",
                    "pdf_export_id": export_id,
                    "follow_up_date": "2026-06-01",
                    "note": "Recorded manual delivery outside intelliOffice.",
                }
                ms = client.post(f"{base}/api/v1/quotes/{quote_id}/mark-sent", headers=headers, json=payload)
                if ms.status_code == 200:
                    checks[2].pass_()
                    data = ms.json()["data"]
                    if data.get("status") == "sent":
                        checks[3].pass_()
                    else:
                        checks[3].fail(data.get("status"))
                    if data.get("delivery_log", {}).get("id"):
                        checks[4].pass_(data["delivery_log"]["id"][:8])
                    else:
                        checks[4].fail("no delivery_log")
                    safety = data.get("safety") or {}
                    if all(
                        safety.get(k) is False
                        for k in (
                            "automatic_sending_enabled",
                            "email_sent_by_system",
                            "linkedin_sent_by_system",
                            "order_created",
                        )
                    ):
                        checks[6].pass_()
                    else:
                        checks[6].fail(str(safety))
                    if data.get("status") != "converted_to_order":
                        checks[5].pass_()
                    else:
                        checks[5].fail("converted")
                else:
                    checks[2].fail(f"HTTP {ms.status_code} {ms.text[:160]}")
                    for c in checks[3:7]:
                        c.fail("mark-sent failed")

                tl = client.get(f"{base}/api/v1/quotes/{quote_id}/timeline", headers=headers)
                if tl.status_code == 200:
                    types = [i.get("type") for i in tl.json()["data"]["items"]]
                    if "manual_sent" in types:
                        checks[7].pass_()
                    else:
                        checks[7].fail(str(types))
                else:
                    checks[7].fail(f"HTTP {tl.status_code}")

                blob = (ms.text if ms.status_code == 200 else "") + (tl.text if tl.status_code == 200 else "")
                if blob.lower() and not any(p in blob.lower() for p in FORBIDDEN):
                    checks[8].pass_()
                else:
                    checks[8].fail("forbidden phrase or empty")

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
