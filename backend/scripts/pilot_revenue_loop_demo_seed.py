"""Seed synthetic demo data for pilot revenue loop rehearsal.

Uses clearly fake customer names — not production data.
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import ManufacturingPartner, ProductCatalog, User
from app.models.customer_project_requests import CustomerProjectRequest
from app.models.enums import CustomerProjectRequestStatus
from app.schemas.customer_project_request_domain import ProjectRequirementFields
from app.services.customer_project_requests.intake_service import build_fit_summary, compute_completeness
from app.services.customer_project_requests.workspace_service import create_admin_request
from app.schemas.customer_project_request_domain import CustomerProjectRequestCreate


MARKER_REF = "CPR-PILOT-DEMO-001"


def main() -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email.isnot(None)).first()
        if not user:
            print("No user found — run bootstrap first.")
            return 1

        existing = (
            db.query(CustomerProjectRequest)
            .filter(CustomerProjectRequest.request_reference == MARKER_REF)
            .first()
        )
        if existing:
            print(f"Demo project request already exists: {MARKER_REF}")
            return 0

        hosun = db.query(ManufacturingPartner).filter(ManufacturingPartner.partner_code == "HOSUN").first()
        catalog = None
        if hosun:
            catalog = (
                db.query(ProductCatalog)
                .filter(ProductCatalog.partner_id == hosun.id, ProductCatalog.status == "active")
                .first()
            )

        body = CustomerProjectRequestCreate(
            customer_name="Pilot Demo Buyer",
            customer_email="pilot.demo@example.com",
            company_name_text="Staging Test Alpha Corp (Synthetic)",
            product_interest="Heavy-duty dual motor desk frame",
            sku=catalog.sku if catalog else "HS-DEMO-PRDDFZ",
            partner_id=hosun.id if hosun else None,
            product_catalog_id=catalog.id if catalog else None,
            quantity_min=20,
            quantity_max=50,
            delivery_region="California, USA",
            project_scenario="Industrial workbench project — 300kg load, low noise target",
            requirements=ProjectRequirementFields(
                load_capacity_kg=300,
                noise_db_target=48,
                stability_requirement="high lateral stability",
                width_mm=1800,
                leg_count=2,
                certifications=["CE"],
                sample_required=True,
            ),
            source="demo_seed",
            priority="normal",
        )
        row = create_admin_request(db, body, actor_id=user.id)
        row.request_reference = MARKER_REF
        row.status = CustomerProjectRequestStatus.submitted.value
        row.completeness_json = compute_completeness(row)
        row.fit_summary_json = build_fit_summary(db, row)
        db.commit()
        print(f"Created demo project request {row.request_reference} ({row.id})")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
