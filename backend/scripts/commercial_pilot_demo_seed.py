"""Seed three commercial pilot runs with full synthetic loop artifacts."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import ManufacturingPartner, ProductCatalog, User
from app.models.customer_project_requests import CustomerProjectRequest
from app.models.enums import CustomerProjectRequestStatus, PartnerLifecycle
from app.models.project_request_candidates import ProjectRequestSupplierCandidate
from app.schemas.customer_project_request_domain import CustomerProjectRequestCreate, ProjectRequirementFields
from app.services.commercial_pilot_service import (
    build_category_coverage,
    build_pilot_gap_tasks,
    ensure_pilot_run,
    link_pilot_artifacts,
    update_pilot_status,
)
from app.services.customer_project_requests.market_signal_service import promote_market_signal_to_review
from app.services.customer_project_requests.multi_supplier_fit_service import (
    record_candidate_decision,
    refresh_supplier_candidates,
)
from app.services.customer_project_requests.workspace_service import create_admin_request
from app.services.partner_lifecycle import get_default_lifting_partner
from app.services.quotes.pdf_generator import generate_quote_pdf
from app.services.quotes.quote_service import create_quote
from app.services.supplier_network_service import freeze_selection_snapshot

PILOT_SPECS = [
    {
        "pilot_code": "PILOT-LIFT-001",
        "pilot_name": "Commercial Pilot — Lifting 300kg Multi-leg",
        "industry_vertical": "lifting_systems",
        "marker_ref": "CPR-PILOT-LIFT-001",
        "synthetic_customer_json": {
            "customer_name": "Pilot Lifting Buyer (Synthetic)",
            "customer_email": "pilot.lift@example.com",
            "company_name": "Heavy Load Workspace Inc (Synthetic)",
        },
        "requirements_json": {
            "load_capacity_kg": 300,
            "noise_db_target": 48,
            "stability_requirement": "high lateral stability",
            "width_mm": 2000,
            "leg_count": 4,
            "mounting_holes": "custom pattern",
            "certifications": ["CE"],
            "sample_required": True,
        },
        "project_scenario": "300kg low-noise multi-leg stability custom mounting",
        "product_interest": "Heavy-duty quad-leg desk frame",
        "sku_key": "LIFT",
        "partner_code": "LIFT-DEMO",
    },
    {
        "pilot_code": "PILOT-EDU-001",
        "pilot_name": "Commercial Pilot — Education Classroom",
        "industry_vertical": "education_furniture",
        "marker_ref": "CPR-PILOT-EDU-001",
        "synthetic_customer_json": {
            "customer_name": "Pilot Education Buyer (Synthetic)",
            "customer_email": "pilot.edu@example.com",
            "company_name": "District Schools Procurement (Synthetic)",
        },
        "requirements_json": {
            "ada_compliance": True,
            "mobility": "casters optional",
            "durability": "high cycle classroom use",
            "color_finish": "multiple laminate options",
            "lead_time_days_max": 90,
            "certifications": ["UNKNOWN"],
            "sample_required": True,
        },
        "project_scenario": "Classroom desks/chairs mobility durability ADA color project lead time",
        "product_interest": "Adjustable classroom desk and chair set",
        "sku_key": "EDU",
        "partner_code": "EDU-DEMO-ACTIVE",
    },
    {
        "pilot_code": "PILOT-OFFICE-001",
        "pilot_name": "Commercial Pilot — Contract Office",
        "industry_vertical": "contract_office",
        "marker_ref": "CPR-PILOT-OFFICE-001",
        "synthetic_customer_json": {
            "customer_name": "Pilot Office Buyer (Synthetic)",
            "customer_email": "pilot.office@example.com",
            "company_name": "Corporate Workplace LLC (Synthetic)",
        },
        "requirements_json": {
            "finishes": "premium laminate and edge banding",
            "quick_delivery": True,
            "install_support": True,
            "certifications": ["BIFMA (verify)"],
            "lead_time_days_max": 45,
        },
        "project_scenario": "Conference/workstation finishes quick delivery install certs",
        "product_interest": "Contract conference and workstation package",
        "sku_key": "OFF",
        "partner_code": "OFFICE-DEMO-ACTIVE",
    },
]


def _ensure_partner(db, *, code: str, name: str, partner_type: str, lifecycle: str, actor_id) -> ManufacturingPartner:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == code).first()
    if row:
        row.lifecycle_status = lifecycle
        row.is_active = lifecycle == PartnerLifecycle.active.value
        return row
    row = ManufacturingPartner(
        partner_code=code,
        partner_name=name,
        partner_type=partner_type,
        lifecycle_status=lifecycle,
        is_active=lifecycle == PartnerLifecycle.active.value,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(row)
    db.flush()
    return row


def _ensure_catalog(db, partner, sku: str, name: str, category: str, attrs: dict, actor_id) -> ProductCatalog:
    row = db.query(ProductCatalog).filter(ProductCatalog.internal_sku == sku).first()
    if row:
        return row
    row = ProductCatalog(
        partner_id=partner.id,
        internal_sku=sku,
        product_name=name,
        product_category=category,
        status="active",
        attributes_json=attrs,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(row)
    db.flush()
    return row


def _run_pilot(db, spec: dict, user: User) -> None:
    pilot = ensure_pilot_run(db, spec=spec, actor_id=user.id)
    partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == spec["partner_code"]).first()
    if not partner and spec["partner_code"] == "LIFT-DEMO":
        partner = get_default_lifting_partner(db)
    catalog = (
        db.query(ProductCatalog)
        .filter(ProductCatalog.partner_id == partner.id, ProductCatalog.status == "active")
        .first()
        if partner
        else None
    )

    existing = (
        db.query(CustomerProjectRequest)
        .filter(CustomerProjectRequest.request_reference == spec["marker_ref"])
        .first()
    )
    if not existing:
        req_fields = {k: v for k, v in spec["requirements_json"].items() if k in ProjectRequirementFields.model_fields}
        body = CustomerProjectRequestCreate(
            customer_name=spec["synthetic_customer_json"]["customer_name"],
            customer_email=spec["synthetic_customer_json"]["customer_email"],
            company_name_text=spec["synthetic_customer_json"]["company_name"],
            product_interest=spec["product_interest"],
            sku=catalog.internal_sku if catalog else f"{spec['sku_key']}-DEMO-001",
            partner_id=partner.id if partner else None,
            product_catalog_id=catalog.id if catalog else None,
            quantity_min=20,
            quantity_max=100,
            delivery_region="California, USA",
            project_scenario=spec["project_scenario"],
            requirements=ProjectRequirementFields(**req_fields),
            source="commercial_pilot",
            priority="high",
        )
        row = create_admin_request(db, body, actor_id=user.id)
        row.request_reference = spec["marker_ref"]
        row.requirements_json = spec["requirements_json"]
        row.status = CustomerProjectRequestStatus.submitted.value
        db.flush()
    else:
        row = existing

    refresh_supplier_candidates(db, row, actor_id=user.id)
    candidates = (
        db.query(ProjectRequestSupplierCandidate)
        .filter(ProjectRequestSupplierCandidate.project_request_id == row.id)
        .all()
    )
    pilot.candidate_summary_json = {
        "count": len(candidates),
        "eligible": sum(1 for c in candidates if c.eligible_for_formal_quote),
        "dimensions_sample": [
            {"display_name": c.display_name, "overall": c.overall_fit_status, "eligible": c.eligible_for_formal_quote}
            for c in candidates[:5]
        ],
    }

    selected = next((c for c in candidates if c.eligible_for_formal_quote), None)
    if selected:
        record_candidate_decision(db, selected, decision="selected", reason="Pilot manual selection — quote-eligible active partner", actor_id=user.id)
        freeze_selection_snapshot(db, project_request_id=row.id, selected_candidate=selected, actor_id=user.id)
        pilot.selection_json = {
            "selected_candidate_id": str(selected.id),
            "display_name": selected.display_name,
            "decision_reason": selected.decision_reason,
        }

    build_pilot_gap_tasks(db, pilot=pilot, actor_id=user.id)
    row.status = CustomerProjectRequestStatus.quote_ready.value
    db.flush()

    quote = create_quote(
        db,
        user=user,
        line_items_in=[
            {
                "product_catalog_id": str(catalog.id) if catalog else None,
                "internal_sku": catalog.internal_sku if catalog else f"{spec['sku_key']}-DEMO-001",
                "product_name": spec["product_interest"],
                "quantity": 30,
                "manual_interval_quote_table": [
                    {"min_qty": 1, "max_qty": 49, "fob_unit_price": "120.00", "ddp_unit_price": "145.00"},
                    {"min_qty": 50, "max_qty": None, "fob_unit_price": "108.00", "ddp_unit_price": "132.00"},
                ],
            }
        ],
        internal_notes="SCENARIO PRICING — block external send until real cost verified",
        customer_notes="Interval pricing for pilot validation only.",
    )
    row.quote_id = quote.id
    pdf_export = generate_quote_pdf(db, quote_id=quote.id, user=user, export_type="customer_pdf")
    review = promote_market_signal_to_review(db, row, actor_id=user.id)

    link_pilot_artifacts(
        db,
        pilot=pilot,
        project_request_id=row.id,
        quote_id=quote.id,
        market_response_review_id=review.id,
    )
    update_pilot_status(db, pilot, "mr_pending")
    pilot.result_summary = (
        f"Pilot complete with {len(candidates)} candidates, scenario quote {quote.quote_number}, "
        f"PDF export {pdf_export.get('export_id')}, MR review pending operator approval."
    )
    pilot.scenario_pricing_blocked = True


def main() -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email.isnot(None)).first()
        if not user:
            print("No user — run bootstrap first.")
            return 1

        _ensure_partner(
            db,
            code="LIFT-DEMO",
            name="Neutral Lifting Demo Supplier",
            partner_type="Lifting System Manufacturer",
            lifecycle=PartnerLifecycle.active.value,
            actor_id=user.id,
        )
        edu = _ensure_partner(
            db,
            code="EDU-DEMO-ACTIVE",
            name="Education Demo Supplier (Synthetic Active)",
            partner_type="Education Furniture Manufacturer",
            lifecycle=PartnerLifecycle.active.value,
            actor_id=user.id,
        )
        office = _ensure_partner(
            db,
            code="OFFICE-DEMO-ACTIVE",
            name="Contract Office Demo Supplier (Synthetic Active)",
            partner_type="Office Furniture Manufacturer",
            lifecycle=PartnerLifecycle.active.value,
            actor_id=user.id,
        )
        _ensure_catalog(
            db,
            _ensure_partner(db, code="LIFT-DEMO", name="LIFT", partner_type="L", lifecycle="active", actor_id=user.id),
            "LIFT-HRD-300",
            "Dual Motor Frame 300kg",
            "Lifting Systems",
            {"load_capacity_kg": 300, "noise_db": 45, "leg_count": 4},
            user.id,
        )
        _ensure_catalog(
            db,
            edu,
            "EDU-CLASS-01",
            "Classroom Desk Chair Set",
            "Education Furniture",
            {"ada_compliant": True, "mobility": "optional casters"},
            user.id,
        )
        _ensure_catalog(
            db,
            office,
            "OFF-CONF-01",
            "Conference Workstation Package",
            "Office Furniture",
            {"quick_ship": True, "install_support": True},
            user.id,
        )

        for industry in ("lifting_systems", "education_furniture", "contract_office"):
            build_category_coverage(db, industry_vertical=industry, actor_id=user.id)

        for spec in PILOT_SPECS:
            _run_pilot(db, spec, user)
            print(f"Pilot seeded: {spec['pilot_code']} -> {spec['marker_ref']}")

        db.commit()
        print("COMMERCIAL_PILOT_DEMO: OK")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"COMMERCIAL_PILOT_DEMO: FAIL — {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
