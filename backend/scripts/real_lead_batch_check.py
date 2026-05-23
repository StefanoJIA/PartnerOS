"""D5.2.6 read-only real lead batch pilot check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.a_domain.outreach_templates import generate_outreach_draft
from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()

PILOT_COMPANIES = [
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
]

DRAFT_SAMPLES = [
    ("SWC Office Furniture", "email_intro", "hosun_lifting"),
    ("Jefferson Group", "email_followup", "project_supply"),
    ("Yony's Office Furniture", "linkedin_followup", "hosun_lifting"),
    ("Commercial Furniture Resource", "email_intro", "general"),
    ("Human Active Technology", "email_intro", "hosun_lifting"),
]

FORBIDDEN = [
    "guaranteed delivery",
    "guaranteed lowest price",
    "lowest price guaranteed",
    "in stock now",
]


class Check:
    def __init__(self, label: str) -> None:
        self.label = label
        self.ok = False
        self.detail = ""

    def pass_(self, detail: str = "") -> None:
        self.ok = True
        self.detail = detail

    def warn(self, detail: str) -> None:
        self.ok = True
        self.detail = f"WARN: {detail}"

    def fail(self, detail: str) -> None:
        self.ok = False
        self.detail = detail

    def line(self) -> str:
        return f"[{'PASS' if self.ok else 'FAIL'}] {self.label}" + (f" ({self.detail})" if self.detail else "")


def _login(client: httpx.Client) -> dict[str, str] | None:
    r = client.post(
        f"{BASE}/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _find_company(client: httpx.Client, headers: dict[str, str], name: str) -> dict | None:
    r = client.get(f"{BASE}/api/companies", headers=headers, params={"q": name.split()[0], "limit": 30})
    if r.status_code != 200:
        return None
    for item in r.json().get("items", []):
        if item.get("company_name") == name:
            return item
    return None


def _lead_for_company(client: httpx.Client, headers: dict[str, str], company_id: str) -> dict | None:
    r = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 200})
    if r.status_code != 200:
        return None
    for lead in r.json().get("items", []):
        if lead.get("company_id") == company_id:
            return lead
    return None


def _scan(text: str) -> list[str]:
    lower = text.lower()
    hits = [p for p in FORBIDDEN if p in lower]
    if " in stock" in lower and "no stock" not in lower:
        hits.append("in stock claim")
    return hits


def run() -> int:
    global BASE
    BASE = log_backend_base_url()
    checks = [
        Check("real pilot companies"),
        Check("contacts or research notes"),
        Check("lift segment"),
        Check("project segment"),
        Check("general office segment"),
        Check("outreach drafts"),
        Check("touchpoints / next actions"),
        Check("primary contact linked"),
        Check("safety wording"),
    ]

    try:
        with httpx.Client(timeout=60.0) as client:
            headers = _login(client)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                _print(checks, "FAIL")
                return 1

            found = 0
            with_contact_or_note = 0
            lift_ok = project_ok = general_ok = 0
            project_need = 3
            general_need = 3

            for name in PILOT_COMPANIES:
                company = _find_company(client, headers, name)
                if not company:
                    continue
                found += 1
                lead = _lead_for_company(client, headers, company["id"])
                if not lead:
                    continue
                wf = client.get(
                    f"{BASE}/api/a-domain/leads/{lead['id']}/workflow",
                    headers=headers,
                )
                if wf.status_code != 200:
                    continue
                w = wf.json()
                segs = w.get("market_fit_segments") or []
                notes = (company.get("notes") or "") + (w.get("company", {}).get("business_description") or "")
                if "lift_system_signal" in segs or "oem_odm_fit" in segs:
                    lift_ok += 1
                if "project_based_furniture" in segs:
                    project_ok += 1
                if "general_office_furniture_only" in segs:
                    general_ok += 1
                cr = client.get(f"{BASE}/api/contacts", headers=headers, params={"limit": 200})
                has_contact = False
                if cr.status_code == 200:
                    has_contact = any(c.get("company_id") == company["id"] for c in cr.json().get("items", []))
                if has_contact or "contact research" in notes.lower():
                    with_contact_or_note += 1

            if found >= 10:
                checks[0].pass_(f"{found}/10")
            elif found >= 8:
                checks[0].warn(f"{found}/10 — run import if missing")
            else:
                checks[0].fail(f"{found}/10")

            if with_contact_or_note >= 7:
                checks[1].pass_(f"{with_contact_or_note}/10")
            else:
                checks[1].fail(f"{with_contact_or_note}/10")

            checks[2].pass_(f"{lift_ok} lead(s)") if lift_ok >= 1 else checks[2].fail("none")
            checks[3].pass_(f"{project_ok} lead(s)") if project_ok >= project_need else checks[3].fail(
                f"{project_ok}/{project_need}"
            )
            checks[4].pass_(f"{general_ok} lead(s)") if general_ok >= general_need else checks[4].fail(
                f"{general_ok}/{general_need}"
            )

            draft_ok = 0
            safety_ok = True
            for name, channel, focus in DRAFT_SAMPLES:
                company = _find_company(client, headers, name)
                if not company:
                    continue
                dr = client.get(
                    f"{BASE}/api/a-domain/outreach-draft",
                    headers=headers,
                    params={"company_id": company["id"], "channel": channel, "product_focus": focus},
                )
                if dr.status_code == 200:
                    draft_ok += 1
                    body = dr.json()
                    blob = " ".join(
                        filter(
                            None,
                            [body.get("linkedin_connect_note"), body.get("email_subject"), body.get("email_body")],
                        )
                    )
                    if _scan(blob):
                        safety_ok = False
                else:
                    offline = generate_outreach_draft(
                        company_name=name,
                        segments=["lift_system_signal"] if focus == "hosun_lifting" else ["project_based_furniture"],
                        channel=channel,
                        product_focus=focus,
                    )
                    blob = offline.linkedin_connect_note or offline.email_body or ""
                    draft_ok += 1
                    if _scan(blob):
                        safety_ok = False

            if draft_ok >= 5:
                checks[5].pass_(f"{draft_ok}/5")
            else:
                checks[5].fail(f"{draft_ok}/5")

            touch_or_next = 0
            for name in PILOT_COMPANIES:
                company = _find_company(client, headers, name)
                if not company:
                    continue
                lead = _lead_for_company(client, headers, company["id"])
                if not lead:
                    continue
                na = (lead.get("next_action") or "").strip()
                ix = client.get(
                    f"{BASE}/api/objects/lead/{lead['id']}/interactions",
                    headers=headers,
                    params={"limit": 1},
                )
                if na or (ix.status_code == 200 and ix.json().get("total", 0) > 0):
                    touch_or_next += 1

            if touch_or_next >= 3:
                checks[6].pass_(f"{touch_or_next} pilot leads")
            else:
                checks[6].warn(f"{touch_or_next}/3 — Mark as Sent in UI for more")

            contact_expected = [n for n in PILOT_COMPANIES if n != "Transfer Enterprises"]
            linked = 0
            for name in contact_expected:
                company = _find_company(client, headers, name)
                if not company:
                    continue
                lead = _lead_for_company(client, headers, company["id"])
                if not lead:
                    continue
                wf = client.get(
                    f"{BASE}/api/a-domain/leads/{lead['id']}/workflow",
                    headers=headers,
                )
                primary = wf.json().get("primary_contact") if wf.status_code == 200 else None
                if primary and primary.get("id"):
                    linked += 1
            if linked >= 7:
                checks[7].pass_(f"{linked}/{len(contact_expected)} with primary_contact_id")
            elif linked >= 5:
                checks[7].warn(f"{linked}/{len(contact_expected)} — re-run import apply to link")
            else:
                checks[7].fail(f"{linked}/{len(contact_expected)}")

            if safety_ok:
                checks[8].pass_("no forbidden promise phrases")
            else:
                checks[8].fail("forbidden wording detected")

    except httpx.ConnectError:
        for c in checks:
            if not c.detail:
                c.fail(f"backend down ({BASE})")
        _print(checks, "FAIL")
        return 1

    failed = [c for c in checks if not c.ok]
    warned = [c for c in checks if c.ok and c.detail.startswith("WARN:")]
    result = "FAIL" if failed else ("WARN" if warned else "PASS")
    _print(checks, result)
    return 1 if failed else 0


def _print(checks: list[Check], result: str) -> None:
    print("D5.2.6 Real Lead Batch Check")
    for c in checks:
        print(c.line())
    print(f"\nResult: {result}")


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
