"""D5.14 pre-quote brief check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()
FORBIDDEN = (
    "guaranteed price",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
)
DEMO_COMPANY = "Ergo Sit Stand Workspace"


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


def _login(client: httpx.Client) -> dict[str, str] | None:
    r = client.post(
        f"{BASE}/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _find_lead_id(client: httpx.Client, headers: dict[str, str]) -> str | None:
    r = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 100})
    if r.status_code != 200:
        return None
    items = r.json().get("items") or []
    for item in items:
        if DEMO_COMPANY.lower() in (item.get("lead_name") or "").lower():
            return item.get("id")
    return items[0]["id"] if items else None


def main() -> int:
    log_backend_base_url()
    print("D5.14 Pre-Quote Brief Check")
    checks = [
        Check("brief API"),
        Check("readiness"),
        Check("checklist"),
        Check("safety flags"),
        Check("no pricing/inventory/certification promises"),
    ]

    try:
        with httpx.Client(timeout=30.0) as client:
            headers = _login(client)
            if not headers:
                checks[0].fail("login failed")
            else:
                lead_id = _find_lead_id(client, headers)
                if not lead_id:
                    checks[0].fail("no lead found")
                else:
                    r = client.get(
                        f"{BASE}/api/a-domain/leads/{lead_id}/pre-quote-brief",
                        headers=headers,
                    )
                    if r.status_code != 200:
                        checks[0].fail(f"HTTP {r.status_code}")
                    else:
                        checks[0].pass_(f"HTTP {r.status_code}")
                        body = r.json()
                        qr = body.get("quote_readiness")
                        sr = body.get("sample_readiness")
                        if qr and sr:
                            checks[1].pass_(f"quote={qr} sample={sr}")
                        else:
                            checks[1].fail("missing readiness")
                        if body.get("quote_preparation_checklist") and body.get("sample_preparation_checklist"):
                            checks[2].pass_("present")
                        else:
                            checks[2].fail("missing checklist")
                        safety = body.get("safety") or {}
                        if (
                            safety.get("quote_created") is False
                            and safety.get("pricing_generated") is False
                            and safety.get("inventory_promised") is False
                            and safety.get("certification_promised") is False
                            and safety.get("lead_time_promised") is False
                            and safety.get("automatic_sending_enabled") is False
                        ):
                            checks[3].pass_("all false")
                        else:
                            checks[3].fail(str(safety))
                        text = (
                            (body.get("pre_quote_brief_text") or "")
                            + (body.get("sample_discussion_brief_text") or "")
                        ).lower()
                        bad = [p for p in FORBIDDEN if p in text]
                        if bad:
                            checks[4].fail(", ".join(bad))
                        else:
                            checks[4].pass_("clean")
    except Exception as e:
        checks[0].fail(str(e))

    for c in checks:
        print(c.line())
    failed = [c for c in checks if not c.ok]
    print(f"\nResult: {'PASS' if not failed else 'FAIL'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
