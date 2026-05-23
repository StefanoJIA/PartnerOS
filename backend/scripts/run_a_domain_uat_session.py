"""One-shot A-domain UAT API session (Part E/F). Writes JSON summary to stdout."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, timedelta

import httpx

BASE = "http://127.0.0.1:8000"
PROXY_BASE = os.environ.get("UAT_FRONTEND_URL", "http://127.0.0.1:5174")
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

COMPANIES = [
    {
        "key": "office_dealer",
        "company_name": "New England Office Furniture Dealer",
        "company_type": "Office Furniture Dealer",
        "website": "https://example.com",
        "business_description": (
            "Regional office furniture dealer serving commercial clients. "
            "office furniture, dealer, commercial furniture, workplace furniture."
        ),
        "product_interest_tags": "office furniture, commercial furniture",
        "notes": "UAT-TC-001 | source_url: https://example.com",
    },
    {
        "key": "ergo_sitstand",
        "company_name": "Ergo Sit Stand Workspace",
        "company_type": "Ergonomic Product Company",
        "website": "https://www.steelcase.com",
        "business_description": (
            "Height adjustable desk and sit-stand desk specialist. "
            "ergonomic workstation, lifting column, adjustable desk frame."
        ),
        "product_interest_tags": "height adjustable desk, lifting columns, adjustable desk frames",
        "notes": "UAT-TC-002",
    },
    {
        "key": "contract_project",
        "company_name": "Contract Project Interiors",
        "company_type": "Interior Design Firm",
        "website": "https://example.org",
        "business_description": (
            "Project furniture contractor for commercial interiors and installation. "
            "project furniture, commercial interiors, installation."
        ),
        "product_interest_tags": "project furniture, contract interiors",
        "notes": "UAT-TC-003",
    },
    {
        "key": "education",
        "company_name": "Campus Learning Furniture",
        "company_type": "Education Furniture Company",
        "website": "https://www.example.edu",
        "business_description": (
            "School furniture supplier for classrooms and training tables. "
            "school furniture, training tables, classroom furniture, education desks."
        ),
        "product_interest_tags": "education desks, school furniture",
        "notes": "UAT-TC-004",
    },
    {
        "key": "healthcare",
        "company_name": "Healthcare Lab Workspace",
        "company_type": "Healthcare Furniture Company",
        "website": "https://www.example.net",
        "business_description": (
            "Medical furniture and lab bench provider with medical-grade precision. "
            "medical furniture, lab bench, healthcare workstation, heavy-duty lifting system."
        ),
        "product_interest_tags": "medical-grade precision, healthcare workstation",
        "notes": "UAT-TC-005",
    },
]

CONTACTS = [
    {
        "company_key": "office_dealer",
        "first_name": "Alex",
        "last_name": "Principal",
        "title": "Owner / President",
        "email": "alex.principal@uat-ne-office.example",
        "contact_type": "Owner",
        "decision_maker_level": "executive",
    },
    {
        "company_key": "ergo_sitstand",
        "first_name": "Sam",
        "last_name": "Sales",
        "title": "Sales Manager",
        "email": "sam.sales@uat-ergo.example",
        "contact_type": "Sales Manager",
        "decision_maker_level": "manager",
    },
    {
        "company_key": "education",
        "first_name": "Pat",
        "last_name": "Procurement",
        "title": "Procurement / Operations",
        "email": "pat.proc@uat-campus.example",
        "contact_type": "Procurement Manager",
        "decision_maker_level": "manager",
    },
]

TOUCHPOINTS = [
    {
        "company_key": "office_dealer",
        "interaction_type": "LinkedIn Message",
        "channel": "LinkedIn",
        "subject": "LinkedIn connect note sent",
        "summary": "Sent intro note about catalog partnership.",
        "next_action": "Follow up on LinkedIn in 5 days",
    },
    {
        "company_key": "ergo_sitstand",
        "interaction_type": "Email",
        "channel": "Email",
        "subject": "Catalog sent by email",
        "summary": "Shared lifting column catalog PDF.",
        "next_action": "Schedule technical call",
    },
    {
        "company_key": "healthcare",
        "interaction_type": "Meeting",
        "channel": "In Person",
        "subject": "Meeting proposed",
        "summary": "Proposed onsite demo for lab bench lifting system.",
        "next_action": "Confirm meeting date",
    },
]

ENRICHMENT_KEYS = ["office_dealer", "ergo_sitstand"]


def main() -> int:
    out: dict = {"errors": [], "steps": {}}
    with httpx.Client(timeout=120.0) as client:
        # Health
        for path in ["/health", "/api/v1/system/readiness", "/api/v1/portal/manifest"]:
            r = client.get(f"{BASE}{path}")
            out["steps"][path] = {"status": r.status_code, "ok": r.status_code == 200}

        # Login direct
        lr = client.post(f"{BASE}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        if lr.status_code != 200:
            out["errors"].append(f"login failed: {lr.status_code} {lr.text}")
            print(json.dumps(out, indent=2, default=str))
            return 1
        token = lr.json()["access_token"]
        out["steps"]["login"] = {"status": 200, "token_received": bool(token)}
        headers = {"Authorization": f"Bearer {token}"}

        # Login via Vite proxy
        try:
            pr = client.post(
                f"{PROXY_BASE}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            )
            out["steps"]["login_via_vite_proxy"] = {"status": pr.status_code, "ok": pr.status_code == 200}
        except httpx.ConnectError as e:
            out["steps"]["login_via_vite_proxy"] = {"ok": False, "error": str(e)}

        # /auth/me
        me = client.get(f"{BASE}/api/auth/me", headers=headers)
        out["steps"]["auth_me"] = {"status": me.status_code, "email": me.json().get("email") if me.status_code == 200 else None}

        company_ids: dict[str, str] = {}
        contact_ids: dict[str, str] = {}
        lead_ids: dict[str, str] = {}

        # Companies
        out["companies"] = []
        for c in COMPANIES:
            payload = {k: v for k, v in c.items() if k != "key"}
            r = client.post(f"{BASE}/api/companies", json=payload, headers=headers)
            row = {
                "key": c["key"],
                "name": c["company_name"],
                "status": r.status_code,
                "company_id": None,
                "error": None,
            }
            if r.status_code == 201:
                row["company_id"] = str(r.json()["id"])
                company_ids[c["key"]] = row["company_id"]
            else:
                row["error"] = r.text[:300]
                out["errors"].append(f"company {c['key']}: {r.status_code}")
            out["companies"].append(row)

        # Contacts
        out["contacts"] = []
        for ct in CONTACTS:
            cid = company_ids.get(ct["company_key"])
            if not cid:
                continue
            payload = {
                "first_name": ct["first_name"],
                "last_name": ct["last_name"],
                "company_id": cid,
                "title": ct["title"],
                "email": ct["email"],
                "contact_type": ct["contact_type"],
                "decision_maker_level": ct["decision_maker_level"],
            }
            r = client.post(f"{BASE}/api/contacts", json=payload, headers=headers)
            row = {
                "name": f"{ct['first_name']} {ct['last_name']}",
                "company_key": ct["company_key"],
                "status": r.status_code,
                "contact_id": None,
            }
            if r.status_code == 201:
                row["contact_id"] = str(r.json()["id"])
                contact_ids[ct["company_key"]] = row["contact_id"]
            out["contacts"].append(row)

        # Leads + workflow
        out["workflows"] = []
        for c in COMPANIES:
            cid = company_ids.get(c["key"])
            if not cid:
                continue
            pc = contact_ids.get(c["key"])
            lp = {
                "lead_name": f"UAT Lead — {c['company_name']}",
                "company_id": cid,
                "primary_contact_id": pc,
                "source": "Manual Research",
                "lead_type": "Product Fit Lead",
                "product_interest": c.get("product_interest_tags", "").split(",")[0].strip(),
                "current_stage": "New",
                "priority": "medium",
            }
            lr2 = client.post(f"{BASE}/api/leads", json=lp, headers=headers)
            if lr2.status_code != 201:
                out["errors"].append(f"lead {c['key']}: {lr2.status_code}")
                continue
            lid = str(lr2.json()["id"])
            lead_ids[c["key"]] = lid
            wf = client.get(f"{BASE}/api/a-domain/leads/{lid}/workflow", headers=headers)
            if wf.status_code == 200:
                wfj = wf.json()
                out["workflows"].append(
                    {
                        "company_key": c["key"],
                        "lead_id": lid,
                        "intelligence_score": wfj.get("intelligence_score"),
                        "market_fit_segments": wfj.get("market_fit_segments"),
                        "suggested_next_actions": wfj.get("suggested_next_actions"),
                        "next_action": wfj.get("lead", {}).get("next_action"),
                    }
                )
            else:
                out["errors"].append(f"workflow {c['key']}: {wf.status_code}")

        # Enrichment
        out["enrichment"] = []
        for key in ENRICHMENT_KEYS:
            cid = company_ids.get(key)
            if not cid:
                continue
            try:
                er = client.post(f"{BASE}/api/companies/{cid}/enrichment/runs", headers=headers)
            except httpx.HTTPError as exc:
                row["error"] = str(exc)
                out["enrichment"].append(row)
                continue
            row = {"company_key": key, "create_status": er.status_code, "run_id": None}
            if er.status_code != 201:
                row["error"] = er.text[:300]
                out["enrichment"].append(row)
                continue
            run_id = str(er.json()["id"])
            row["run_id"] = run_id
            final = None
            for _ in range(30):
                time.sleep(2)
                dr = client.get(f"{BASE}/api/companies/enrichment/runs/{run_id}", headers=headers)
                if dr.status_code == 200:
                    final = dr.json()
                    if final.get("status") in ("completed", "failed", "partial"):
                        break
            if final:
                row["status"] = final.get("status")
                row["pages_fetched"] = final.get("pages_fetched")
                row["sources_count"] = len(final.get("sources") or [])
                row["suggestions_count"] = len(final.get("suggestions") or [])
                row["error_message"] = final.get("error_message")
                pending = [s for s in (final.get("suggestions") or []) if s.get("review_status") == "pending"]
                if pending:
                    sid = pending[0]["id"]
                    rr = client.post(
                        f"{BASE}/api/companies/enrichment/suggestions/{sid}/review",
                        headers=headers,
                        json={"review_status": "rejected", "review_note": "UAT reject sample"},
                    )
                    row["review_reject_status"] = rr.status_code
            out["enrichment"].append(row)

        # Touchpoints
        out["touchpoints"] = []
        due = (date.today() + timedelta(days=7)).isoformat()
        for tp in TOUCHPOINTS:
            lid = lead_ids.get(tp["company_key"])
            if not lid:
                continue
            body = {
                "interaction_type": tp["interaction_type"],
                "channel": tp["channel"],
                "subject": tp["subject"],
                "summary": tp["summary"],
                "next_action": tp["next_action"],
                "next_action_due_date": due,
            }
            tr = client.post(f"{BASE}/api/a-domain/leads/{lid}/touchpoint", json=body, headers=headers)
            row = {
                "company_key": tp["company_key"],
                "lead_id": lid,
                "status": tr.status_code,
                "next_action": None,
                "persisted": False,
            }
            if tr.status_code == 201:
                row["next_action"] = tr.json().get("next_action")
                wf2 = client.get(f"{BASE}/api/a-domain/leads/{lid}/workflow", headers=headers)
                if wf2.status_code == 200:
                    row["persisted"] = wf2.json().get("lead", {}).get("next_action") == tp["next_action"]
            out["touchpoints"].append(row)

        # Frontend HTML smoke (public routes)
        out["frontend_pages"] = []
        for path in ["/login", "/", "/companies", "/lead-intelligence", "/contacts", "/tasks"]:
            try:
                fr = client.get(f"{PROXY_BASE}{path}")
                out["frontend_pages"].append(
                    {"path": path, "status": fr.status_code, "html_len": len(fr.text), "ok": fr.status_code == 200}
                )
            except httpx.ConnectError as e:
                out["frontend_pages"].append({"path": path, "ok": False, "error": str(e)})

        # Company workspace contacts check
        if company_ids.get("office_dealer"):
            ws = client.get(
                f"{BASE}/api/companies/{company_ids['office_dealer']}/workspace",
                headers=headers,
            )
            out["steps"]["company_workspace"] = {
                "status": ws.status_code,
                "contacts_count": len(ws.json().get("contacts", [])) if ws.status_code == 200 else 0,
            }

    print(json.dumps(out, indent=2, default=str))
    return 0 if not out["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
