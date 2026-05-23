"""D5.2.3 read-only pilot workflow check.

Requires live backend (default BACKEND_BASE_URL=http://127.0.0.1:8000). Does not write to the database.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()

UAT_COMPANIES = [
    "New England Office Furniture Dealer",
    "Ergo Sit Stand Workspace",
    "Contract Project Interiors",
    "Campus Learning Furniture",
    "Healthcare Lab Workspace",
]

SEGMENT_BY_COMPANY = {
    "Ergo Sit Stand Workspace": ("lift segment", "lift_system_signal"),
    "Campus Learning Furniture": ("education segment", "education_vertical"),
    "Healthcare Lab Workspace": ("medical segment", "medical_vertical"),
    "Contract Project Interiors": ("project segment", "project_based_furniture"),
}


class Check:
    def __init__(self, label: str) -> None:
        self.label = label
        self.ok = False
        self.detail = ""
        self.hint = ""

    def pass_(self, detail: str = "") -> None:
        self.ok = True
        self.detail = detail

    def fail(self, detail: str, hint: str = "") -> None:
        self.ok = False
        self.detail = detail
        self.hint = hint

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


def _lead_for_company(client: httpx.Client, headers: dict[str, str], substr: str) -> dict | None:
    lr = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 100})
    if lr.status_code != 200:
        return None
    for lead in lr.json().get("items", []):
        if substr in (lead.get("lead_name") or ""):
            return lead
    return None


def _workflow(client: httpx.Client, headers: dict[str, str], lead_id: str) -> dict | None:
    r = client.get(f"{BASE}/api/a-domain/leads/{lead_id}/workflow", headers=headers)
    return r.json() if r.status_code == 200 else None


def run() -> int:
    global BASE
    BASE = log_backend_base_url()
    checks: list[Check] = [
        Check("companies"),
        Check("contacts"),
        Check("lift segment"),
        Check("education segment"),
        Check("medical segment"),
        Check("project segment"),
        Check("enrichment"),
        Check("accepted/rejected review"),
        Check("next action"),
        Check("touchpoint"),
    ]
    c_companies, c_contacts = checks[0], checks[1]
    by_label = {c.label: c for c in checks}
    c_enrich = by_label["enrichment"]
    c_review = by_label["accepted/rejected review"]
    c_next = by_label["next action"]
    c_touch = by_label["touchpoint"]

    try:
        with httpx.Client(timeout=45.0) as client:
            headers = _login(client)
            if not headers:
                for c in checks:
                    c.fail("login failed", "Run: python -m app.scripts.seed")
                _print_report(checks)
                return 1

            cr = client.get(f"{BASE}/api/companies", headers=headers, params={"limit": 100})
            names = {i.get("company_name") for i in cr.json().get("items", [])} if cr.status_code == 200 else set()
            found = sum(1 for n in UAT_COMPANIES if n in names)
            if found >= 5:
                c_companies.pass_(f"{found} companies")
            else:
                c_companies.fail(
                    f"{found}/5 UAT companies",
                    "Create companies via /companies or UAT script",
                )

            ctr = client.get(f"{BASE}/api/contacts", headers=headers, params={"limit": 50})
            total = ctr.json().get("total", 0) if ctr.status_code == 200 else 0
            if total >= 3:
                c_contacts.pass_(f"{total} contacts")
            else:
                c_contacts.fail(f"{total} contacts", "Add contacts on /contacts")

            for company_substr, (label, seg_key) in SEGMENT_BY_COMPANY.items():
                chk = by_label[label]
                lead = _lead_for_company(client, headers, company_substr)
                if not lead:
                    chk.fail(f"no lead for {company_substr}", "Create lead on /lead-intelligence")
                    continue
                wf = _workflow(client, headers, lead["id"])
                segs = (wf or {}).get("market_fit_segments") or []
                if seg_key in segs:
                    chk.pass_(seg_key)
                else:
                    chk.fail(
                        f"got {segs}",
                        f"Update company/lead notes for {company_substr} — see docs/templates/lead_import_template.md",
                    )

            enrichment_runs: list[dict] = []
            for name in UAT_COMPANIES:
                sr = client.get(
                    f"{BASE}/api/companies",
                    headers=headers,
                    params={"q": name.split()[0], "limit": 10},
                )
                if sr.status_code != 200:
                    continue
                match = next(
                    (i for i in sr.json().get("items", []) if i.get("company_name") == name),
                    None,
                )
                if not match:
                    continue
                er = client.get(
                    f"{BASE}/api/companies/{match['id']}/enrichment/runs",
                    headers=headers,
                    params={"limit": 5},
                )
                if er.status_code == 200:
                    enrichment_runs.extend(er.json().get("items", []))

            if enrichment_runs:
                c_enrich.pass_(f"{len(enrichment_runs)} run(s)")
            else:
                c_enrich.fail(
                    "none",
                    "Company detail → Enrichment Panel → run enrichment (Ergo recommended)",
                )

            reviewed = False
            for run in enrichment_runs[:5]:
                dr = client.get(
                    f"{BASE}/api/companies/enrichment/runs/{run['id']}",
                    headers=headers,
                )
                if dr.status_code != 200:
                    continue
                for sug in dr.json().get("suggestions", []):
                    st = (sug.get("review_status") or "").lower()
                    if st in ("accepted", "rejected", "partial"):
                        reviewed = True
                        break
                if reviewed:
                    break
            if reviewed:
                c_review.pass_()
            else:
                c_review.fail(
                    "no reviewed suggestion",
                    "Ergo company → Enrichment Panel → Accept or Reject a suggestion",
                )

            has_next = False
            has_touch = False
            lr = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 50})
            if lr.status_code == 200:
                for lead in lr.json().get("items", []):
                    wf = _workflow(client, headers, lead["id"])
                    if wf:
                        na = ((wf.get("lead") or {}).get("next_action") or "").strip()
                        if na:
                            has_next = True
                    ix = client.get(
                        f"{BASE}/api/objects/lead/{lead['id']}/interactions",
                        headers=headers,
                        params={"limit": 1},
                    )
                    if ix.status_code == 200 and ix.json().get("total", 0) > 0:
                        has_touch = True
                    if has_next and has_touch:
                        break

            if has_next:
                c_next.pass_()
            else:
                c_next.fail(
                    "empty",
                    "/lead-intelligence → set Next Action on a lead",
                )
            if has_touch:
                c_touch.pass_()
            else:
                c_touch.fail(
                    "none",
                    "/lead-intelligence → Record touchpoint form → Save",
                )

    except httpx.ConnectError:
        for c in checks:
            if not c.ok:
                c.fail(f"backend down ({BASE})", "Start uvicorn or set BACKEND_BASE_URL")
        _print_report(checks)
        return 1

    _print_report(checks)
    blocking = [c for c in checks if not c.ok]
    if not blocking:
        return 0
    # Non-critical: education segment missing if Campus not seeded — still FAIL per spec
    return 1


def _print_report(checks: list[Check]) -> None:
    print("D5.2.3 Pilot Workflow Check")
    for c in checks:
        print(c.line())
    failed = [c for c in checks if not c.ok]
    if failed:
        print("\nHints:")
        for c in failed:
            if c.hint:
                print(f"  · {c.label}: {c.hint}")
    all_ok = not failed
    print(f"\nResult: {'PASS' if all_ok else 'FAIL'}")


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
