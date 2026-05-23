"""D5.18 quote handoff check."""

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
    r = client.post(
        f"{base}/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _find_handoff_lead(client: httpx.Client, base: str, headers: dict[str, str]) -> str | None:
    r = client.get(f"{base}/api/a-domain/quote-handoff-board", headers=headers)
    if r.status_code == 200:
        for row in r.json().get("rows") or []:
            if row.get("quote_readiness") in ("almost_ready", "ready"):
                return row.get("lead_id")
    r2 = client.get(f"{base}/api/leads", headers=headers, params={"limit": 50})
    if r2.status_code != 200:
        return None
    items = r2.json().get("items") or []
    return items[0]["id"] if items else None


def main() -> int:
    base = log_backend_base_url()
    checks = [
        Check("handoff API"),
        Check("status"),
        Check("route"),
        Check("missing info limit"),
        Check("safety flags"),
        Check("no forbidden promises"),
    ]

    try:
        with httpx.Client(timeout=60.0) as client:
            headers = _login(client, base)
            if not headers:
                checks[0].fail("login failed")
            else:
                lead_id = _find_handoff_lead(client, base, headers)
                if not lead_id:
                    checks[0].fail("no lead found")
                else:
                    r = client.get(
                        f"{base}/api/a-domain/leads/{lead_id}/quote-handoff-brief",
                        headers=headers,
                    )
                    if r.status_code != 200:
                        checks[0].fail(f"HTTP {r.status_code}")
                    else:
                        checks[0].pass_(f"HTTP {r.status_code}")
                        body = r.json()
                        if body.get("handoff_status"):
                            checks[1].pass_(body["handoff_status"])
                        else:
                            checks[1].fail("no status")
                        routes = body.get("recommended_partner_route") or []
                        if routes:
                            checks[2].pass_(",".join(routes[:2]))
                        else:
                            checks[2].fail("no route")
                        missing = body.get("missing_customer_info") or []
                        if len(missing) <= 6:
                            checks[3].pass_(f"count={len(missing)}")
                        else:
                            checks[3].fail(f"count={len(missing)}")
                        safety = body.get("safety") or {}
                        if (
                            safety.get("quote_created") is False
                            and safety.get("pricing_generated") is False
                            and safety.get("automatic_sending_enabled") is False
                        ):
                            checks[4].pass_("all false")
                        else:
                            checks[4].fail(str(safety))
                        text = (
                            (body.get("quote_handoff_brief_text") or "")
                            + " ".join(body.get("supplier_preparation_notes") or [])
                        ).lower()
                        bad = [p for p in FORBIDDEN if p in text]
                        if bad:
                            checks[5].fail(", ".join(bad))
                        else:
                            checks[5].pass_("clean")
    except Exception as e:
        checks[0].fail(str(e))

    print("D5.18 Quote Handoff Check")
    for c in checks:
        print(c.line())
    failed = [c for c in checks if not c.ok]
    print(f"\nResult: {'PASS' if not failed else 'FAIL'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
