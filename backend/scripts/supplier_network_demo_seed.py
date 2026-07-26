"""Seed neutral synthetic demo for supplier network commercial loop."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import (
    BenchmarkBrand,
    ManufacturingPartner,
    ProductCatalog,
    SupplierDiscoveryRecord,
    User,
)
from app.models.customer_project_requests import CustomerProjectRequest
from app.models.enums import CustomerProjectRequestStatus, PartnerLifecycle, SupplierDiscoveryStatus
from app.schemas.customer_project_request_domain import CustomerProjectRequestCreate, ProjectRequirementFields
from app.services.customer_project_requests.multi_supplier_fit_service import refresh_supplier_candidates
from app.services.customer_project_requests.workspace_service import create_admin_request
from app.services.partner_lifecycle import get_default_lifting_partner
from app.services.supplier_discovery_service import init_qualification_json

MARKER_REF = "CPR-SUPPLIER-NET-DEMO-001"


def _ensure_partner(
    db,
    *,
    code: str,
    name: str,
    lifecycle: str,
    partner_type: str,
    actor_id,
) -> ManufacturingPartner:
    row = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == code).first()
    if row:
        row.lifecycle_status = lifecycle
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


def _ensure_catalog(db, partner: ManufacturingPartner, sku: str, name: str, attrs: dict, actor_id, *, category: str) -> ProductCatalog:
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


def main() -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email.isnot(None)).first()
        if not user:
            print("No user — run bootstrap first.")
            return 1

        lift_active = _ensure_partner(
            db,
            code="LIFT-DEMO",
            name="Neutral Lifting Demo Supplier",
            lifecycle=PartnerLifecycle.active.value,
            partner_type="Lifting System Manufacturer",
            actor_id=user.id,
        )
        edu_candidate = _ensure_partner(
            db,
            code="EDU-CANDIDATE",
            name="Education Furniture Candidate (Synthetic)",
            lifecycle=PartnerLifecycle.candidate.value,
            partner_type="Education Furniture Manufacturer",
            actor_id=user.id,
        )
        office_paused = _ensure_partner(
            db,
            code="OFFICE-PAUSED",
            name="Contract Office Supplier (Paused)",
            lifecycle=PartnerLifecycle.paused.value,
            partner_type="Office Furniture Manufacturer",
            actor_id=user.id,
        )
        _ensure_partner(
            db,
            code="HOSUN",
            name="HOSUN Legacy",
            lifecycle=PartnerLifecycle.legacy.value,
            partner_type="Lifting System Manufacturer",
            actor_id=user.id,
        )

        _ensure_catalog(
            db,
            lift_active,
            "LIFT-HRD-300",
            "Dual Motor Frame 300kg",
            {"load_capacity_kg": 300, "noise_db": 45, "stroke_range_mm": "650-1250"},
            user.id,
            category="Lifting Systems",
        )
        _ensure_catalog(
            db,
            edu_candidate,
            "EDU-DESK-01",
            "Adjustable School Desk",
            {"catalog_pending": True},
            user.id,
            category="Education Furniture",
        )
        _ensure_catalog(
            db,
            office_paused,
            "OFF-DESK-01",
            "Contract Desk",
            {"load_capacity_kg": 100},
            user.id,
            category="Office Furniture",
        )

        if not db.query(BenchmarkBrand).filter(BenchmarkBrand.brand_code == "LINAK-BENCH").first():
            db.add(
                BenchmarkBrand(
                    brand_code="LINAK-BENCH",
                    display_name="LINAK (Benchmark Reference Only)",
                    industry_vertical="lifting_systems",
                    relationship_disclaimer="Industry benchmark — not a PartnerOS supplier",
                    review_status="verified",
                    is_active=True,
                    created_by_id=user.id,
                    updated_by_id=user.id,
                )
            )

        if not db.query(SupplierDiscoveryRecord).filter(SupplierDiscoveryRecord.company_name == "Synth Discover Co").first():
            db.add(
                SupplierDiscoveryRecord(
                    company_name="Synth Discover Co",
                    country="CN",
                    categories=["lifting_systems"],
                    capabilities=["OEM desk frames"],
                    status=SupplierDiscoveryStatus.evaluating.value,
                    data_source="manual",
                    qualification_json=init_qualification_json(),
                    owner_user_id=user.id,
                    created_by_id=user.id,
                    updated_by_id=user.id,
                )
            )

        existing = (
            db.query(CustomerProjectRequest)
            .filter(CustomerProjectRequest.request_reference == MARKER_REF)
            .first()
        )
        if not existing:
            lift_partner = get_default_lifting_partner(db)
            catalog = (
                db.query(ProductCatalog)
                .filter(ProductCatalog.partner_id == lift_partner.id, ProductCatalog.status == "active")
                .first()
                if lift_partner
                else None
            )
            body = CustomerProjectRequestCreate(
                customer_name="Supplier Network Demo Buyer",
                customer_email="supplier.net.demo@example.com",
                company_name_text="Neutral Demo Corp (Synthetic)",
                product_interest="Heavy-duty dual motor desk frame",
                sku=catalog.internal_sku if catalog else "LIFT-HRD-300",
                partner_id=lift_partner.id if lift_partner else None,
                product_catalog_id=catalog.id if catalog else None,
                quantity_min=20,
                quantity_max=50,
                delivery_region="California, USA",
                project_scenario="No-HOSUN supplier network demo project",
                requirements=ProjectRequirementFields(
                    load_capacity_kg=300,
                    noise_db_target=48,
                    stability_requirement="high lateral stability",
                    width_mm=1800,
                    leg_count=2,
                    certifications=["CE"],
                    sample_required=True,
                ),
                source="supplier_network_demo",
                priority="normal",
            )
            row = create_admin_request(db, body, actor_id=user.id)
            row.request_reference = MARKER_REF
            row.status = CustomerProjectRequestStatus.submitted.value
            refresh_supplier_candidates(db, row, actor_id=user.id)
            db.commit()
            print(f"Created demo CPR {MARKER_REF}")
        else:
            print(f"Demo CPR already exists: {MARKER_REF}")

        db.commit()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
