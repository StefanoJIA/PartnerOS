"""Supplier selection snapshot and sample evaluation services."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    ProjectRequestSupplierCandidate,
    SupplierSampleEvaluation,
    SupplierSelectionSnapshot,
)
from app.services.supplier_discovery_service import SAMPLE_TEMPLATES


def build_candidate_snapshot_payload(candidates: list[ProjectRequestSupplierCandidate]) -> dict[str, Any]:
    return {
        "candidates": [
            {
                "id": str(c.id),
                "candidate_source_type": c.candidate_source_type,
                "candidate_role": c.candidate_role,
                "display_name": c.display_name,
                "sku": c.sku,
                "fit_dimensions_json": c.fit_dimensions_json,
                "evidence_quality": c.evidence_quality,
                "overall_fit_status": c.overall_fit_status,
                "eligible_for_formal_quote": c.eligible_for_formal_quote,
                "operator_decision": c.operator_decision,
                "decision_reason": c.decision_reason,
                "is_auto_recommended": c.is_auto_recommended,
                "partner_id": str(c.partner_id) if c.partner_id else None,
            }
            for c in candidates
        ]
    }


def freeze_selection_snapshot(
    db: Session,
    *,
    project_request_id: UUID,
    selected_candidate: ProjectRequestSupplierCandidate,
    actor_id: UUID,
) -> SupplierSelectionSnapshot:
    existing = (
        db.query(SupplierSelectionSnapshot)
        .filter(SupplierSelectionSnapshot.project_request_id == project_request_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Supplier selection snapshot already frozen for this request")

    all_candidates = (
        db.query(ProjectRequestSupplierCandidate)
        .filter(ProjectRequestSupplierCandidate.project_request_id == project_request_id)
        .all()
    )
    snapshot = SupplierSelectionSnapshot(
        project_request_id=project_request_id,
        selected_candidate_id=selected_candidate.id,
        snapshot_json=build_candidate_snapshot_payload(all_candidates),
        selected_by_id=actor_id,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(snapshot)
    db.flush()
    return snapshot


def get_selection_snapshot(db: Session, project_request_id: UUID) -> SupplierSelectionSnapshot | None:
    return (
        db.query(SupplierSelectionSnapshot)
        .filter(SupplierSelectionSnapshot.project_request_id == project_request_id)
        .first()
    )


def create_sample_evaluation(
    db: Session,
    *,
    template_key: str,
    supplier_discovery_id: UUID | None = None,
    partner_id: UUID | None = None,
    project_request_id: UUID | None = None,
    product_catalog_id: UUID | None = None,
    request_date: date | None = None,
    actor_id: UUID,
) -> SupplierSampleEvaluation:
    items = list(SAMPLE_TEMPLATES.get(template_key, SAMPLE_TEMPLATES["generic"]))
    row = SupplierSampleEvaluation(
        template_key=template_key,
        supplier_discovery_id=supplier_discovery_id,
        partner_id=partner_id,
        project_request_id=project_request_id,
        product_catalog_id=product_catalog_id,
        request_date=request_date,
        test_items_json=[{"key": key, "label": key.replace("_", " ").title()} for key in items],
        results_json={key: {"status": "pending", "notes": None} for key in items},
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(row)
    db.flush()
    return row
