"""D5.5 — apply manual contact research updates (company/contact/lead + touchpoint)."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Contact, Interaction, Lead, User
from app.services.activity import log_activity
from app.services.a_domain.lead_completeness_board import build_lead_completeness_row_for_lead
from app.services.a_domain.lead_import_apply import match_existing_contact
from app.services.a_domain.lead_import_intake import split_contact_name


def _non_empty(value: str | None) -> str | None:
    if value is None:
        return None
    s = value.strip()
    return s if s else None


def _patch_company_fields(company: Company, data: dict[str, str | None]) -> dict[str, Any]:
    changed: dict[str, Any] = {}
    website = _non_empty(data.get("website"))
    if website and not (company.website or "").strip():
        company.website = website
        changed["website"] = website
    company_type = _non_empty(data.get("company_type"))
    if company_type and not (company.company_type or "").strip():
        company.company_type = company_type
        changed["company_type"] = company_type
    notes = _non_empty(data.get("notes"))
    if notes:
        stamp = date.today().isoformat()
        block = f"[Contact Research {stamp}] {notes}"
        if (company.notes or "").strip():
            company.notes = f"{company.notes.rstrip()}\n\n{block}"
        else:
            company.notes = block
        changed["notes_appended"] = True
    return changed


def _contacts_cache(db: Session, company_id: UUID) -> list[dict]:
    rows = db.query(Contact).filter(Contact.company_id == company_id, Contact.is_active.is_(True)).all()
    return [
        {
            "id": str(c.id),
            "company_id": str(c.company_id),
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
        }
        for c in rows
    ]


def _update_contact_fields(contact: Contact, data: dict[str, str | None]) -> dict[str, Any]:
    changed: dict[str, Any] = {}
    name = _non_empty(data.get("name"))
    if name:
        first, last = split_contact_name(name)
        contact.first_name = first
        contact.last_name = last
        changed["first_name"] = first
        changed["last_name"] = last
    for field, key in (("title", "title"), ("email", "email"), ("phone", "phone"), ("linkedin_url", "linkedin_url")):
        val = _non_empty(data.get(key))
        if val:
            setattr(contact, field, val)
            changed[field] = val
    return changed


def _resolve_or_create_contact(
    db: Session,
    user: User,
    company: Company,
    lead: Lead,
    data: dict[str, str | None],
) -> tuple[Contact | None, bool, dict[str, Any]]:
    """Return (contact, created, diff)."""
    name = _non_empty(data.get("name"))
    email = _non_empty(data.get("email"))
    if not name and not email and not lead.primary_contact_id:
        return None, False, {}

    cache = _contacts_cache(db, company.id)
    row = {
        "contact_name": name or "",
        "contact_email": email or "",
        "contact_title": data.get("title") or "",
        "contact_phone": data.get("phone") or "",
        "linkedin_url": data.get("linkedin_url") or "",
    }

    if lead.primary_contact_id:
        contact = db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()
        if contact:
            return contact, False, _update_contact_fields(contact, data)

    if name or email:
        existing_id = match_existing_contact(cache, str(company.id), row)
        if existing_id:
            contact = db.query(Contact).filter(Contact.id == UUID(existing_id)).first()
            if contact:
                return contact, False, _update_contact_fields(contact, data)

    if not name:
        return None, False, {}

    first, last = split_contact_name(name)
    contact = Contact(
        first_name=first,
        last_name=last,
        company_id=company.id,
        title=_non_empty(data.get("title")),
        email=email,
        phone=_non_empty(data.get("phone")),
        linkedin_url=_non_empty(data.get("linkedin_url")),
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(contact)
    db.flush()
    return contact, True, {"created": True}


def apply_contact_research(
    db: Session,
    user: User,
    lead_id: UUID,
    *,
    company_data: dict[str, str | None] | None,
    contact_data: dict[str, str | None] | None,
    lead_data: dict[str, str | None] | None,
    touchpoint_note: str | None,
) -> dict[str, Any]:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    if not lead:
        raise ValueError("Lead not found")
    company = db.query(Company).filter(Company.id == lead.company_id).first()
    if not company:
        raise ValueError("Company not found")

    company_diff = _patch_company_fields(company, company_data or {})
    if company_diff:
        company.updated_by_id = user.id

    contact, contact_created, contact_diff = _resolve_or_create_contact(
        db, user, company, lead, contact_data or {}
    )
    if contact:
        lead.primary_contact_id = contact.id
        contact.updated_by_id = user.id

    next_action = _non_empty((lead_data or {}).get("next_action"))
    if next_action:
        lead.next_action = next_action
    lead.updated_by_id = user.id

    note = _non_empty(touchpoint_note) or "Updated contact research information manually."
    summary = f"{note} [manually_researched=true]"
    intr = Interaction(
        related_object_type="lead",
        related_object_id=lead.id,
        interaction_type="contact_research",
        channel="manual_research",
        subject="Contact research",
        summary=summary,
        direction="internal",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(intr)
    db.flush()

    if company_diff:
        log_activity(
            db,
            object_type="company",
            object_id=company.id,
            action="contact_research_company_updated",
            actor_id=user.id,
            diff=company_diff,
        )
    if contact and contact_created:
        log_activity(
            db,
            object_type="contact",
            object_id=contact.id,
            action="contact_research_contact_created",
            actor_id=user.id,
        )
    elif contact and contact_diff:
        log_activity(
            db,
            object_type="contact",
            object_id=contact.id,
            action="contact_research_contact_updated",
            actor_id=user.id,
            diff=contact_diff,
        )
    log_activity(
        db,
        object_type="lead",
        object_id=lead.id,
        action="contact_research_touchpoint",
        actor_id=user.id,
        diff={"interaction_id": str(intr.id)},
    )

    db.commit()
    db.refresh(intr)

    completeness = build_lead_completeness_row_for_lead(db, lead.id)
    return {
        "lead_id": str(lead.id),
        "interaction_id": str(intr.id),
        "completeness": completeness,
    }
