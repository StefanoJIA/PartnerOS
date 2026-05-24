"""D6.3 Quote CRUD smoke check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url

FORBIDDEN = (
    "guaranteed price",
    "in stock",
    "certified for",
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
    print("D6.3 Quote CRUD Check")
    checks = [
        Check("products exist"),
        Check("fx exists"),
        Check("create quote"),
        Check("quote_number"),
        Check("line item priced"),
        Check("totals"),
        Check("version v1"),
        Check("mark-ready"),
        Check("mark-sent manual only"),
        Check("no automatic sending"),
        Check("no forbidden promises"),
    ]
    quote_id = None

    try:
        with httpx.Client(timeout=60.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                print("\n".join(c.line() for c in checks))
                print("Result: FAIL")
                return 1

            pr = client.get(f"{base}/api/v1/products?limit=5", headers=headers)
            if pr.status_code == 200 and (pr.json().get("data") or {}).get("total", 0) > 0:
                checks[0].pass_(f"{pr.json()['data']['total']} product(s)")
                product_id = pr.json()["data"]["items"][0]["id"]
            else:
                checks[0].fail(f"HTTP {pr.status_code}")
                product_id = None

            fx = client.get(f"{base}/api/v1/fx-rates/latest?base=USD&quote=CNY", headers=headers)
            checks[1].pass_("latest fx") if fx.status_code == 200 else checks[1].fail(f"HTTP {fx.status_code}")

            if not product_id:
                for c in checks[2:]:
                    c.fail("no product")
            else:
                cr = client.post(
                    f"{base}/api/v1/quotes",
                    headers=headers,
                    json={
                        "line_items": [
                            {
                                "product_id": product_id,
                                "quantity": 50,
                                "incoterm": "FOB",
                                "pricing_strategy": "volume",
                            }
                        ],
                        "bill_to": {"company": "Smoke Test Co"},
                    },
                )
                if cr.status_code == 201:
                    data = cr.json()["data"]
                    quote_id = data["id"]
                    checks[2].pass_(quote_id[:8])
                    checks[3].pass_(data.get("quote_number", ""))
                    lines = data.get("line_items") or []
                    if lines and float(lines[0].get("final_unit_price", 0)) > 0:
                        checks[4].pass_(f"source={lines[0].get('pricing_source')}")
                    else:
                        checks[4].fail("no priced line")
                    gt = float(data.get("grand_total", 0))
                    checks[5].pass_(f"grand_total={gt}") if gt > 0 else checks[5].fail("zero total")
                    if (data.get("versions_count") or 0) >= 1:
                        checks[6].pass_("v1")
                    else:
                        vr = client.get(f"{base}/api/v1/quotes/{quote_id}/versions", headers=headers)
                        if vr.status_code == 200 and vr.json()["data"]["items"]:
                            checks[6].pass_("v1 via API")
                        else:
                            checks[6].fail("no version")
                    mr = client.post(f"{base}/api/v1/quotes/{quote_id}/mark-ready", headers=headers)
                    st = data.get("status")
                    if mr.status_code == 200:
                        checks[7].pass_()
                    elif st == "ready_to_send" and mr.status_code == 400:
                        checks[7].pass_("already ready_to_send")
                    else:
                        checks[7].fail(f"HTTP {mr.status_code}")
                    ms = client.post(
                        f"{base}/api/v1/quotes/{quote_id}/mark-sent",
                        headers=headers,
                        json={"send_channel": "manual_email"},
                    )
                    if ms.status_code == 200:
                        checks[8].pass_("manual_sent recorded")
                        safety = ms.json()["data"].get("safety") or {}
                        if safety.get("automatic_sending_enabled") is False:
                            checks[9].pass_()
                        else:
                            checks[9].fail("automatic_sending_enabled true")
                    else:
                        checks[8].fail(f"HTTP {ms.status_code}")
                        checks[9].fail("skipped")
                else:
                    checks[2].fail(f"HTTP {cr.status_code} {cr.text[:120]}")
                    for c in checks[3:10]:
                        c.fail("create failed")

            blob = ""
            if quote_id:
                gr = client.get(f"{base}/api/v1/quotes/{quote_id}", headers=headers)
                if gr.status_code == 200:
                    blob = gr.text.lower()
            if blob and not any(p in blob for p in FORBIDDEN):
                checks[10].pass_()
            elif not blob:
                checks[10].fail("no quote payload")
            else:
                checks[10].fail("forbidden phrase found")

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
