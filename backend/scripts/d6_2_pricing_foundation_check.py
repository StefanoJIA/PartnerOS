"""D6.2 pricing foundation smoke check."""

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


def _safety_ok(payload: dict) -> bool:
    safety = payload.get("safety") or {}
    return (
        safety.get("quote_created") is False
        and safety.get("automatic_sending_enabled") is False
        and safety.get("inventory_promised") is False
        and safety.get("certification_promised") is False
        and safety.get("lead_time_promised") is False
    )


def main() -> int:
    base = log_backend_base_url()
    print("D6.2 Pricing Foundation Check")
    checks = [
        Check("products API"),
        Check("partners/products"),
        Check("fx latest"),
        Check("pricing preview"),
        Check("safety flags"),
        Check("no forbidden promises"),
    ]

    try:
        with httpx.Client(timeout=60.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                for c in checks:
                    print(c.line())
                print("Result: FAIL")
                return 1

            r = client.get(f"{base}/api/v1/products", headers=headers, params={"limit": 5})
            if r.status_code != 200 or not r.json().get("ok"):
                checks[0].fail(f"HTTP {r.status_code}")
            else:
                checks[0].pass_()

            data = r.json().get("data") or {}
            items = data.get("items") or []
            if not items:
                checks[1].fail("no products — run seed_quote_catalog.py --apply --confirm")
            else:
                checks[1].pass_(f"{len(items)} product(s)")

            fx = client.get(f"{base}/api/v1/fx-rates/latest", headers=headers, params={"base": "USD", "quote": "CNY"})
            if fx.status_code != 200 or not fx.json().get("ok"):
                checks[2].fail(f"HTTP {fx.status_code}")
            else:
                checks[2].pass_()

            if not items:
                checks[3].fail("no product for preview")
                checks[4].fail("skipped")
                checks[5].fail("skipped")
            else:
                pid = items[0]["id"]
                prev = client.post(
                    f"{base}/api/v1/quotes/pricing/preview",
                    headers=headers,
                    json={
                        "product_id": pid,
                        "quantity": 100,
                        "incoterm": "FOB",
                        "pricing_strategy": "volume",
                    },
                )
                if prev.status_code != 200 or not prev.json().get("ok"):
                    checks[3].fail(f"HTTP {prev.status_code}")
                else:
                    body = prev.json().get("data") or {}
                    checks[3].pass_(f"source={body.get('source')}")
                    if _safety_ok(body):
                        checks[4].pass_()
                    else:
                        checks[4].fail("safety flags")
                    blob = str(body)
                    if any(p in blob.lower() for p in FORBIDDEN):
                        checks[5].fail("forbidden phrase")
                    else:
                        checks[5].pass_()
    except httpx.ConnectError:
        for c in checks:
            if not c.ok:
                c.fail(f"cannot connect to {get_backend_base_url()}")

    for c in checks:
        print(c.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
