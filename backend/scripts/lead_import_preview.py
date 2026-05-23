"""Preview CSV lead intake rows (D5.2.4). Default read-only; use --apply --confirm to import via API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.services.a_domain.lead_import_apply import (
    build_contact_create_payload,
    build_lead_link_payload,
    format_apply_result,
    match_existing_contact,
)
from app.services.a_domain.lead_import_intake import (
    preview_row,
    read_csv_rows,
    validate_headers,
)
from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()

SOURCE_MAP = {
    "trade show": "Trade Show",
    "referral": "Referral",
    "website": "Website",
    "website inbound": "Website",
    "linkedin": "LinkedIn",
    "email": "Email",
    "manual": "Manual Research",
    "manual research": "Manual Research",
    "other": "Other",
    "partner intro": "Referral",
    "phone / prior outreach": "Manual Research",
    "virtual meeting / quote": "Manual Research",
    "visit / outreach": "Field Visit",
    "quotation / outreach": "Manual Research",
    "lead list / outreach": "Manual Research",
    "handwritten note / lead record": "Manual Research",
    "outreach": "Manual Research",
}


def _login(client: httpx.Client) -> dict[str, str] | None:
    r = client.post(
        f"{BASE}/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _existing_company_names(client: httpx.Client, headers: dict[str, str]) -> set[str]:
    r = client.get(f"{BASE}/api/companies", headers=headers, params={"limit": 200})
    if r.status_code != 200:
        return set()
    return {i.get("company_name", "") for i in r.json().get("items", [])}


def _map_source(raw: str) -> str:
    key = (raw or "").strip().lower()
    return SOURCE_MAP.get(key, raw if raw in SOURCE_MAP.values() else "Other")


def _normalize_priority(raw: str | None) -> str | None:
    if not raw:
        return None
    p = raw.strip().lower()
    if p in ("high", "medium", "low", "urgent"):
        return p
    return None


def _list_contacts(client: httpx.Client, headers: dict[str, str]) -> list[dict]:
    r = client.get(f"{BASE}/api/contacts", headers=headers, params={"limit": 200})
    if r.status_code != 200:
        return []
    return r.json().get("items", [])


def _find_company_id(client: httpx.Client, headers: dict[str, str], name: str) -> str | None:
    r = client.get(f"{BASE}/api/companies", headers=headers, params={"q": name.split()[0], "limit": 30})
    if r.status_code != 200:
        return None
    for item in r.json().get("items", []):
        if item.get("company_name") == name:
            return item["id"]
    return None


def _find_lead_for_company(client: httpx.Client, headers: dict[str, str], company_id: str) -> dict | None:
    r = client.get(f"{BASE}/api/leads", headers=headers, params={"limit": 200})
    if r.status_code != 200:
        return None
    for lead in r.json().get("items", []):
        if lead.get("company_id") == company_id:
            wf = client.get(
                f"{BASE}/api/a-domain/leads/{lead['id']}/workflow",
                headers=headers,
            )
            if wf.status_code == 200:
                body = wf.json()
                primary = body.get("primary_contact")
                if primary and primary.get("id"):
                    lead = {**lead, "primary_contact_id": str(primary["id"])}
            return lead
    return None


def _ensure_contact(
    client: httpx.Client,
    headers: dict[str, str],
    company_id: str,
    row: dict[str, str],
    contacts: list[dict] | None = None,
) -> str | None:
    if contacts is None:
        contacts = _list_contacts(client, headers)
    existing_id = match_existing_contact(contacts, company_id, row)
    if existing_id:
        return existing_id
    cp = build_contact_create_payload(company_id, row)
    if not cp:
        return None
    ccr = client.post(f"{BASE}/api/contacts", headers=headers, json=cp)
    if ccr.status_code in (200, 201):
        return str(ccr.json()["id"])
    return None


def _fetch_company_detail(client: httpx.Client, headers: dict[str, str], company_id: str) -> dict:
    ws = client.get(f"{BASE}/api/companies/{company_id}/workspace", headers=headers)
    if ws.status_code == 200:
        return ws.json().get("company") or {}
    return {}


def _maybe_patch_company(
    client: httpx.Client,
    headers: dict[str, str],
    company_id: str,
    row: dict[str, str],
) -> bool:
    co = _fetch_company_detail(client, headers, company_id)
    patch: dict = {}
    if row.get("notes") and not co.get("business_description"):
        patch["business_description"] = row.get("notes")
        patch["notes"] = row.get("notes")
    if row.get("initial_interest") and not co.get("product_interest_tags"):
        patch["product_interest_tags"] = row.get("initial_interest")
    for field, key in (
        ("city", "city"),
        ("state", "state"),
        ("industry", "industry"),
        ("company_type", "company_type"),
    ):
        if row.get(field) and not co.get(field):
            patch[key] = row.get(field)
    if not patch:
        return False
    pr = client.put(f"{BASE}/api/companies/{company_id}", headers=headers, json=patch)
    return pr.status_code == 200


def _link_lead(
    client: httpx.Client,
    headers: dict[str, str],
    lead: dict,
    contact_id: str | None,
    recommended_next_action: str,
) -> tuple[bool, str | None]:
    payload = build_lead_link_payload(lead, contact_id, recommended_next_action)
    if not payload:
        return False, None
    lr = client.put(f"{BASE}/api/leads/{lead['id']}", headers=headers, json=payload)
    if lr.status_code != 200:
        return False, f"FAIL link {lead.get('lead_name', lead['id'])}: {lr.status_code} {lr.text[:120]}"
    return True, None


def _apply_row(client: httpx.Client, headers: dict[str, str], row: dict[str, str]) -> str:
    name = row.get("company_name", "").strip()
    existing = _existing_company_names(client, headers)
    company_id: str | None = None
    contact_id: str | None = None
    updated_company = False
    linked = False
    contacts = _list_contacts(client, headers)
    preview = preview_row(row)

    if name in existing:
        company_id = _find_company_id(client, headers, name)
        if not company_id:
            return format_apply_result(name, fail=f"SKIP duplicate: {name} (not found by id)")
        updated_company = _maybe_patch_company(client, headers, company_id, row)
        contact_id = _ensure_contact(client, headers, company_id, row, contacts)
        lead = _find_lead_for_company(client, headers, company_id)
        if lead:
            linked, err = _link_lead(
                client,
                headers,
                lead,
                contact_id,
                preview.recommended_next_action,
            )
            if err:
                return err
            if linked or updated_company:
                return format_apply_result(
                    name,
                    linked=linked,
                    updated_company=updated_company,
                )
            return format_apply_result(name, skipped=True)
    else:
        company_type = row.get("company_type") or "Other"
        payload = {
            "company_name": name,
            "website": row.get("website") or None,
            "linkedin_url": row.get("linkedin_url") or None,
            "company_type": company_type,
            "industry": row.get("industry") or None,
            "city": row.get("city") or None,
            "state": row.get("state") or None,
            "country": row.get("country") or "United States",
            "business_description": row.get("notes") or None,
            "product_interest_tags": row.get("initial_interest") or None,
            "source": row.get("source") or None,
            "notes": row.get("notes") or None,
            "priority": _normalize_priority(row.get("priority")),
        }
        cr = client.post(f"{BASE}/api/companies", headers=headers, json=payload)
        if cr.status_code not in (200, 201):
            return format_apply_result(
                name,
                fail=f"FAIL company {name}: {cr.status_code} {cr.text[:120]}",
            )
        company_id = cr.json()["id"]
        contact_id = _ensure_contact(client, headers, company_id, row, contacts)

    lead_name = f"Lead — {name}"
    lp = {
        "lead_name": lead_name,
        "company_id": company_id,
        "primary_contact_id": contact_id,
        "source": _map_source(row.get("source", "")),
        "lead_type": "Channel Lead",
        "product_interest": row.get("initial_interest") or None,
        "current_stage": "New",
        "priority": _normalize_priority(row.get("priority")),
        "next_action": preview.recommended_next_action,
        "notes": row.get("notes") or None,
    }
    lr = client.post(f"{BASE}/api/leads", headers=headers, json=lp)
    if lr.status_code not in (200, 201):
        return format_apply_result(
            name,
            partial=f"PARTIAL {name}: company created, lead failed {lr.status_code}",
        )

    return format_apply_result(name, imported=True)


def _print_preview(previews: list, header_warnings: list[str]) -> None:
    print("Lead Import Preview")
    if header_warnings:
        for w in header_warnings:
            print(f"[HEADER WARN] {w}")
    for p in previews:
        tag = p.status
        print(f"[{tag}] {p.company_name}")
        if p.duplicate_hint:
            print(f"  duplicate: {p.duplicate_hint}")
        if p.missing_fields:
            print(f"  missing: {', '.join(p.missing_fields)}")
        seg = ", ".join(p.likely_segments) if p.likely_segments else "(none)"
        print(f"  segments: {seg}")
        print(f"  priority: {p.priority_hint}")
        print(f"  next_action: {p.recommended_next_action}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview CSV lead intake (D5.2.4)")
    parser.add_argument("csv_path", type=Path, help="Path to lead_import_template.csv")
    parser.add_argument("--apply", action="store_true", help="Create companies/contacts/leads via API")
    parser.add_argument("--confirm", action="store_true", help="Required with --apply")
    args = parser.parse_args()

    if not args.csv_path.is_file():
        print(f"File not found: {args.csv_path}")
        return 1

    if args.apply and not args.confirm:
        print("Refusing --apply without --confirm")
        return 1

    try:
        headers_list, rows = read_csv_rows(args.csv_path)
    except ValueError as e:
        print(f"CSV error: {e}")
        return 1

    header_missing = validate_headers(headers_list)
    header_warnings = [f"missing optional column: {c}" for c in header_missing]

    duplicate_names: set[str] = set()
    if args.apply:
        with httpx.Client(timeout=60.0) as client:
            auth = _login(client)
            if not auth:
                print("Cannot login — is backend running?")
                print(f"  BACKEND_BASE_URL={get_backend_base_url()}")
                return 1
            duplicate_names = _existing_company_names(client, auth)
    else:
        try:
            with httpx.Client(timeout=10.0) as client:
                auth = _login(client)
                if auth:
                    duplicate_names = _existing_company_names(client, auth)
        except httpx.ConnectError:
            pass

    previews = [preview_row(r, duplicate_names=duplicate_names) for r in rows]
    _print_preview(previews, header_warnings)

    if args.apply:
        print("--- Apply ---")
        global BASE
        BASE = log_backend_base_url()
        with httpx.Client(timeout=60.0) as client:
            auth = _login(client)
            if not auth:
                print("Cannot login")
                return 1
            for row in rows:
                print(_apply_row(client, auth, row))

    return 0


if __name__ == "__main__":
    sys.exit(main())
