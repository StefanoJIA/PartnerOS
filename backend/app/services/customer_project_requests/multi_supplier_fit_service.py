"""Multi-supplier fit matching for project requests."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import (
    BenchmarkBrand,
    CustomerProjectRequest,
    ManufacturingPartner,
    ProductCatalog,
    ProjectRequestSupplierCandidate,
    SupplierDiscoveryRecord,
)
from app.models.enums import CandidateRole, CandidateSourceType, PartnerLifecycle
from app.models.project_request_candidates import ProjectRequestSupplierCandidate as CandidateModel
from app.services.customer_project_requests.intake_service import LIFTING_MATCH_DIMENSIONS, _match_status_for_dimension
from app.services.partner_lifecycle import (
    is_partner_default_recommendable,
    is_partner_selectable_for_new_quote,
    normalize_lifecycle,
)


FIT_DIMENSION_KEYS = ("capability", "commercial", "compliance", "delivery")


def _build_dimension_fits(
    requirement_map: dict[str, Any],
    catalog_attrs: dict[str, Any],
    *,
    partner_pending: bool,
) -> dict[str, dict[str, Any]]:
    """Map lifting dimensions into capability/commercial/compliance/delivery buckets."""
    lifting_matches = []
    for dim_key, label, _cap in LIFTING_MATCH_DIMENSIONS:
        result = _match_status_for_dimension(
            dim_key,
            requirement_map.get(dim_key),
            catalog_attrs,
            partner_pending=partner_pending,
        )
        lifting_matches.append({"dimension": dim_key, "label": label, **result})

    def _aggregate(keys: tuple[str, ...]) -> dict[str, Any]:
        subset = [m for m in lifting_matches if m["dimension"] in keys]
        statuses = [m["match_status"] for m in subset]
        if partner_pending or not subset:
            status = "UNKNOWN"
        elif "NOT_SUPPORTED" in statuses:
            status = "NOT_SUPPORTED"
        elif all(s == "MATCH" for s in statuses if s != "UNKNOWN"):
            status = "MATCH"
        elif "MATCH" in statuses or "PARTIAL" in statuses:
            status = "PARTIAL"
        else:
            status = "UNKNOWN"
        return {
            "match_status": status,
            "dimensions": subset,
            "evidence_quality": "high" if status == "MATCH" else "medium" if status == "PARTIAL" else "low",
        }

    return {
        "capability": _aggregate(
            ("heavy_load", "high_stability", "extra_wide_multi_leg", "stroke_range", "speed_duty", "controller")
        ),
        "commercial": _aggregate(("sample_validation", "lead_time", "warranty")),
        "compliance": _aggregate(("certification", "medical_industrial", "anti_collision")),
        "delivery": _aggregate(("finish_color", "lead_time")),
    }


def _overall_from_dimensions(dims: dict[str, dict[str, Any]]) -> str:
    statuses = [dims[k]["match_status"] for k in FIT_DIMENSION_KEYS]
    if "NOT_SUPPORTED" in statuses:
        return "NOT_SUPPORTED"
    if all(s == "MATCH" for s in statuses if s != "UNKNOWN"):
        return "MATCH"
    if "MATCH" in statuses or "PARTIAL" in statuses:
        return "PARTIAL"
    return "UNKNOWN"


def _eligible_for_formal_quote(source_type: str, partner: ManufacturingPartner | None, pending: bool) -> bool:
    if source_type == CandidateSourceType.benchmark.value:
        return False
    if source_type == CandidateSourceType.supplier_discovery.value:
        return False
    if pending:
        return False
    if partner and not is_partner_selectable_for_new_quote(partner):
        return False
    return source_type == CandidateSourceType.partner.value


def build_partner_candidate(
    db: Session,
    row: CustomerProjectRequest,
    catalog: ProductCatalog,
    partner: ManufacturingPartner,
) -> dict[str, Any]:
    req = row.requirements_json or {}
    catalog_attrs = catalog.attributes_json if isinstance(catalog.attributes_json, dict) else {}
    partner_pending = bool(catalog_attrs.get("is_pending") or catalog_attrs.get("catalog_pending"))
    requirement_map = {
        "heavy_load": req.get("load_capacity_kg") or req.get("load_capacity_lb"),
        "quiet_operation": req.get("noise_db_target"),
        "high_stability": req.get("stability_requirement"),
        "extra_wide_multi_leg": req.get("width_mm") or req.get("leg_count"),
        "medical_industrial": req.get("medical_industrial"),
        "custom_mount_holes": req.get("mounting_holes"),
        "controller": req.get("controller_type"),
        "anti_collision": req.get("anti_collision"),
        "finish_color": req.get("color_finish") or req.get("powder_coat"),
        "certification": req.get("certifications"),
        "sample_validation": req.get("sample_required"),
        "lead_time": req.get("lead_time_days_max"),
        "warranty": req.get("warranty_requirement"),
        "stroke_range": req.get("stroke_range_mm"),
        "speed_duty": req.get("speed_mm_s") or req.get("duty_cycle"),
    }
    dims = _build_dimension_fits(requirement_map, catalog_attrs, partner_pending=partner_pending)
    overall = _overall_from_dimensions(dims)
    lifecycle = normalize_lifecycle(partner)
    auto_rec = is_partner_default_recommendable(partner) and not partner_pending and overall in {"MATCH", "PARTIAL"}
    return {
        "candidate_source_type": CandidateSourceType.partner.value,
        "candidate_ref_id": catalog.id,
        "partner_id": partner.id,
        "product_catalog_id": catalog.id,
        "display_name": f"{partner.partner_name} · {catalog.product_name}",
        "sku": catalog.internal_sku,
        "fit_dimensions_json": dims,
        "evidence_quality": "high" if not partner_pending else "low",
        "overall_fit_status": overall if not partner_pending else "UNKNOWN",
        "eligible_for_formal_quote": _eligible_for_formal_quote(
            CandidateSourceType.partner.value, partner, partner_pending
        ),
        "is_auto_recommended": auto_rec,
        "candidate_role": CandidateRole.primary.value if auto_rec else CandidateRole.alternate.value,
        "lifecycle_status": lifecycle,
    }


def build_benchmark_candidate(db: Session, row: CustomerProjectRequest, brand: BenchmarkBrand) -> dict[str, Any]:
    caps = {c.capability_key: c for c in brand.capabilities}
    req = row.requirements_json or {}

    def _bench_status(key: str, req_val: Any) -> str:
        if req_val in (None, "", [], False):
            return "UNKNOWN"
        cap = caps.get(key)
        if not cap:
            return "UNKNOWN"
        if cap.verification_status == "pending_verification":
            return "UNKNOWN"
        return "PARTIAL"

    dims = {
        "capability": {
            "match_status": _bench_status("load_capacity_kg", req.get("load_capacity_kg")),
            "evidence_quality": "medium",
        },
        "commercial": {"match_status": "UNKNOWN", "evidence_quality": "low"},
        "compliance": {
            "match_status": _bench_status("certifications", req.get("certifications")),
            "evidence_quality": "medium",
        },
        "delivery": {"match_status": "UNKNOWN", "evidence_quality": "low"},
    }
    return {
        "candidate_source_type": CandidateSourceType.benchmark.value,
        "candidate_ref_id": brand.id,
        "benchmark_brand_id": brand.id,
        "display_name": f"[Benchmark] {brand.display_name}",
        "sku": None,
        "fit_dimensions_json": dims,
        "evidence_quality": "medium",
        "overall_fit_status": _overall_from_dimensions(dims),
        "eligible_for_formal_quote": False,
        "is_auto_recommended": False,
        "candidate_role": CandidateRole.engineering_review.value,
    }


def build_discovery_candidate(db: Session, record: SupplierDiscoveryRecord) -> dict[str, Any]:
    dims = {
        k: {"match_status": "UNKNOWN", "evidence_quality": "low"} for k in FIT_DIMENSION_KEYS
    }
    return {
        "candidate_source_type": CandidateSourceType.supplier_discovery.value,
        "candidate_ref_id": record.id,
        "supplier_discovery_id": record.id,
        "partner_id": record.partner_id,
        "display_name": f"[Discovery] {record.company_name}",
        "sku": None,
        "fit_dimensions_json": dims,
        "evidence_quality": "low",
        "overall_fit_status": "UNKNOWN",
        "eligible_for_formal_quote": False,
        "is_auto_recommended": False,
        "candidate_role": CandidateRole.engineering_review.value,
    }


def refresh_supplier_candidates(db: Session, row: CustomerProjectRequest, *, actor_id: UUID | None = None) -> list[CandidateModel]:
    """Rebuild candidate list from active partners, benchmarks, and discovery — no legacy auto-select."""
    db.query(ProjectRequestSupplierCandidate).filter(
        ProjectRequestSupplierCandidate.project_request_id == row.id
    ).delete()

    created: list[CandidateModel] = []
    catalogs = (
        db.query(ProductCatalog)
        .join(ManufacturingPartner, ProductCatalog.partner_id == ManufacturingPartner.id)
        .filter(
            ProductCatalog.status == "active",
            ManufacturingPartner.lifecycle_status.in_(
                [PartnerLifecycle.active.value, PartnerLifecycle.onboarding.value, PartnerLifecycle.legacy.value]
            ),
        )
        .limit(50)
        .all()
    )
    for catalog in catalogs:
        partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == catalog.partner_id).first()
        if not partner:
            continue
        payload = build_partner_candidate(db, row, catalog, partner)
        payload.pop("lifecycle_status", None)
        cand = ProjectRequestSupplierCandidate(
            project_request_id=row.id,
            created_by_id=actor_id,
            updated_by_id=actor_id,
            **payload,
        )
        db.add(cand)
        created.append(cand)

    for brand in db.query(BenchmarkBrand).filter(BenchmarkBrand.is_active.is_(True)).limit(20).all():
        payload = build_benchmark_candidate(db, row, brand)
        cand = ProjectRequestSupplierCandidate(
            project_request_id=row.id,
            created_by_id=actor_id,
            updated_by_id=actor_id,
            **payload,
        )
        db.add(cand)
        created.append(cand)

    for rec in (
        db.query(SupplierDiscoveryRecord)
        .filter(SupplierDiscoveryRecord.status.in_(["evaluating", "qualified", "sample_requested"]))
        .limit(10)
        .all()
    ):
        payload = build_discovery_candidate(db, rec)
        cand = ProjectRequestSupplierCandidate(
            project_request_id=row.id,
            created_by_id=actor_id,
            updated_by_id=actor_id,
            **payload,
        )
        db.add(cand)
        created.append(cand)

    db.flush()
    return created


def record_candidate_decision(
    db: Session,
    candidate: CandidateModel,
    *,
    decision: str,
    reason: str | None,
    actor_id: UUID,
) -> CandidateModel:
    candidate.operator_decision = decision
    candidate.decision_reason = reason
    candidate.updated_by_id = actor_id
    if decision == "selected" and candidate.eligible_for_formal_quote:
        candidate.candidate_role = CandidateRole.primary.value
    db.commit()
    db.refresh(candidate)
    return candidate
