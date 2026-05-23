"""Verify enrichment accept/reject API (same endpoints as Enrichment Panel UI)."""

from __future__ import annotations

import json
import sys

import httpx

BASE = "http://127.0.0.1:8000"
COMPANIES = {
    "office_dealer": "cd3ebcfc-70b2-438f-b2cd-f8745e6e656e",
    "ergo_sitstand": "d4706133-5062-468a-8355-e4a1e2d1ff46",
}


def main() -> int:
    out: list[dict] = []
    with httpx.Client(timeout=60.0) as client:
        lr = client.post(
            f"{BASE}/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        if lr.status_code != 200:
            print(json.dumps({"error": "login failed", "status": lr.status_code}))
            return 1
        h = {"Authorization": f"Bearer {lr.json()['access_token']}"}

        for key, cid in COMPANIES.items():
            lruns = client.get(f"{BASE}/api/companies/{cid}/enrichment/runs", headers=h, params={"limit": 5})
            if lruns.status_code != 200 or not lruns.json().get("items"):
                out.append({"company_key": key, "error": "no runs"})
                continue
            run_id = lruns.json()["items"][0]["id"]
            detail = client.get(f"{BASE}/api/companies/enrichment/runs/{run_id}", headers=h)
            if detail.status_code != 200:
                out.append({"company_key": key, "error": "detail failed"})
                continue
            suggestions = detail.json().get("suggestions", [])
            pending = [s for s in suggestions if s.get("review_status") == "pending"]
            accepted_before = [s for s in suggestions if s.get("review_status") == "accepted"]
            rejected_before = [s for s in suggestions if s.get("review_status") == "rejected"]

            row_base = {
                "company_key": key,
                "run_id": run_id,
                "sources": len(detail.json().get("sources", [])),
                "suggestions_total": len(suggestions),
                "status": detail.json().get("run", {}).get("status"),
            }

            # Reject one pending (or first pending for reject test)
            if pending:
                sid_reject = pending[0]["id"]
                rr = client.post(
                    f"{BASE}/api/companies/enrichment/suggestions/{sid_reject}/review",
                    headers=h,
                    json={"review_status": "rejected"},
                )
                out.append(
                    {
                        **row_base,
                        "operation": "reject",
                        "suggestion_id": sid_reject,
                        "suggestion_type": pending[0].get("suggestion_type"),
                        "api_status": rr.status_code,
                        "api_ok": rr.status_code == 200,
                        "review_status_after": rr.json().get("review_status") if rr.status_code == 200 else None,
                    }
                )
                pending = pending[1:]

            # Accept one pending
            if pending:
                sid_accept = pending[0]["id"]
                ar = client.post(
                    f"{BASE}/api/companies/enrichment/suggestions/{sid_accept}/review",
                    headers=h,
                    json={"review_status": "accepted"},
                )
                accept_id = sid_accept
                accept_ok = ar.status_code == 200
                accept_status = ar.json().get("review_status") if accept_ok else None
            else:
                # use already accepted for persist check
                accept_id = accepted_before[0]["id"] if accepted_before else None
                accept_ok = None
                accept_status = accepted_before[0].get("review_status") if accepted_before else None

            if pending or accept_id:
                out.append(
                    {
                        **row_base,
                        "operation": "accept",
                        "suggestion_id": accept_id or (pending[0]["id"] if pending else None),
                        "api_status": 200 if accept_ok else ("skipped" if accept_ok is None else 0),
                        "api_ok": accept_ok if accept_ok is not None else bool(accepted_before),
                        "review_status_after": accept_status,
                    }
                )

            # Persist check: re-fetch detail
            detail2 = client.get(f"{BASE}/api/companies/enrichment/runs/{run_id}", headers=h)
            if detail2.status_code == 200:
                statuses = {s["id"]: s["review_status"] for s in detail2.json().get("suggestions", [])}
                for item in out:
                    if item.get("company_key") == key and item.get("suggestion_id"):
                        sid = item["suggestion_id"]
                        item["persisted_after_refresh"] = statuses.get(sid) == item.get("review_status_after")

    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
