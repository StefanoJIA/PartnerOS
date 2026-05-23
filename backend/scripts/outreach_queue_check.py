"""D5.2.5 read-only manual outreach queue check."""

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

FORBIDDEN_PHRASES = [
    "guaranteed delivery",
    "guaranteed lowest price",
    "lowest price guaranteed",
    "in stock now",
    "certified unless",
]

SEGMENT_TARGETS = {
    "Ergo Sit Stand Workspace": "lift_system_signal",
    "Healthcare Lab Workspace": "medical_vertical",
    "Contract Project Interiors": "project_based_furniture",
}


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


def _find_company(client: httpx.Client, headers: dict[str, str], name: str) -> dict | None:
    r = client.get(f"{BASE}/api/companies", headers=headers, params={"q": name.split()[0], "limit": 20})
    if r.status_code != 200:
        return None
    for item in r.json().get("items", []):
        if item.get("company_name") == name:
            return item
    return None


def _lead_for_company(client: httpx.Client, headers: dict[str, str], company_id: str) -> dict | None:
    r = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 100})
    if r.status_code != 200:
        return None
    for lead in r.json().get("items", []):
        if lead.get("company_id") == company_id:
            return lead
    return None


def _scan_draft_text(text: str) -> list[str]:
    lower = text.lower()
    hits = []
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            hits.append(phrase)
    if " in stock" in lower and "no stock" not in lower and "not in stock" not in lower:
        hits.append("in stock (availability claim)")
    return hits


def run() -> int:
    global BASE
    BASE = log_backend_base_url()
    checks = [
        Check("leads count"),
        Check("lift segment lead"),
        Check("medical segment lead"),
        Check("project segment lead"),
        Check("next action"),
        Check("touchpoint"),
        Check("outreach draft API"),
        Check("draft safety wording"),
    ]

    try:
        with httpx.Client(timeout=45.0) as client:
            headers = _login(client)
            if not headers:
                for c in checks:
                    c.fail("login failed")
                _print(checks)
                return 1

            lr = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 100})
            total = lr.json().get("total", 0) if lr.status_code == 200 else 0
            if total >= 5:
                checks[0].pass_(f"{total} leads")
            else:
                checks[0].warn(f"{total} leads (expected ≥5 for full demo)")

            for idx, (company_name, seg) in enumerate(SEGMENT_TARGETS.items(), start=1):
                company = _find_company(client, headers, company_name)
                if not company:
                    checks[idx].fail(f"company missing: {company_name}")
                    continue
                lead = _lead_for_company(client, headers, company["id"])
                if not lead:
                    checks[idx].fail("no lead")
                    continue
                wf = client.get(
                    f"{BASE}/api/a-domain/leads/{lead['id']}/workflow",
                    headers=headers,
                )
                segs = wf.json().get("market_fit_segments", []) if wf.status_code == 200 else []
                if seg in segs:
                    checks[idx].pass_(seg)
                else:
                    checks[idx].fail(f"got {segs}")

            has_next = False
            has_touch = False
            if lr.status_code == 200:
                for lead in lr.json().get("items", []):
                    na = (lead.get("next_action") or "").strip()
                    if na:
                        has_next = True
                    ix = client.get(
                        f"{BASE}/api/objects/lead/{lead['id']}/interactions",
                        headers=headers,
                        params={"limit": 1},
                    )
                    if ix.status_code == 200 and ix.json().get("total", 0) > 0:
                        has_touch = True

            if has_next:
                checks[4].pass_()
            else:
                checks[4].fail("set next action in Lead Intelligence")

            if has_touch:
                checks[5].pass_()
            else:
                checks[5].fail("log touchpoint via Mark as Sent or form")

            ergo = _find_company(client, headers, "Ergo Sit Stand Workspace")
            if ergo:
                dr = client.get(
                    f"{BASE}/api/a-domain/outreach-draft",
                    headers=headers,
                    params={
                        "company_id": ergo["id"],
                        "channel": "linkedin_connect",
                        "product_focus": "hosun_lifting",
                    },
                )
                if dr.status_code == 200:
                    checks[6].pass_("Ergo linkedin_connect")
                    body = dr.json()
                    blob = " ".join(
                        filter(
                            None,
                            [
                                body.get("linkedin_connect_note"),
                                body.get("email_subject"),
                                body.get("email_body"),
                            ],
                        )
                    )
                    hits = _scan_draft_text(blob)
                    if hits:
                        checks[7].fail(", ".join(hits))
                    else:
                        checks[7].pass_("no forbidden promise phrases")
                elif dr.status_code == 404:
                    checks[6].warn("API 404 — restart uvicorn for /outreach-draft route")
                    offline = generate_outreach_draft(
                        company_name=ergo["company_name"],
                        segments=["lift_system_signal"],
                        channel="linkedin_connect",
                        product_focus="hosun_lifting",
                    )
                    blob = offline.linkedin_connect_note or ""
                    hits = _scan_draft_text(blob)
                    if hits:
                        checks[7].fail("offline: " + ", ".join(hits))
                    else:
                        checks[7].pass_("offline template OK (API unavailable)")
                else:
                    checks[6].fail(f"HTTP {dr.status_code}")
                    checks[7].fail("skipped")
            else:
                checks[6].fail("Ergo company missing")
                checks[7].fail("skipped")

            if checks[7].detail == "":
                offline = generate_outreach_draft(
                    company_name="Test Co",
                    segments=["lift_system_signal"],
                    channel="email_intro",
                    product_focus="hosun_lifting",
                )
                offline_text = offline.email_body or ""
                off_hits = _scan_draft_text(offline_text)
                if off_hits and checks[7].ok:
                    checks[7].fail("offline template: " + ", ".join(off_hits))

    except httpx.ConnectError:
        for c in checks:
            if not c.detail:
                c.fail(f"backend down ({BASE})")
        _print(checks)
        return 1

    _print(checks)
    failed = [c for c in checks if not c.ok]
    warned = [c for c in checks if c.ok and c.detail.startswith("WARN:")]
    if failed:
        print("\nResult: FAIL")
        return 1
    if warned:
        print("\nResult: WARN")
        return 0
    print("\nResult: PASS")
    return 0


def _print(checks: list[Check]) -> None:
    print("D5.2.5 Outreach Queue Check")
    for c in checks:
        print(c.line())


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
