"""D5.2.2 read-only smoke check — internal MVP demo readiness.

Requires backend running at http://127.0.0.1:8000 (default).
Does not write to the database unless --seed-demo is passed (not implemented; use seed scripts).
"""

from __future__ import annotations

import argparse
import sys

import httpx

BASE = "http://127.0.0.1:8000"

COMPANY_NAMES = [
    "New England Office Furniture Dealer",
    "Ergo Sit Stand Workspace",
    "Contract Project Interiors",
    "Campus Learning Furniture",
    "Healthcare Lab Workspace",
]

SEGMENT_TARGETS = {
    "Healthcare Lab Workspace": "medical_vertical",
    "Contract Project Interiors": "project_based_furniture",
    "Ergo Sit Stand Workspace": "lift_system_signal",
}


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


def _find_lead_by_company(client: httpx.Client, headers: dict[str, str], company_substr: str) -> dict | None:
    lr = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 100})
    if lr.status_code != 200:
        return None
    for lead in lr.json().get("items", []):
        name = lead.get("lead_name") or ""
        if company_substr in name:
            return lead
    return None


def run_checks(seed_demo: bool) -> int:
    if seed_demo:
        print("Note: --seed-demo is not implemented. Run: python -m app.scripts.seed")
        return 1

    checks: list[Check] = []
    c_health = Check("backend health")
    c_db = Check("database ready")
    c_readiness = Check("readiness")
    c_manifest = Check("manifest")
    c_companies = Check("demo companies")
    c_contacts = Check("contacts")
    c_healthcare = Check("healthcare segment")
    c_project = Check("project segment")
    c_lifting = Check("lifting segment")
    c_enrichment = Check("enrichment")
    c_next_action = Check("next action")
    checks.extend(
        [
            c_health,
            c_db,
            c_readiness,
            c_manifest,
            c_companies,
            c_contacts,
            c_healthcare,
            c_project,
            c_lifting,
            c_enrichment,
            c_next_action,
        ]
    )

    try:
        with httpx.Client(timeout=30.0) as client:
            hr = client.get(f"{BASE}/health")
            if hr.status_code == 200:
                body = hr.json()
                if body.get("status") in ("ok", "degraded"):
                    c_health.pass_(body.get("status", ""))
                else:
                    c_health.fail(f"status={body.get('status')}")
                if body.get("database_status") == "ready":
                    c_db.pass_()
                else:
                    c_db.fail(f"database_status={body.get('database_status')}")
            else:
                c_health.fail(f"HTTP {hr.status_code}")
                c_db.fail("health unavailable")

            rr = client.get(f"{BASE}/api/v1/system/readiness")
            if rr.status_code == 200:
                env = rr.json()
                data = env.get("data") or {}
                if env.get("ok") and data.get("database_ready"):
                    c_readiness.pass_()
                else:
                    c_readiness.fail("database not ready in envelope")
            else:
                c_readiness.fail(f"HTTP {rr.status_code}")

            mr = client.get(f"{BASE}/api/v1/portal/manifest")
            if mr.status_code == 200:
                menv = mr.json()
                mdata = menv.get("data") or {}
                mods = mdata.get("modules") or []
                caps = mdata.get("capabilities") or []
                if menv.get("ok") and mods and caps:
                    c_manifest.pass_(f"{len(mods)} modules")
                else:
                    c_manifest.fail("missing modules or capabilities")
            else:
                c_manifest.fail(f"HTTP {mr.status_code}")

            headers = _login(client)
            if not headers:
                for c in checks[4:]:
                    c.fail("login failed — run seed?")
            else:
                cr = client.get(f"{BASE}/api/companies", headers=headers, params={"limit": 100})
                found = 0
                if cr.status_code == 200:
                    names = {i.get("company_name") for i in cr.json().get("items", [])}
                    for n in COMPANY_NAMES:
                        if n in names:
                            found += 1
                if found >= 5:
                    c_companies.pass_(f"{found} UAT companies")
                else:
                    c_companies.fail(
                        f"found {found}/5 — run seed or UAT script (docs/records/demo_script_20260523.md)"
                    )

                ctr = client.get(f"{BASE}/api/contacts", headers=headers, params={"limit": 50})
                total_contacts = ctr.json().get("total", 0) if ctr.status_code == 200 else 0
                if total_contacts >= 3:
                    c_contacts.pass_(f"{total_contacts} contacts")
                else:
                    c_contacts.fail(f"only {total_contacts} contacts")

                for company_substr, segment_key in SEGMENT_TARGETS.items():
                    chk = {
                        "Healthcare Lab Workspace": c_healthcare,
                        "Contract Project Interiors": c_project,
                        "Ergo Sit Stand Workspace": c_lifting,
                    }[company_substr]
                    lead = _find_lead_by_company(client, headers, company_substr)
                    if not lead:
                        chk.fail(f"no lead for {company_substr}")
                        continue
                    wf = client.get(
                        f"{BASE}/api/a-domain/leads/{lead['id']}/workflow",
                        headers=headers,
                    )
                    if wf.status_code != 200:
                        chk.fail(f"workflow HTTP {wf.status_code}")
                        continue
                    segs = wf.json().get("market_fit_segments") or []
                    if segment_key in segs:
                        chk.pass_(segment_key)
                    else:
                        chk.fail(f"got {segs}, expected {segment_key}")

                enrichment_total = 0
                for name in COMPANY_NAMES[:3]:
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
                    )
                    if er.status_code == 200:
                        enrichment_total += er.json().get("total", 0)
                if enrichment_total >= 1:
                    c_enrichment.pass_(f"{enrichment_total} run(s)")
                else:
                    c_enrichment.fail("no enrichment runs — run enrichment on Ergo in UI")

                has_next = False
                lr = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 50})
                if lr.status_code == 200:
                    for lead in lr.json().get("items", []):
                        wf = client.get(
                            f"{BASE}/api/a-domain/leads/{lead['id']}/workflow",
                            headers=headers,
                        )
                        if wf.status_code != 200:
                            continue
                        w = wf.json()
                        na = (w.get("lead") or {}).get("next_action") or ""
                        touchpoints = w.get("touchpoints") or w.get("interactions") or []
                        if na.strip() or len(touchpoints) >= 1:
                            has_next = True
                            break
                if has_next:
                    c_next_action.pass_()
                else:
                    c_next_action.fail("no next_action or touchpoint — add via Lead Intelligence UI")

    except httpx.ConnectError:
        for c in checks:
            if not c.ok and not c.detail:
                c.fail("backend not reachable at :8000")
        print("D5.2.2 Smoke Check")
        for c in checks:
            print(c.line())
        print("\nResult: FAIL")
        print("Hint: start backend — cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return 1

    print("D5.2.2 Smoke Check")
    for c in checks:
        print(c.line())
    all_ok = all(c.ok for c in checks)
    print(f"\nResult: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="D5.2.2 internal MVP smoke check (read-only)")
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Not implemented — use python -m app.scripts.seed instead",
    )
    args = parser.parse_args()
    sys.exit(run_checks(seed_demo=args.seed_demo))


if __name__ == "__main__":
    main()
