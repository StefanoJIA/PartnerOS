"""Build quote input contract from DB (D5.19 read-only)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Contact, Lead
from app.services.a_domain.product_fit_board import build_product_fit_for_lead
from app.services.a_domain.quote_handoff_board import build_quote_handoff_for_lead
from app.services.a_domain.quote_input_contract import QuoteInputContractInput, build_quote_input_contract


def build_quote_input_contract_for_lead(db: Session, lead_id: UUID) -> dict[str, Any] | None:
    handoff = build_quote_handoff_for_lead(db, lead_id)
    fit = build_product_fit_for_lead(db, lead_id)
    if not handoff or not fit:
        return None

    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    company = db.query(Company).filter(Company.id == lead.company_id).first() if lead else None
    contact = None
    if lead and lead.primary_contact_id:
        contact = db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()

    contact_name = None
    if contact:
        contact_name = f"{contact.first_name} {contact.last_name}".strip() or None

    has_contact = bool(
        contact
        and (
            (contact.email and contact.email.strip())
            or (contact.linkedin_url and contact.linkedin_url.strip())
            or (company and company.linkedin_url and company.linkedin_url.strip())
        )
    )

    notes_parts = [
        company.notes if company else None,
        company.business_description if company else None,
        lead.notes if lead else None,
        lead.product_interest if lead else None,
    ]
    notes_blob = " ".join(p for p in notes_parts if p).lower()

    inp = QuoteInputContractInput(
        lead_id=str(lead_id),
        company_name=handoff.get("company_name", ""),
        contact_name=contact_name,
        has_contact_method=has_contact,
        handoff=handoff,
        product_fit=fit,
        notes_blob=notes_blob,
        lead_product_interest=lead.product_interest if lead else None,
        expected_timeline=lead.expected_timeline if lead else None,
        estimated_value=str(lead.estimated_value) if lead and lead.estimated_value is not None else None,
    )
    return build_quote_input_contract(inp)


def build_quote_input_contract_board_rows(db: Session) -> list[dict[str, Any]]:
    leads = db.query(Lead).filter(Lead.is_active.is_(True)).order_by(Lead.created_at.desc()).all()
    rows: list[dict[str, Any]] = []
    for lead in leads:
        contract = build_quote_input_contract_for_lead(db, lead.id)
        if not contract:
            continue
        rows.append(
            {
                "lead_id": contract["lead_id"],
                "company_name": contract["company_name"],
                "handoff_status": contract["handoff_status"],
                "quote_module_readiness": contract["quote_module_readiness"],
                "recommended_partner_route": contract.get("recommended_partner_route") or [],
                "missing_requirements_count": len(
                    contract.get("quote_input_fields", {}).get("missing_requirements") or []
                ),
            }
        )
    return rows


def summarize_quote_input_contract_board(rows: list[dict[str, Any]]) -> dict[str, int]:
    def _has_route(row: dict[str, Any], route: str) -> bool:
        return route in (row.get("recommended_partner_route") or [])

    return {
        "total": len(rows),
        "ready_for_phase2_quote_draft": sum(
            1 for r in rows if r.get("quote_module_readiness") == "ready_for_phase2_quote_draft"
        ),
        "needs_more_customer_info": sum(
            1 for r in rows if r.get("quote_module_readiness") == "needs_more_customer_info"
        ),
        "not_quote_ready": sum(1 for r in rows if r.get("quote_module_readiness") == "not_quote_ready"),
        "lifting_system_route": sum(1 for r in rows if _has_route(r, "hosun_lifting_systems")),
        "jooboo_route": sum(1 for r in rows if _has_route(r, "jooboo_education_furniture")),
        "project_supply_route": sum(1 for r in rows if _has_route(r, "project_supply")),
        "oem_odm_route": sum(1 for r in rows if _has_route(r, "oem_odm_components")),
    }


def build_quote_input_contract_board(db: Session) -> dict[str, Any]:
    rows = build_quote_input_contract_board_rows(db)
    return {
        "summary": summarize_quote_input_contract_board(rows),
        "rows": rows,
        "warnings": [],
        "degraded": False,
    }
