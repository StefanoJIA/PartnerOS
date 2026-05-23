"""Lead CSV preview + apply orchestration (D5.3 — shared by API and CLI)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Contact, Lead, User
from app.services.activity import log_activity
from app.services.a_domain.lead_import_apply import (
    build_contact_create_payload,
    build_lead_link_payload,
    match_existing_contact,
)
from app.services.a_domain.lead_import_intake import (
    first_semicolon_token,
    parse_csv_text,
    preview_row,
    validate_headers,
)

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

TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3].parent / "docs" / "templates" / "lead_import_template.csv"
)


@dataclass
class LeadIntakePreviewRow:
    row_number: int
    company_name: str
    contact_name: str
    website: str
    company_type: str
    source: str
    likely_segments: list[str]
    priority_hint: str
    missing_fields: list[str]
    duplicate_status: str  # new | possible_duplicate | existing
    recommended_next_action: str
    status: str  # ok | warn | error
    warnings: list[str] = field(default_factory=list)


@dataclass
class LeadIntakePreviewSummary:
    total: int
    ok: int
    warnings: int
    errors: int
    duplicates: int
    ready_to_import: int


@dataclass
class LeadIntakePreviewResult:
    rows: list[LeadIntakePreviewRow]
    summary: LeadIntakePreviewSummary
    header_warnings: list[str] = field(default_factory=list)


@dataclass
class LeadIntakeApplyResult:
    created_companies: int
    skipped_duplicates: int
    created_contacts: int
    linked_leads: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class _RowApplyStats:
    company_created: bool = False
    contact_created: bool = False
    lead_created: bool = False
    lead_linked: bool = False
    skipped_duplicate: bool = False


def get_template_csv() -> str:
    if TEMPLATE_PATH.is_file():
        return TEMPLATE_PATH.read_text(encoding="utf-8-sig")
    return (
        "company_name,website,company_type,industry,city,state,country,"
        "contact_name,contact_title,contact_email,contact_phone,linkedin_url,"
        "source,notes,initial_interest,priority,next_action\n"
    )


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


def load_duplicate_company_names(db: Session) -> set[str]:
    names = (
        db.query(Company.company_name)
        .filter(Company.is_active.is_(True))
        .all()
    )
    return {n[0] for n in names if n[0]}


def _contacts_cache(db: Session) -> list[dict]:
    rows = db.query(Contact).filter(Contact.is_active.is_(True)).all()
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


def _duplicate_status(
    company_name: str,
    *,
    crm_names: set[str],
    seen_in_csv: set[str],
) -> str:
    if company_name in crm_names:
        return "existing"
    if company_name in seen_in_csv:
        return "possible_duplicate"
    return "new"


def _preview_single_row(
    row: dict[str, str],
    row_number: int,
    *,
    crm_names: set[str],
    seen_in_csv: set[str],
) -> LeadIntakePreviewRow:
    name = row.get("company_name", "").strip()
    contact_name = first_semicolon_token(row.get("contact_name", ""))
    warnings: list[str] = []

    if not name:
        return LeadIntakePreviewRow(
            row_number=row_number,
            company_name="",
            contact_name=contact_name,
            website=row.get("website", ""),
            company_type=row.get("company_type", ""),
            source=row.get("source", ""),
            likely_segments=[],
            priority_hint="low",
            missing_fields=["company_name"],
            duplicate_status="new",
            recommended_next_action="Fix row — company_name is required",
            status="error",
            warnings=["company_name is required"],
        )

    dup = _duplicate_status(name, crm_names=crm_names, seen_in_csv=seen_in_csv)
    seen_in_csv.add(name)

    preview = preview_row(row, duplicate_names=crm_names)
    status = preview.status.lower()
    if dup in ("existing", "possible_duplicate"):
        warnings.append(f"Duplicate: {dup.replace('_', ' ')}")

    return LeadIntakePreviewRow(
        row_number=row_number,
        company_name=name,
        contact_name=contact_name,
        website=row.get("website", ""),
        company_type=row.get("company_type", ""),
        source=row.get("source", ""),
        likely_segments=preview.likely_segments,
        priority_hint=preview.priority_hint,
        missing_fields=preview.missing_fields,
        duplicate_status=dup,
        recommended_next_action=preview.recommended_next_action,
        status=status,
        warnings=warnings,
    )


def preview_lead_csv_text(db: Session, csv_text: str) -> LeadIntakePreviewResult:
    headers, rows = parse_csv_text(csv_text)
    header_missing = validate_headers(headers)
    header_warnings = [f"missing column: {c}" for c in header_missing]
    crm_names = load_duplicate_company_names(db)
    seen_in_csv: set[str] = set()

    preview_rows = [
        _preview_single_row(row, i + 1, crm_names=crm_names, seen_in_csv=seen_in_csv)
        for i, row in enumerate(rows)
    ]

    ok = sum(1 for r in preview_rows if r.status == "ok")
    warn = sum(1 for r in preview_rows if r.status == "warn")
    err = sum(1 for r in preview_rows if r.status == "error")
    dup = sum(1 for r in preview_rows if r.duplicate_status in ("existing", "possible_duplicate"))
    ready = sum(1 for r in preview_rows if r.status in ("ok", "warn"))

    return LeadIntakePreviewResult(
        rows=preview_rows,
        summary=LeadIntakePreviewSummary(
            total=len(preview_rows),
            ok=ok,
            warnings=warn,
            errors=err,
            duplicates=dup,
            ready_to_import=ready,
        ),
        header_warnings=header_warnings,
    )


def _find_company_by_name(db: Session, name: str) -> Company | None:
    return (
        db.query(Company)
        .filter(Company.company_name == name, Company.is_active.is_(True))
        .first()
    )


def _find_lead_for_company(db: Session, company_id: UUID) -> Lead | None:
    return (
        db.query(Lead)
        .filter(Lead.company_id == company_id, Lead.is_active.is_(True))
        .order_by(Lead.created_at.desc())
        .first()
    )


def _maybe_patch_company(db: Session, company: Company, row: dict[str, str], user: User) -> bool:
    patch: dict = {}
    if row.get("notes") and not company.business_description:
        patch["business_description"] = row.get("notes")
        patch["notes"] = row.get("notes")
    if row.get("initial_interest") and not company.product_interest_tags:
        patch["product_interest_tags"] = row.get("initial_interest")
    for csv_field, model_field in (
        ("city", "city"),
        ("state", "state"),
        ("industry", "industry"),
        ("company_type", "company_type"),
    ):
        if row.get(csv_field) and not getattr(company, model_field, None):
            patch[model_field] = row.get(csv_field)
    if not patch:
        return False
    for k, v in patch.items():
        setattr(company, k, v)
    company.updated_by_id = user.id
    db.commit()
    db.refresh(company)
    log_activity(db, object_type="company", object_id=company.id, action="company_updated", actor_id=user.id, diff=patch)
    db.commit()
    return True


def _ensure_contact(
    db: Session,
    user: User,
    company_id: UUID,
    row: dict[str, str],
    contacts: list[dict],
) -> tuple[str | None, bool]:
    existing_id = match_existing_contact(contacts, str(company_id), row)
    if existing_id:
        return existing_id, False
    cp = build_contact_create_payload(str(company_id), row)
    if not cp:
        return None, False
    cp.pop("company_id", None)
    contact = Contact(
        **cp,
        company_id=company_id,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    contacts.append(
        {
            "id": str(contact.id),
            "company_id": str(company_id),
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
        }
    )
    log_activity(db, object_type="contact", object_id=contact.id, action="contact_created", actor_id=user.id)
    db.commit()
    return str(contact.id), True


def _apply_row_db(
    db: Session,
    user: User,
    row: dict[str, str],
    recommended_next_action: str,
    crm_names: set[str],
    contacts: list[dict],
) -> _RowApplyStats:
    stats = _RowApplyStats()
    name = row.get("company_name", "").strip()
    if not name:
        return stats

    preview = preview_row(row)
    company: Company | None = None
    contact_id: str | None = None

    if name in crm_names:
        company = _find_company_by_name(db, name)
        if not company:
            stats.skipped_duplicate = True
            return stats
        updated = _maybe_patch_company(db, company, row, user)
        contact_id, contact_created = _ensure_contact(db, user, company.id, row, contacts)
        if contact_created:
            stats.contact_created = True
        lead = _find_lead_for_company(db, company.id)
        if lead:
            lead_dict = {
                "id": str(lead.id),
                "primary_contact_id": str(lead.primary_contact_id) if lead.primary_contact_id else None,
                "next_action": lead.next_action or "",
                "lead_name": lead.lead_name,
            }
            payload = build_lead_link_payload(lead_dict, contact_id, recommended_next_action)
            if payload:
                if payload.get("primary_contact_id"):
                    lead.primary_contact_id = UUID(payload["primary_contact_id"])
                if payload.get("next_action"):
                    lead.next_action = payload["next_action"]
                lead.updated_by_id = user.id
                db.commit()
                stats.lead_linked = True
            elif updated:
                pass
            else:
                stats.skipped_duplicate = True
            return stats
    else:
        company_type = row.get("company_type") or "Other"
        company = Company(
            company_name=name,
            website=row.get("website") or None,
            linkedin_url=row.get("linkedin_url") or None,
            company_type=company_type,
            industry=row.get("industry") or None,
            city=row.get("city") or None,
            state=row.get("state") or None,
            country=row.get("country") or "United States",
            business_description=row.get("notes") or None,
            product_interest_tags=row.get("initial_interest") or None,
            source=row.get("source") or None,
            notes=row.get("notes") or None,
            priority=_normalize_priority(row.get("priority")),
            created_by_id=user.id,
            updated_by_id=user.id,
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        crm_names.add(name)
        stats.company_created = True
        log_activity(db, object_type="company", object_id=company.id, action="company_created", actor_id=user.id)
        db.commit()
        contact_id, contact_created = _ensure_contact(db, user, company.id, row, contacts)
        if contact_created:
            stats.contact_created = True

    lead_name = f"Lead — {name}"
    lead = Lead(
        lead_name=lead_name,
        company_id=company.id,
        primary_contact_id=UUID(contact_id) if contact_id else None,
        source=_map_source(row.get("source", "")),
        lead_type="Channel Lead",
        product_interest=row.get("initial_interest") or None,
        current_stage="New",
        priority=_normalize_priority(row.get("priority")) or preview.priority_hint,
        next_action=row.get("next_action") or recommended_next_action,
        notes=row.get("notes") or None,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    stats.lead_created = True
    log_activity(db, object_type="lead", object_id=lead.id, action="lead_created", actor_id=user.id)
    log_activity(
        db,
        object_type="company",
        object_id=company.id,
        action="lead_created_from_company",
        actor_id=user.id,
        diff={"lead_id": str(lead.id)},
    )
    db.commit()
    return stats


def apply_lead_csv_text(db: Session, user: User, csv_text: str, *, confirm: bool) -> LeadIntakeApplyResult:
    if not confirm:
        raise ValueError("confirm must be true to import leads")

    preview = preview_lead_csv_text(db, csv_text)
    if preview.summary.errors > 0:
        raise ValueError(
            f"Cannot import: {preview.summary.errors} row(s) have errors. Fix CSV and preview again."
        )

    _, rows = parse_csv_text(csv_text)
    crm_names = load_duplicate_company_names(db)
    contacts = _contacts_cache(db)

    created_companies = 0
    skipped_duplicates = 0
    created_contacts = 0
    linked_leads = 0
    warnings: list[str] = list(preview.header_warnings)

    preview_by_row = {r.row_number: r for r in preview.rows}

    for i, row in enumerate(rows):
        pr = preview_by_row.get(i + 1)
        if not pr or pr.status == "error":
            continue
        if pr.warnings:
            warnings.extend([f"Row {pr.row_number}: {w}" for w in pr.warnings])

        stats = _apply_row_db(
            db,
            user,
            row,
            pr.recommended_next_action,
            crm_names,
            contacts,
        )
        if stats.company_created:
            created_companies += 1
        if stats.contact_created:
            created_contacts += 1
        if stats.lead_created:
            linked_leads += 1
        elif stats.lead_linked:
            linked_leads += 1
        if stats.skipped_duplicate:
            skipped_duplicates += 1

    return LeadIntakeApplyResult(
        created_companies=created_companies,
        skipped_duplicates=skipped_duplicates,
        created_contacts=created_contacts,
        linked_leads=linked_leads,
        warnings=warnings,
    )
