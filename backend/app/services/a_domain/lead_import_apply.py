"""Lead CSV apply helpers — idempotent company/contact/lead linking (D5.2.6 P2)."""

from __future__ import annotations

from app.services.a_domain.lead_import_intake import (
    first_email,
    first_phone,
    first_semicolon_token,
    split_contact_name,
)


def match_existing_contact(
    contacts: list[dict],
    company_id: str,
    row: dict[str, str],
) -> str | None:
    """Match contact by email first, then first/last name on the same company."""
    contact_name = first_semicolon_token(row.get("contact_name", ""))
    email = first_email(row.get("contact_email", ""))
    company_contacts = [c for c in contacts if c.get("company_id") == company_id]

    if email:
        email_lower = email.lower()
        for c in company_contacts:
            if (c.get("email") or "").strip().lower() == email_lower:
                return str(c["id"])

    if contact_name:
        first, last = split_contact_name(contact_name)
        for c in company_contacts:
            if c.get("first_name") == first and c.get("last_name") == last:
                return str(c["id"])

    if company_contacts:
        return str(company_contacts[0]["id"])

    return None


def build_contact_create_payload(company_id: str, row: dict[str, str]) -> dict | None:
    contact_name = first_semicolon_token(row.get("contact_name", ""))
    if not contact_name:
        return None
    first, last = split_contact_name(contact_name)
    return {
        "first_name": first,
        "last_name": last,
        "company_id": company_id,
        "title": row.get("contact_title") or None,
        "email": first_email(row.get("contact_email", "")) or None,
        "phone": first_phone(row.get("contact_phone", "")) or None,
        "linkedin_url": row.get("linkedin_url") or None,
    }


def build_lead_link_payload(
    lead: dict,
    contact_id: str | None,
    recommended_next_action: str,
) -> dict | None:
    """Build a safe PUT payload to link primary_contact_id without clobbering manual edits."""
    payload: dict = {}
    existing_contact = lead.get("primary_contact_id")
    existing_next = (lead.get("next_action") or "").strip()

    if contact_id:
        if not existing_contact:
            payload["primary_contact_id"] = contact_id
        elif str(existing_contact) != str(contact_id):
            return None

    if recommended_next_action and not existing_next:
        payload["next_action"] = recommended_next_action

    return payload or None


def format_apply_result(
    company_name: str,
    *,
    skipped: bool = False,
    linked: bool = False,
    updated_company: bool = False,
    imported: bool = False,
    partial: str | None = None,
    fail: str | None = None,
) -> str:
    if fail:
        return fail
    if partial:
        return partial
    if imported:
        return f"IMPORTED {company_name} (company + contact + lead)"
    if linked and updated_company:
        return f"UPDATED {company_name} (company + linked primary_contact)"
    if linked:
        return f"LINKED {company_name} (primary_contact_id)"
    if updated_company:
        return f"UPDATED {company_name} (company fields)"
    if skipped:
        return f"SKIP duplicate: {company_name}"
    return f"SKIP duplicate: {company_name}"
