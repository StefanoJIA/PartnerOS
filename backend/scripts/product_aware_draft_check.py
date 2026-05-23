"""D5.15 product-aware draft check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url
from app.services.a_domain.outreach_templates import LINKEDIN_MAX

BASE = get_backend_base_url()
FORBIDDEN = (
    "guaranteed price",
    "lowest price guaranteed",
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


def _find_lift_lead(client: httpx.Client, headers: dict[str, str]) -> str | None:
    r = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 100})
    if r.status_code != 200:
        return None
    for item in r.json().get("items") or []:
        name = (item.get("lead_name") or "").lower()
        if "ergo" in name or "sit stand" in name or DEMO_COMPANY.lower() in name:
            return item.get("id")
    items = r.json().get("items") or []
    return items[0]["id"] if items else None


def main() -> int:
    log_backend_base_url()
    print("D5.15 Product-Aware Draft Check")
    checks = [
        Check("draft API"),
        Check("lifting system context"),
        Check("questions"),
        Check("linkedin length"),
        Check("safety flags"),
        Check("no forbidden promises"),
    ]

    try:
        with httpx.Client(timeout=30.0) as client:
            headers = _login(client)
            if not headers:
                checks[0].fail("login failed")
            else:
                lead_id = _find_lift_lead(client, headers)
                if not lead_id:
                    checks[0].fail("no lead found")
                else:
                    r = client.post(
                        f"{BASE}/api/a-domain/leads/{lead_id}/product-aware-draft",
                        headers=headers,
                        json={
                            "channel": "email_intro",
                            "draft_purpose": "product_discovery",
                            "tone": "warm",
                            "language": "en",
                        },
                    )
                    if r.status_code != 200:
                        checks[0].fail(f"HTTP {r.status_code}")
                    else:
                        checks[0].pass_(f"HTTP {r.status_code}")
                        body = r.json()
                        text = (
                            (body.get("subject") or "")
                            + (body.get("body") or "")
                            + (body.get("linkedin_note") or "")
                        ).lower()
                        focus = body.get("source_context", {}).get("product_focus") or []
                        if "lifting" in text or "adjustable" in text or "hosun" in str(focus).lower():
                            checks[1].pass_("lifting context")
                        else:
                            checks[1].fail("no lifting context")
                        if body.get("questions"):
                            checks[2].pass_(f"count={len(body['questions'])}")
                        else:
                            checks[2].fail("no questions")
                        r_li = client.post(
                            f"{BASE}/api/a-domain/leads/{lead_id}/product-aware-draft",
                            headers=headers,
                            json={"channel": "linkedin_connect", "draft_purpose": "product_discovery"},
                        )
                        if r_li.status_code == 200:
                            note = r_li.json().get("linkedin_note") or ""
                            if len(note) <= LINKEDIN_MAX:
                                checks[3].pass_(f"{len(note)} chars")
                            else:
                                checks[3].fail(f"{len(note)} chars")
                        else:
                            checks[3].fail(f"linkedin HTTP {r_li.status_code}")
                        safety = body.get("safety") or {}
                        if (
                            safety.get("quote_created") is False
                            and safety.get("pricing_generated") is False
                            and safety.get("automatic_sending_enabled") is False
                        ):
                            checks[4].pass_("all false")
                        else:
                            checks[4].fail(str(safety))
                        bad = [p for p in FORBIDDEN if p in text]
                        if bad:
                            checks[5].fail(", ".join(bad))
                        else:
                            checks[5].pass_("clean")
    except Exception as e:
        checks[0].fail(str(e))

    for c in checks:
        print(c.line())
    failed = [c for c in checks if not c.ok]
    print(f"\nResult: {'PASS' if not failed else 'FAIL'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
