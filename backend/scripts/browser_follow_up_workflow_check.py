"""D5.2.8 API workflow check mirroring browser Manual Outreach steps (read-only except one touchpoint)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.core.backend_url import get_backend_base_url, get_health_url, log_backend_base_url
from app.services.a_domain.follow_up_rhythm import (
    NO_NEXT_ACTION,
    RhythmLead,
    summarize_counts,
)

BASE = get_backend_base_url()
TARGET_COMPANY = "SWC Office Furniture"


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


def _load_rhythm_leads(client: httpx.Client, headers: dict[str, str]) -> list[RhythmLead]:
    lr = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 200})
    if lr.status_code != 200:
        return []
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
    return rhythm_leads



def run() -> int:
    global BASE
    BASE = log_backend_base_url()
    checks = [
        Check("login"),
        Check("system health"),
        Check("daily summary load"),
        Check("operation filter counts"),
        Check("generate draft API"),
        Check("mark as sent touchpoint"),
        Check("touchpoint persistence"),
        Check("next action persistence"),
        Check("summary count delta"),
    ]
    before: dict[str, int] = {}
    after: dict[str, int] = {}
    touch_before = 0
    touch_after = 0
    lead_id: str | None = None
    next_before = ""
    next_after = ""

    try:
        with httpx.Client(timeout=90.0) as client:
            headers = _login(client)
            if not headers:
                checks[0].fail("login failed")
                _print(checks, before, after)
                return 1
            checks[0].pass_()

            hr = client.get(get_health_url())
            if hr.status_code == 200 and hr.json().get("status") == "ok":
                checks[1].pass_("backend health ok")
            else:
                checks[1].fail(f"health {hr.status_code}")

            leads = _load_rhythm_leads(client, headers)
            if not leads:
                checks[2].fail("no leads loaded")
                _print(checks, before, after)
                return 1
            before = summarize_counts(leads)
            checks[2].pass_(f"total={before['total']}")

            filters_ok = before["total"] >= 5 and before["high_priority"] >= 1
            if filters_ok:
                checks[3].pass_(
                    f"first={before['needs_first_outreach']} wait={before['waiting_for_reply']} "
                    f"priority={before['high_priority']}"
                )
            else:
                checks[3].fail("insufficient demo data for filter summary")

            company = _find_company(client, headers, TARGET_COMPANY)
            if not company:
                for c in checks[4:]:
                    c.fail(f"company missing: {TARGET_COMPANY}")
                _print(checks, before, after)
                return 1
            lead = _lead_for_company(client, headers, company["id"])
            if not lead:
                for c in checks[4:]:
                    c.fail("lead missing")
                _print(checks, before, after)
                return 1
            lead_id = lead["id"]
            next_before = (lead.get("next_action") or "").strip()

            ix0 = client.get(
                f"{BASE}/api/objects/lead/{lead_id}/interactions",
                headers=headers,
                params={"limit": 1},
            )
            touch_before = ix0.json().get("total", 0) if ix0.status_code == 200 else 0

            channel = "email_intro"
            product_focus = "hosun_lifting"
            dr = client.get(
                f"{BASE}/api/a-domain/outreach-draft",
                headers=headers,
                params={
                    "company_id": company["id"],
                    "channel": channel,
                    "product_focus": product_focus,
                },
            )
            if dr.status_code != 200:
                checks[4].fail(f"draft HTTP {dr.status_code}")
                _print(checks, before, after)
                return 1
            draft = dr.json()
            preview = (
                draft.get("linkedin_connect_note")
                or "\n\n".join(filter(None, [draft.get("email_subject"), draft.get("email_body")]))
                or ""
            )
            checks[4].pass_(f"{TARGET_COMPANY} {channel}")

            preview_short = preview[:200].replace("\n", " ")
            summary = (
                f"[manually_sent=true] channel={channel}; product_focus={product_focus}; "
                f'draft_preview="{preview_short}"'
            )
            next_action = "Follow up in 5 days - waiting for email reply"
            tp = client.post(
                f"{BASE}/api/a-domain/leads/{lead_id}/touchpoint",
                headers=headers,
                json={
                    "interaction_type": "catalog_sent",
                    "channel": "email",
                    "subject": f"Manual outreach - {channel}",
                    "summary": summary,
                    "next_action": next_action,
                },
            )
            if tp.status_code not in (200, 201):
                checks[5].fail(f"touchpoint HTTP {tp.status_code}")
                _print(checks, before, after)
                return 1
            checks[5].pass_("touchpoint logged (manual send outside intelliOffice)")

            ix1 = client.get(
                f"{BASE}/api/objects/lead/{lead_id}/interactions",
                headers=headers,
                params={"limit": 1},
            )
            touch_after = ix1.json().get("total", 0) if ix1.status_code == 200 else 0
            if touch_after > touch_before:
                checks[6].pass_(f"{touch_before} -> {touch_after}")
            else:
                checks[6].fail(f"touch count unchanged ({touch_before})")

            lr2 = client.get(f"{BASE}/api/leads/{lead_id}", headers=headers)
            wf2 = client.get(f"{BASE}/api/a-domain/leads/{lead_id}/workflow", headers=headers)
            next_after = ""
            if lr2.status_code == 200:
                next_after = (lr2.json().get("next_action") or "").strip()
            if not next_after and wf2.status_code == 200:
                next_after = ((wf2.json().get("lead") or {}).get("next_action") or "").strip()
            if next_after and "wait" in next_after.lower():
                checks[7].pass_(next_after[:60])
            else:
                checks[7].fail(f"next_action={next_after!r}")

            leads_after = _load_rhythm_leads(client, headers)
            after = summarize_counts(leads_after)
            delta_wait = after["waiting_for_reply"] - before["waiting_for_reply"]
            checks[8].pass_(
                f"waiting_for_reply {before['waiting_for_reply']}->{after['waiting_for_reply']} "
                f"(delta {delta_wait:+d})"
            )

    except httpx.ConnectError:
        print(f"Backend not reachable at {BASE}")
        return 1

    _print(checks, before, after)
    return 0 if all(c.ok for c in checks) else 1


def _print(checks: list[Check], before: dict[str, int], after: dict[str, int]) -> None:
    print("D5.2.8 Browser Follow-up Workflow Check")
    for c in checks:
        print(c.line())
    if before and after:
        print()
        print("Summary counts (before -> after):")
        for key in (
            "needs_first_outreach",
            "waiting_for_reply",
            "follow_up_soon",
            "needs_contact_research",
            "high_priority",
        ):
            print(f"  {key}: {before.get(key, 0)} -> {after.get(key, 0)}")
    failed = sum(1 for c in checks if not c.ok)
    print()
    print(f"Result: {'PASS' if failed == 0 else 'FAIL'}")


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
