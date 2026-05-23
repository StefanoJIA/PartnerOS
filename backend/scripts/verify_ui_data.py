"""Verify UAT test data reachable via API (browser UI pre-check)."""

from __future__ import annotations

import json
import sys

import httpx

BASE = "http://127.0.0.1:8000"
PROXY = "http://127.0.0.1:5174"


def main() -> int:
    out: dict = {}
    with httpx.Client(timeout=30.0) as client:
        lr = client.post(f"{BASE}/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
        out["login"] = lr.status_code
        if lr.status_code != 200:
            print(json.dumps(out, indent=2))
            return 1
        h = {"Authorization": f"Bearer {lr.json()['access_token']}"}
        out["proxy_login"] = client.post(
            f"{PROXY}/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        ).status_code

        company_names = [
            "New England Office Furniture Dealer",
            "Ergo Sit Stand Workspace",
            "Contract Project Interiors",
            "Campus Learning Furniture",
            "Healthcare Lab Workspace",
        ]
        out["companies"] = []
        for name in company_names:
            r = client.get(f"{BASE}/api/companies", headers=h, params={"q": name.split()[0], "limit": 10})
            match = next((i for i in r.json().get("items", []) if i["company_name"] == name), None)
            row = {"name": name, "found": match is not None}
            if match:
                cid = match["id"]
                row["id"] = cid
                ws = client.get(f"{BASE}/api/companies/{cid}/workspace", headers=h)
                row["workspace_ok"] = ws.status_code == 200
                row["contacts_in_workspace"] = len(ws.json().get("contacts", [])) if ws.status_code == 200 else 0
                er = client.get(f"{BASE}/api/companies/{cid}/enrichment/runs", headers=h)
                row["enrichment_runs"] = er.json().get("total", 0) if er.status_code == 200 else 0
            out["companies"].append(row)

        contacts = ["Alex", "Sam", "Pat"]
        out["contacts"] = []
        cr = client.get(f"{BASE}/api/contacts", headers=h, params={"limit": 50})
        for fn in contacts:
            match = next((i for i in cr.json().get("items", []) if i["first_name"] == fn), None)
            out["contacts"].append(
                {
                    "first_name": fn,
                    "found": match is not None,
                    "company_name": match.get("company_name") if match else None,
                }
            )

        out["leads"] = []
        lr2 = client.get(f"{BASE}/api/leads", headers=h, params={"limit": 30})
        for lead in lr2.json().get("items", []):
            if "UAT Lead" not in lead.get("lead_name", ""):
                continue
            wf = client.get(f"{BASE}/api/a-domain/leads/{lead['id']}/workflow", headers=h)
            if wf.status_code != 200:
                continue
            w = wf.json()
            out["leads"].append(
                {
                    "lead_name": lead["lead_name"],
                    "score": w.get("intelligence_score"),
                    "segments": w.get("market_fit_segments"),
                    "next_action": w.get("lead", {}).get("next_action"),
                    "suggestions_count": len(w.get("suggested_next_actions") or []),
                }
            )

        for path in ["/login", "/companies", "/contacts", "/lead-intelligence"]:
            try:
                fr = client.get(f"{PROXY}{path}")
                out.setdefault("frontend_routes", {})[path] = fr.status_code
            except httpx.HTTPError as exc:
                out.setdefault("frontend_routes", {})[path] = str(exc)

    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
