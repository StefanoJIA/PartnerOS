"""Preview CSV lead intake rows (D5.2.4). Default read-only; use --apply --confirm to import via API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.services.a_domain.lead_import_intake import (
    preview_row,
    read_csv_rows,
    split_contact_name,
    validate_headers,
)

BASE = "http://127.0.0.1:8000"

SOURCE_MAP = {
    "trade show": "Trade Show",
    "referral": "Referral",
    "website": "Website",
    "website inbound": "Website",
    "linkedin": "LinkedIn",
    "email": "Email",
    "manual": "Manual Research",
    "other": "Other",
    "partner intro": "Referral",
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


def _apply_row(client: httpx.Client, headers: dict[str, str], row: dict[str, str]) -> str:
    name = row.get("company_name", "").strip()
    existing = _existing_company_names(client, headers)
    if name in existing:
        return f"SKIP duplicate: {name}"

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
        "priority": row.get("priority") or None,
    }
    cr = client.post(f"{BASE}/api/companies", headers=headers, json=payload)
    if cr.status_code not in (200, 201):
        return f"FAIL company {name}: {cr.status_code} {cr.text[:120]}"

    company_id = cr.json()["id"]
    contact_id = None
    if row.get("contact_name"):
        first, last = split_contact_name(row["contact_name"])
        cp = {
            "first_name": first,
            "last_name": last,
            "company_id": company_id,
            "title": row.get("contact_title") or None,
            "email": row.get("contact_email") or None,
            "phone": row.get("contact_phone") or None,
            "linkedin_url": row.get("linkedin_url") or None,
        }
        ccr = client.post(f"{BASE}/api/contacts", headers=headers, json=cp)
        if ccr.status_code in (200, 201):
            contact_id = ccr.json()["id"]

    preview = preview_row(row)
    lead_name = f"Lead — {name}"
    lp = {
        "lead_name": lead_name,
        "company_id": company_id,
        "primary_contact_id": contact_id,
        "source": _map_source(row.get("source", "")),
        "lead_type": "Channel Lead",
        "product_interest": row.get("initial_interest") or None,
        "current_stage": "New",
        "priority": row.get("priority") or None,
        "next_action": preview.recommended_next_action,
        "notes": row.get("notes") or None,
    }
    lr = client.post(f"{BASE}/api/leads", headers=headers, json=lp)
    if lr.status_code not in (200, 201):
        return f"PARTIAL {name}: company created, lead failed {lr.status_code}"

    return f"IMPORTED {name} (company + contact + lead)"


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
