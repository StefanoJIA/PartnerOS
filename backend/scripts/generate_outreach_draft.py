"""Generate human-reviewed outreach drafts (D5.2.4 — no send, no LinkedIn/Outlook)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.services.a_domain.outreach_templates import generate_outreach_draft
from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()


def _login(client: httpx.Client) -> dict[str, str] | None:
    r = client.post(
        f"{BASE}/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _resolve_company(
    client: httpx.Client,
    headers: dict[str, str],
    *,
    company_id: str | None,
    company_name: str | None,
) -> dict | None:
    if company_id:
        r = client.get(f"{BASE}/api/companies/{company_id}", headers=headers)
        return r.json() if r.status_code == 200 else None
    if not company_name:
        return None
    r = client.get(f"{BASE}/api/companies", headers=headers, params={"q": company_name.split()[0], "limit": 50})
    if r.status_code != 200:
        return None
    for item in r.json().get("items", []):
        if item.get("company_name") == company_name:
            return item
    for item in r.json().get("items", []):
        if company_name.lower() in (item.get("company_name") or "").lower():
            return item
    return None


def _segments_for_company(client: httpx.Client, headers: dict[str, str], company: dict) -> list[str]:
    lr = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 100})
    if lr.status_code != 200:
        return []
    cid = company["id"]
    for lead in lr.json().get("items", []):
        if lead.get("company_id") != cid:
            continue
        wf = client.get(f"{BASE}/api/a-domain/leads/{lead['id']}/workflow", headers=headers)
        if wf.status_code == 200:
            segs = wf.json().get("market_fit_segments") or []
            if segs:
                return segs
    from app.services.a_domain.intelligence_score import infer_market_fit_segments

    blob = " \n ".join(
        filter(
            None,
            [
                company.get("product_interest_tags"),
                company.get("business_description"),
                company.get("notes"),
                company.get("industry"),
                company.get("company_type"),
            ],
        )
    ).lower()
    return infer_market_fit_segments(blob)


def _contact_name(client: httpx.Client, headers: dict[str, str], company_id: str) -> str | None:
    r = client.get(f"{BASE}/api/contacts", headers=headers, params={"limit": 50})
    if r.status_code != 200:
        return None
    for c in r.json().get("items", []):
        if c.get("company_id") == company_id:
            return f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
    return None


def _print_draft(draft) -> None:
    print(f"Outreach Draft — {draft.company_name}")
    print(f"  channel: {draft.channel}")
    print(f"  language: {draft.language}  tone: {draft.tone}  focus: {draft.product_focus}")
    print(f"  segments: {', '.join(draft.segments) or '(none)'}")
    if draft.linkedin_connect_note:
        print(f"  linkedin_note ({len(draft.linkedin_connect_note)} chars):")
        print(f"    {draft.linkedin_connect_note}")
    if draft.email_subject:
        print(f"  email_subject: {draft.email_subject}")
    if draft.email_body:
        print("  email_body:")
        for line in draft.email_body.splitlines():
            print(f"    {line}")
    print(f"  suggested_next_action: {draft.suggested_next_action}")
    print(f"  suggested_touchpoint_type: {draft.suggested_touchpoint_type}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate outreach draft text (D5.2.4)")
    parser.add_argument("--company-id", dest="company_id", default=None)
    parser.add_argument("--company", dest="company_name", default=None)
    parser.add_argument("--channel", default="linkedin_connect")
    parser.add_argument("--language", default="en", choices=["en", "zh"])
    parser.add_argument("--tone", default="concise", choices=["concise", "warm", "formal"])
    parser.add_argument(
        "--product-focus",
        dest="product_focus",
        default="general",
        choices=["hosun_lifting", "jooboo_education", "medical_workspace", "project_supply", "general"],
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    if not args.company_id and not args.company_name:
        print("Provide --company or --company-id")
        return 1

    global BASE
    BASE = log_backend_base_url()

    with httpx.Client(timeout=30.0) as client:
        headers = _login(client)
        if not headers:
            print(f"Cannot login — start backend at {BASE}")
            return 1
        company = _resolve_company(
            client,
            headers,
            company_id=args.company_id,
            company_name=args.company_name,
        )
        if not company:
            print("Company not found")
            return 1

        segments = _segments_for_company(client, headers, company)
        contact = _contact_name(client, headers, company["id"])
        draft = generate_outreach_draft(
            company_name=company["company_name"],
            segments=segments,
            contact_name=contact,
            channel=args.channel,
            language=args.language,
            tone=args.tone,
            product_focus=args.product_focus,
            notes=company.get("notes"),
        )

    if args.json:
        print(json.dumps(draft.__dict__, indent=2, ensure_ascii=False))
    else:
        _print_draft(draft)
    return 0


if __name__ == "__main__":
    sys.exit(main())
