"""D5.16 read-only real lead UAT check — validates end-to-end API coverage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url
from app.services.a_domain.outreach_templates import LINKEDIN_MAX

FORBIDDEN = (
    "guaranteed price",
    "lowest price guaranteed",
    "in stock",
    "certified for",
    "delivery guaranteed",
    "lead time confirmed",
)

PILOT_COMPANIES = (
    "SWC Office Furniture",
    "Jefferson Group",
    "Yony's Office Furniture",
    "Commercial Furniture Resource",
    "Human Active Technology",
    "OCI Office Concepts Inc.",
    "LABERS Furniture",
    "Overnight Office",
    "Dancker",
    "Transfer Enterprises",
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


def _pick_lead(client: httpx.Client, base: str, headers: dict[str, str]) -> dict | None:
    r = client.get(f"{base}/api/leads", headers=headers, params={"limit": 200})
    if r.status_code != 200:
        return None
    items = r.json().get("items") or []
    if not items:
        return None
    companies = {
        c["id"]: c
        for c in (client.get(f"{base}/api/companies", headers=headers, params={"limit": 200}).json().get("items") or [])
    }
    for lead in items:
        co = companies.get(lead.get("company_id"))
        if co and co.get("company_name") in PILOT_COMPANIES:
            return lead
    return items[0]


def _safety_ok(payload: dict) -> bool:
    safety = payload.get("safety") or {}
    return (
        safety.get("automatic_sending_enabled") is False
        and safety.get("quote_created") is False
        and safety.get("pricing_generated") is False
        and safety.get("inventory_promised") is False
        and safety.get("certification_promised") is False
        and safety.get("lead_time_promised") is False
    )


def run(*, write_test: bool = False) -> int:
    base = log_backend_base_url()
    checks = [
        Check("lead completeness"),
        Check("product opportunity board"),
        Check("product fit"),
        Check("pre-quote brief"),
        Check("product-aware draft"),
        Check("follow-up queue"),
        Check("daily work summary"),
        Check("safety flags"),
    ]

    if write_test:
        print("Note: --write-test ignored — D5.16 check stays read-only.")

    try:
        with httpx.Client(timeout=60.0) as client:
            headers = _login(client, base)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                _print(checks)
                return 1

            r = client.get(f"{base}/api/a-domain/lead-completeness", headers=headers)
            if r.status_code == 200:
                total = (r.json().get("summary") or {}).get("total", 0)
                checks[0].pass_(f"total={total}") if total >= 10 else checks[0].fail(f"total={total}")
            else:
                checks[0].fail(f"HTTP {r.status_code}")

            r = client.get(f"{base}/api/a-domain/product-opportunity-board", headers=headers)
            if r.status_code == 200:
                summary = r.json().get("summary") or {}
                rows = r.json().get("rows") or []
                checks[1].pass_(f"rows={len(rows)} total={summary.get('total', len(rows))}")
            else:
                checks[1].fail(f"HTTP {r.status_code}")

            lead = _pick_lead(client, base, headers)
            if not lead:
                for c in checks[2:]:
                    c.fail("no lead")
                _print(checks)
                return 1

            lead_id = lead["id"]
            r = client.get(f"{base}/api/a-domain/leads/{lead_id}/product-fit", headers=headers)
            if r.status_code == 200 and r.json().get("recommended_product_focus"):
                checks[2].pass_(f"focus={len(r.json()['recommended_product_focus'])}")
            else:
                checks[2].fail(f"HTTP {r.status_code if r.status_code != 200 else 'empty focus'}")

            r = client.get(f"{base}/api/a-domain/leads/{lead_id}/pre-quote-brief", headers=headers)
            if r.status_code == 200 and r.json().get("quote_readiness"):
                checks[3].pass_(r.json()["quote_readiness"])
            else:
                checks[3].fail(f"HTTP {r.status_code}")

            r = client.post(
                f"{base}/api/a-domain/leads/{lead_id}/product-aware-draft",
                headers=headers,
                json={
                    "channel": "email_intro",
                    "draft_purpose": "product_discovery",
                    "tone": "warm",
                    "language": "en",
                },
            )
            draft_body: dict = {}
            if r.status_code == 200:
                draft_body = r.json()
                text = ((draft_body.get("subject") or "") + (draft_body.get("body") or "")).lower()
                bad = [p for p in FORBIDDEN if p in text]
                if draft_body.get("subject") and draft_body.get("body") and not bad:
                    checks[4].pass_("email draft ok")
                else:
                    checks[4].fail("missing fields or forbidden wording")
                r_li = client.post(
                    f"{base}/api/a-domain/leads/{lead_id}/product-aware-draft",
                    headers=headers,
                    json={"channel": "linkedin_connect", "draft_purpose": "product_discovery"},
                )
                if r_li.status_code == 200:
                    note = r_li.json().get("linkedin_note") or ""
                    if len(note) > LINKEDIN_MAX:
                        checks[4].fail(f"linkedin {len(note)} chars")
            else:
                checks[4].fail(f"HTTP {r.status_code}")

            r = client.get(f"{base}/api/a-domain/follow-up-queue", headers=headers)
            if r.status_code == 200:
                summary = r.json().get("summary") or {}
                checks[5].pass_(f"total={summary.get('total', 0)}")
            else:
                checks[5].fail(f"HTTP {r.status_code}")

            r = client.get(f"{base}/api/a-domain/daily-work-summary", headers=headers)
            if r.status_code == 200 and r.json().get("copyable_summary"):
                checks[6].pass_("summary present")
            else:
                checks[6].fail(f"HTTP {r.status_code}")

            tl = client.get(f"{base}/api/a-domain/leads/{lead_id}/timeline", headers=headers)
            timeline_ok = tl.status_code == 200
            if draft_body and _safety_ok(draft_body):
                detail = "all false"
                if timeline_ok:
                    detail += f"; timeline={len(tl.json().get('items') or [])}"
                checks[7].pass_(detail)
            else:
                checks[7].fail(str(draft_body.get("safety")))

    except httpx.ConnectError:
        for c in checks:
            if not c.detail:
                c.fail(f"backend down ({base})")
        _print(checks)
        return 1
    except Exception as e:
        checks[0].fail(str(e))
        _print(checks)
        return 1

    _print(checks)
    failed = [c for c in checks if not c.ok]
    return 1 if failed else 0


def _print(checks: list[Check]) -> None:
    print("D5.16 Real Lead UAT Check")
    for c in checks:
        print(c.line())
    failed = [c for c in checks if not c.ok]
    print(f"\nResult: {'PASS' if not failed else 'FAIL'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="D5.16 read-only real lead UAT check")
    parser.add_argument(
        "--write-test",
        action="store_true",
        help="Reserved; script remains read-only in D5.16",
    )
    args = parser.parse_args()
    sys.exit(run(write_test=args.write_test))


if __name__ == "__main__":
    main()
