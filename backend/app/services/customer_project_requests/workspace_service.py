"""Operator workspace helpers for customer project requests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, CustomerProjectRequest, ManufacturingPartner, ProductCatalog, User
from app.models.enums import CustomerProjectRequestStatus
from app.schemas.customer_project_request_domain import CustomerProjectRequestCreate
from app.services.a_domain.quote_input_contract import QuoteInputContractInput, build_quote_input_contract
from app.services.activity import log_activity
from app.services.customer_project_requests.intake_service import (
    build_fit_summary,
    compute_completeness,
    create_project_request_from_site,
    requirements_to_json,
)
from app.services.customer_project_requests.market_signal_service import build_market_signal_draft


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_admin_request(db: Session, body: CustomerProjectRequestCreate, *, actor_id: UUID) -> CustomerProjectRequest:
    import uuid

    row = CustomerProjectRequest(
        request_reference=f"CPR-{uuid.uuid4().hex[:8].upper()}",
        status=CustomerProjectRequestStatus.submitted.value,
        source=body.source,
        priority=body.priority.value,
        customer_name=body.customer_name,
        customer_email=str(body.customer_email) if body.customer_email else None,
        company_name_text=body.company_name_text,
        company_id=body.company_id,
        contact_id=body.contact_id,
        partner_id=body.partner_id,
        product_catalog_id=body.product_catalog_id,
        sku=body.sku,
        product_interest=body.product_interest,
        quantity_min=body.quantity_min,
        quantity_max=body.quantity_max,
        target_price=body.target_price,
        delivery_region=body.delivery_region,
        expected_date=body.expected_date,
        project_scenario=body.project_scenario,
        requirements_json=requirements_to_json(body.requirements),
        attachment_refs=body.attachment_refs,
        submitted_at=_now(),
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(row)
    db.flush()
    row.completeness_json = compute_completeness(row)
    row.fit_summary_json = build_fit_summary(db, row)
    log_activity(db, object_type="customer_project_request", object_id=row.id, action="created", actor_id=actor_id, diff={"source": body.source})
    db.commit()
    db.refresh(row)
    return row


def update_request_status(
    db: Session,
    row: CustomerProjectRequest,
    *,
    status: CustomerProjectRequestStatus,
    actor_id: UUID,
    operator_notes: str | None = None,
) -> CustomerProjectRequest:
    old = row.status
    row.status = status.value
    row.updated_by_id = actor_id
    if operator_notes is not None:
        row.operator_notes = operator_notes
    now = _now()
    if status == CustomerProjectRequestStatus.triage and not row.triaged_at:
        row.triaged_at = now
    if status == CustomerProjectRequestStatus.quote_ready and not row.quote_ready_at:
        row.quote_ready_at = now
    if status in {CustomerProjectRequestStatus.converted, CustomerProjectRequestStatus.declined}:
        row.resolved_at = now
    log_activity(db, object_type="customer_project_request", object_id=row.id, action="status_change", actor_id=actor_id, diff={"from": old, "to": status.value})
    db.commit()
    db.refresh(row)
    return row


def assign_partner_and_sku(
    db: Session,
    row: CustomerProjectRequest,
    *,
    partner_id: UUID | None,
    product_catalog_id: UUID | None,
    sku: str | None,
    actor_id: UUID,
) -> CustomerProjectRequest:
    row.partner_id = partner_id
    row.product_catalog_id = product_catalog_id
    if sku:
        row.sku = sku
    row.updated_by_id = actor_id
    catalog = None
    if product_catalog_id:
        catalog = db.query(ProductCatalog).filter(ProductCatalog.id == product_catalog_id).first()
    row.fit_summary_json = build_fit_summary(db, row, catalog_row=catalog)
    row.completeness_json = compute_completeness(row)
    log_activity(
        db,
        object_type="customer_project_request",
        object_id=row.id,
        action="partner_sku_assigned",
        actor_id=actor_id,
        diff={"partner_id": str(partner_id) if partner_id else None, "sku": sku},
    )
    db.commit()
    db.refresh(row)
    return row


def build_quote_input_contract_for_request(db: Session, row: CustomerProjectRequest) -> dict[str, Any]:
    company_name = row.company_name_text or "Unknown company"
    if row.company_id:
        company = db.query(Company).filter(Company.id == row.company_id).first()
        if company:
            company_name = company.company_name

    fit = row.fit_summary_json or {}
    req = row.requirements_json or {}
    notes_blob = " ".join(
        filter(
            None,
            [
                row.project_scenario,
                row.operator_notes,
                str(req.get("custom_notes")),
            ],
        )
    )

    missing = row.completeness_json.get("missing_fields", []) if row.completeness_json else []
    handoff = {
        "handoff_status": "ready" if row.status == CustomerProjectRequestStatus.quote_ready.value else "needs_info",
        "recommended_partner_route": [fit.get("partner_code")] if fit.get("partner_code") else [],
        "recommended_product_scope": [row.product_interest or row.sku or "lifting project"],
        "missing_customer_info": missing,
        "customer_clarification_questions": [
            f"Please confirm {m.replace('_', ' ')}." for m in missing[:5]
        ],
        "supplier_preparation_notes": [
            m.get("suggested_validation") for m in fit.get("matches", []) if m.get("engineering_review_required")
        ][:5],
        "known_context": [f"Request reference: {row.request_reference}"],
        "sample_readiness": "needs_review",
        "quote_readiness": row.status,
    }
    product_fit = {
        "recommended_product_focus": [row.product_interest] if row.product_interest else [],
        "project_type": "lifting_project",
        "fit_overall": fit.get("overall_status"),
    }
    inp = QuoteInputContractInput(
        company_name=company_name,
        contact_name=row.customer_name,
        has_contact_method=bool(row.customer_email),
        handoff=handoff,
        product_fit=product_fit,
        notes_blob=notes_blob,
        lead_product_interest=row.product_interest,
        expected_timeline=str(row.expected_date) if row.expected_date else None,
    )
    return build_quote_input_contract(inp)


def build_detail_payload(db: Session, row: CustomerProjectRequest) -> dict[str, Any]:
    company_name = None
    if row.company_id:
        c = db.query(Company).filter(Company.id == row.company_id).first()
        company_name = c.company_name if c else None
    partner_code = None
    if row.partner_id:
        p = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == row.partner_id).first()
        partner_code = p.partner_code if p else None
    owner_email = None
    if row.owner_user_id:
        u = db.query(User).filter(User.id == row.owner_user_id).first()
        owner_email = u.email if u else None

    base = {
        **{c.name: getattr(row, c.name) for c in row.__table__.columns},
        "company_name": company_name,
        "partner_code": partner_code,
        "owner_email": owner_email,
        "completeness_pct": (row.completeness_json or {}).get("completeness_pct"),
        "fit_summary": row.fit_summary_json,
        "quote_input_contract": build_quote_input_contract_for_request(db, row),
        "market_signal_draft": build_market_signal_draft(db, row),
    }
    return base
