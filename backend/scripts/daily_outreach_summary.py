"""D5.2.7 read-only daily outreach summary."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.core.backend_url import get_backend_base_url, log_backend_base_url
from app.services.a_domain.follow_up_rhythm import (
    NO_NEXT_ACTION,
    RhythmLead,
    recommend_top_actions,
    segment_breakdown,
    summarize_counts,
)

BASE = get_backend_base_url()


def _ascii_safe(text: str) -> str:
    """Avoid em-dash mojibake in Windows PowerShell."""
    return text.replace("\u2014", "-").replace("\u2013", "-")


def _login(client: httpx.Client) -> dict[str, str] | None:
    r = client.post(
        f"{BASE}/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _display_enrichment(status: str, pending: int) -> str:
    s = (status or "").lower()
    if s == "completed":
        return f"Completed ({pending} pending)" if pending > 0 else "Completed"
    if s == "running":
        return "Running"
    if s == "failed":
        return "Failed"
    if s == "pending":
        return "Pending"
    return status or "No runs"


def run() -> int:
    base = log_backend_base_url()
    try:
        with httpx.Client(timeout=90.0) as client:
            headers = _login(client)
            if not headers:
                print(f"Cannot login at {base}")
                return 1

            lr = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 200})
            if lr.status_code != 200:
                print(f"Failed to list leads: {lr.status_code}")
                return 1

            leads_raw = lr.json().get("items", [])
            rhythm_leads: list[RhythmLead] = []
            enrich_cache: dict[str, str] = {}

            for lead in leads_raw:
                lid = lead["id"]
                wf = client.get(f"{BASE}/api/a-domain/leads/{lid}/workflow", headers=headers)
                if wf.status_code != 200:
                    continue
                w = wf.json()
                company = w.get("company") or {}
                contact = w.get("primary_contact")
                cid = company.get("id")

                touch_count = 0
                last_touch = "-"
                last_touch_date = None
                ix = client.get(
                    f"{BASE}/api/objects/lead/{lid}/interactions",
                    headers=headers,
                    params={"limit": 1},
                )
                if ix.status_code == 200:
                    touch_count = ix.json().get("total", 0) or 0
                    items = ix.json().get("items") or []
                    if items:
                        t0 = items[0]
                        last_touch = t0.get("summary") or t0.get("subject") or t0.get("interaction_type") or "-"
                        last_touch_date = t0.get("interaction_date")

                if cid and cid not in enrich_cache:
                    er = client.get(
                        f"{BASE}/api/companies/{cid}/enrichment/runs",
                        headers=headers,
                        params={"limit": 1},
                    )
                    if er.status_code == 200 and er.json().get("total", 0) > 0:
                        r0 = er.json()["items"][0]
                        enrich_cache[cid] = _display_enrichment(
                            r0.get("status", ""),
                            r0.get("pending_suggestion_count", 0),
                        )
                    else:
                        enrich_cache[cid] = "No runs"

                next_action = (lead.get("next_action") or (w.get("lead") or {}).get("next_action") or "").strip()
                if not next_action:
                    next_action = NO_NEXT_ACTION

                rhythm_leads.append(
                    RhythmLead(
                        company_name=company.get("company_name") or lead.get("lead_name", "(unnamed)"),
                        score=int(w.get("intelligence_score") or 0),
                        segments=list(w.get("market_fit_segments") or []),
                        next_action=next_action,
                        touch_count=touch_count,
                        last_touch=last_touch,
                        last_touch_date=last_touch_date,
                        contact_email=contact.get("email") if contact else None,
                        linkedin_url=company.get("linkedin_url"),
                        enrichment_status=enrich_cache.get(cid, "-") if cid else "-",
                        company_website=company.get("website"),
                    )
                )

    except httpx.ConnectError:
        print(f"Backend not reachable at {base}")
        return 1

    counts = summarize_counts(rhythm_leads)
    segments = segment_breakdown(rhythm_leads)
    top = recommend_top_actions(rhythm_leads, limit=10)

    print("D5.2.7 Daily Outreach Summary")
    print()
    print(f"Total leads: {counts['total']}")
    print(f"Needs first outreach: {counts['needs_first_outreach']}")
    print(f"Waiting for reply: {counts['waiting_for_reply']}")
    print(f"Follow up soon: {counts['follow_up_soon']}")
    print(f"Needs contact research: {counts['needs_contact_research']}")
    print(f"High priority: {counts['high_priority']}")
    print(f"Needs enrichment: {counts['needs_enrichment']}")
    print(f"Ready for catalog / quote: {counts['ready_for_catalog_quote']}")
    print()
    print("Top 10 recommended actions:")
    for i, (company, action, reason) in enumerate(top, start=1):
        action_short = action[:80] + ("..." if len(action) > 80 else "")
        print(f"{i}. {_ascii_safe(company)} - {_ascii_safe(action_short)} - {_ascii_safe(reason)}")
    print()
    print("Segment breakdown:")
    for key, val in segments.items():
        print(f"- {key}: {val}")
    print()
    print("Safety:")
    print("- no automatic sending")
    print("- manual review required")
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
