"""Commercial pilot operations — coverage, development tasks, pilots, metrics."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    CategoryCoverageAssessment,
    CommercialPilotRun,
    CustomerProjectRequest,
    ManufacturingPartner,
    PlatformBenchmarkRecord,
    ProjectRequestSupplierCandidate,
    Quote,
    QuotePdfExport,
    SupplierDevelopmentTask,
    SupplierDiscoveryRecord,
    SupplierSelectionSnapshot,
)
from app.models.enums import (
    CommercialPilotIndustry,
    CommercialPilotStatus,
    PartnerLifecycle,
    SupplierDevelopmentTaskType,
    SupplierEvidenceStatus,
    SupplierRelationshipType,
)
from app.services.partner_lifecycle import is_partner_selectable_for_new_quote
from app.services.supplier_discovery_service import build_dedup_fingerprint, init_qualification_json, normalize_domain

DEVELOPMENT_TASK_TEMPLATES: tuple[dict[str, str], ...] = (
    {"task_type": SupplierDevelopmentTaskType.initial_research.value, "title": "初步公开资料调研"},
    {"task_type": SupplierDevelopmentTaskType.contact_prep.value, "title": "联系准备与渠道确认"},
    {"task_type": SupplierDevelopmentTaskType.information_request.value, "title": "发送资料请求"},
    {"task_type": SupplierDevelopmentTaskType.catalog_requested.value, "title": "产品目录请求"},
    {"task_type": SupplierDevelopmentTaskType.price_list_requested.value, "title": "价格表/区间价请求"},
    {"task_type": SupplierDevelopmentTaskType.certification_requested.value, "title": "认证证书请求"},
    {"task_type": SupplierDevelopmentTaskType.sample_requested.value, "title": "样品请求"},
    {"task_type": SupplierDevelopmentTaskType.sample_follow_up.value, "title": "样品跟进"},
    {"task_type": SupplierDevelopmentTaskType.qualification_review.value, "title": "资质评审"},
)

LIFTING_CUSTOMER_NEEDS: tuple[str, ...] = (
    "heavy_load",
    "low_noise",
    "stability",
    "multi_leg_sync",
    "ultra_wide",
    "industrial_medical",
    "controller",
    "anti_collision",
    "mounting_holes",
    "powder_coat",
    "certs",
    "warranty",
    "lead_time",
)

EDUCATION_CUSTOMER_NEEDS: tuple[str, ...] = (
    "classroom_desks_chairs",
    "mobility",
    "durability",
    "ada_compliance",
    "color_options",
    "project_lead_time",
    "fire_rating",
    "bulk_packaging",
)

CONTRACT_OFFICE_NEEDS: tuple[str, ...] = (
    "conference_workstation",
    "finishes",
    "quick_delivery",
    "install_support",
    "certs",
    "modular_config",
    "warranty",
)

INDUSTRY_NEEDS: dict[str, tuple[str, ...]] = {
    CommercialPilotIndustry.lifting_systems.value: LIFTING_CUSTOMER_NEEDS,
    CommercialPilotIndustry.education_furniture.value: EDUCATION_CUSTOMER_NEEDS,
    CommercialPilotIndustry.contract_office.value: CONTRACT_OFFICE_NEEDS,
}

INDUSTRY_CATEGORY_FILTERS: dict[str, list[str]] = {
    CommercialPilotIndustry.lifting_systems.value: ["Lifting", "Desk Frame", "Actuator", "Column"],
    CommercialPilotIndustry.education_furniture.value: ["Education", "School", "Classroom"],
    CommercialPilotIndustry.contract_office.value: ["Office", "Contract", "Workstation", "Conference"],
}


def build_doc_request_checklist(*, task_type: str) -> list[dict[str, str]]:
    base = [
        {"item": "company_profile", "label": "公司简介（公开来源核实）", "status": "pending"},
        {"item": "product_catalog", "label": "产品目录/规格摘要", "status": "pending"},
        {"item": "certifications", "label": "认证清单（CE/UL 等，未提供则 UNKNOWN）", "status": "pending"},
        {"item": "moq_lead_time", "label": "MOQ 与交期说明", "status": "pending"},
        {"item": "sample_policy", "label": "样品政策", "status": "pending"},
        {"item": "export_markets", "label": "出口市场经验", "status": "pending"},
    ]
    if task_type == SupplierDevelopmentTaskType.price_list_requested.value:
        base.append({"item": "interval_pricing", "label": "区间价/FOB 参考（不含内部成本）", "status": "pending"})
    if task_type == SupplierDevelopmentTaskType.certification_requested.value:
        base.append({"item": "cert_copies", "label": "认证复印件或官网公开链接", "status": "pending"})
    return base


def build_email_draft(*, company_name: str, task_type: str, operator_name: str = "PartnerOS Operator") -> dict[str, str]:
    subject_map = {
        SupplierDevelopmentTaskType.information_request.value: f"Information request — {company_name}",
        SupplierDevelopmentTaskType.catalog_requested.value: f"Product catalog request — {company_name}",
        SupplierDevelopmentTaskType.price_list_requested.value: f"Pricing reference request — {company_name}",
        SupplierDevelopmentTaskType.certification_requested.value: f"Certification inquiry — {company_name}",
        SupplierDevelopmentTaskType.sample_requested.value: f"Sample evaluation request — {company_name}",
    }
    body = (
        f"Dear {company_name} team,\n\n"
        "We are evaluating manufacturing partners for a U.S.-facing project. "
        "Please share the requested information at your convenience.\n\n"
        "This message is a DRAFT for human review — NOT sent automatically.\n\n"
        f"Prepared by: {operator_name}\n"
        "PartnerOS Supplier Development"
    )
    return {
        "subject": subject_map.get(task_type, f"Supplier development — {company_name}"),
        "body": body,
        "approval_required": "true",
        "auto_send_blocked": "true",
    }


def create_development_task(
    db: Session,
    *,
    supplier_discovery_id: UUID,
    task_type: str,
    title: str | None,
    owner_user_id: UUID | None,
    actor_id: UUID,
    priority: str = "P2",
    due_days: int = 7,
    depends_on_task_ids: list[str] | None = None,
) -> SupplierDevelopmentTask:
    record = db.query(SupplierDiscoveryRecord).filter(SupplierDiscoveryRecord.id == supplier_discovery_id).first()
    if not record:
        raise ValueError("Supplier discovery record not found")
    checklist = build_doc_request_checklist(task_type=task_type)
    email_draft = build_email_draft(company_name=record.company_name, task_type=task_type)
    row = SupplierDevelopmentTask(
        supplier_discovery_id=supplier_discovery_id,
        task_type=task_type,
        title=title or next((t["title"] for t in DEVELOPMENT_TASK_TEMPLATES if t["task_type"] == task_type), task_type),
        owner_user_id=owner_user_id,
        due_date=date.today() + timedelta(days=due_days),
        priority=priority,
        status="open",
        depends_on_task_ids=depends_on_task_ids,
        email_draft_json=email_draft,
        checklist_json=checklist,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(row)
    db.flush()
    return row


def seed_standard_development_tasks(db: Session, *, supplier_discovery_id: UUID, owner_user_id: UUID, actor_id: UUID) -> list[SupplierDevelopmentTask]:
    created: list[SupplierDevelopmentTask] = []
    prior_id: str | None = None
    for idx, template in enumerate(DEVELOPMENT_TASK_TEMPLATES):
        depends = [prior_id] if prior_id else None
        row = create_development_task(
            db,
            supplier_discovery_id=supplier_discovery_id,
            task_type=template["task_type"],
            title=template["title"],
            owner_user_id=owner_user_id,
            actor_id=actor_id,
            priority="P0" if idx < 3 else "P1",
            due_days=7 + idx * 3,
            depends_on_task_ids=depends,
        )
        prior_id = str(row.id)
        created.append(row)
    return created


def _count_discovery_by_industry(db: Session, industry: str) -> dict[str, int]:
    filters = INDUSTRY_CATEGORY_FILTERS.get(industry, [])
    public = db.query(SupplierDiscoveryRecord).filter(
        SupplierDiscoveryRecord.relationship_type == SupplierRelationshipType.public_candidate.value
    )
    active_partners = db.query(ManufacturingPartner).filter(
        ManufacturingPartner.lifecycle_status == PartnerLifecycle.active.value
    ).count()
    candidate_count = 0
    for row in public.all():
        cats = row.categories or []
        if any(any(f.lower() in (c or "").lower() for f in filters) for c in cats):
            candidate_count += 1
    return {"public_candidates": candidate_count, "active_partners": active_partners}


def build_category_coverage(db: Session, *, industry_vertical: str, actor_id: UUID) -> CategoryCoverageAssessment:
    needs = list(INDUSTRY_NEEDS.get(industry_vertical, ()))
    counts = _count_discovery_by_industry(db, industry_vertical)
    coverage: dict[str, Any] = {
        "active_partner_count": counts["active_partners"],
        "public_candidate_count": counts["public_candidates"],
        "needs_with_active_coverage": [],
        "needs_with_candidate_coverage": [],
        "needs_missing": [],
    }
    gaps: list[dict[str, str]] = []
    for need in needs:
        if counts["active_partners"] > 0 and need in ("lead_time", "warranty", "certs"):
            coverage["needs_with_active_coverage"].append(need)
        elif counts["public_candidates"] >= 2:
            coverage["needs_with_candidate_coverage"].append(need)
        else:
            coverage["needs_missing"].append(need)
            gaps.append({"need": need, "gap_type": "capability", "status": "UNKNOWN"})

    if counts["active_partners"] <= 1:
        gaps.append({"need": "supplier_diversity", "gap_type": "single_supplier_dependency", "status": "HIGH_RISK"})

    risk = {
        "single_supplier_dependency": counts["active_partners"] <= 1,
        "pricing_doc_gaps": True,
        "sample_cycle_unknown": True,
    }
    suggested = [
        {"action": "develop_public_candidates", "supplier_type": "lifting_oem" if industry_vertical == "lifting_systems" else "category_oem"},
        {"action": "request_certifications", "priority": "P0"},
        {"action": "request_sample_cycle", "priority": "P1"},
    ]
    row = CategoryCoverageAssessment(
        industry_vertical=industry_vertical,
        assessment_label=f"{industry_vertical} coverage {date.today().isoformat()}",
        customer_needs_json={"needs": needs},
        coverage_json=coverage,
        gaps_json={"gaps": gaps},
        risk_json=risk,
        suggested_actions_json=suggested,
        linked_evidence_json={"project_market_refs": []},
        generated_at=datetime.now(timezone.utc),
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(row)
    db.flush()
    return row


def get_latest_category_coverage(db: Session, industry_vertical: str) -> CategoryCoverageAssessment | None:
    return (
        db.query(CategoryCoverageAssessment)
        .filter(CategoryCoverageAssessment.industry_vertical == industry_vertical)
        .order_by(CategoryCoverageAssessment.generated_at.desc())
        .first()
    )


def build_commercial_metrics(db: Session) -> dict[str, Any]:
    public_candidates = (
        db.query(SupplierDiscoveryRecord)
        .filter(SupplierDiscoveryRecord.relationship_type == SupplierRelationshipType.public_candidate.value)
        .count()
    )
    qualified = (
        db.query(SupplierDiscoveryRecord)
        .filter(SupplierDiscoveryRecord.status.in_(("qualified", "active")))
        .count()
    )
    open_tasks = db.query(SupplierDevelopmentTask).filter(SupplierDevelopmentTask.status == "open").count()
    pilots = db.query(CommercialPilotRun).count()
    multi_candidate_projects = (
        db.query(ProjectRequestSupplierCandidate.project_request_id)
        .group_by(ProjectRequestSupplierCandidate.project_request_id)
        .having(func.count(ProjectRequestSupplierCandidate.id) >= 2)
        .count()
    )
    snapshots = db.query(SupplierSelectionSnapshot).count()
    quotes_with_pilot = db.query(CommercialPilotRun).filter(CommercialPilotRun.quote_id.isnot(None)).count()
    return {
        "candidate_suppliers": public_candidates,
        "qualification_conversion_pct": round(qualified / public_candidates * 100, 1) if public_candidates else 0,
        "open_development_tasks": open_tasks,
        "commercial_pilot_runs": pilots,
        "projects_with_2_plus_candidates": multi_candidate_projects,
        "frozen_selection_snapshots": snapshots,
        "pilots_with_quotes": quotes_with_pilot,
        "info_completeness_note": "UNKNOWN fields remain until operator verification",
        "sample_cycle_days": "UNKNOWN",
        "quote_readiness_blocked_scenario": True,
    }


def import_public_candidate(
    db: Session,
    *,
    payload: dict[str, Any],
    actor_id: UUID,
) -> SupplierDiscoveryRecord:
    source_url = payload.get("source_url")
    domain = normalize_domain(source_url)
    fingerprint = build_dedup_fingerprint(
        company_name=payload["company_name"],
        domain_key=domain,
        factory_address=payload.get("factory_address"),
    )
    existing = (
        db.query(SupplierDiscoveryRecord)
        .filter(SupplierDiscoveryRecord.dedup_fingerprint == fingerprint)
        .first()
    )
    if existing:
        return existing
    row = SupplierDiscoveryRecord(
        company_name=payload["company_name"],
        brand_name=payload.get("brand_name"),
        country=payload.get("country"),
        manufacturing_region=payload.get("manufacturing_region"),
        categories=payload.get("categories"),
        capabilities=payload.get("capabilities"),
        certifications=payload.get("certifications"),
        moq_notes=payload.get("moq_notes") or "UNKNOWN",
        sample_policy=payload.get("sample_policy") or "UNKNOWN",
        lead_time_notes=payload.get("lead_time_notes") or "UNKNOWN",
        export_markets=payload.get("export_markets"),
        data_source=payload.get("data_source") or "public_research",
        source_url=source_url,
        domain_key=domain,
        dedup_fingerprint=fingerprint,
        relationship_type=SupplierRelationshipType.public_candidate.value,
        evidence_status=payload.get("evidence_status") or SupplierEvidenceStatus.partial_public.value,
        source_review_status="pending",
        data_rights_status="public_page_only",
        pricing_doc_status="unknown",
        retrieved_at=payload.get("retrieved_at") or datetime.now(timezone.utc),
        usage_restrictions="Public candidate — not a PartnerOS partner. No auto activation.",
        status="discovered",
        qualification_json=init_qualification_json(),
        notes=payload.get("notes"),
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(row)
    db.flush()
    return row


def assert_partner_quote_eligibility(partner: ManufacturingPartner) -> bool:
    return is_partner_selectable_for_new_quote(partner)


def build_pilot_gap_tasks(db: Session, *, pilot: CommercialPilotRun, actor_id: UUID) -> list[dict[str, Any]]:
    gaps = pilot.gap_tasks_json or []
    if gaps:
        return gaps
    discovery = (
        db.query(SupplierDiscoveryRecord)
        .filter(SupplierDiscoveryRecord.relationship_type == SupplierRelationshipType.public_candidate.value)
        .first()
    )
    if not discovery:
        return [{"task": "seed_public_candidates", "priority": "P0"}]
    tasks = seed_standard_development_tasks(
        db, supplier_discovery_id=discovery.id, owner_user_id=actor_id, actor_id=actor_id
    )
    payload = [{"task_id": str(t.id), "task_type": t.task_type, "title": t.title} for t in tasks]
    pilot.gap_tasks_json = payload
    return payload


def update_pilot_status(db: Session, pilot: CommercialPilotRun, status: str) -> CommercialPilotRun:
    pilot.status = status
    db.flush()
    return pilot


def link_pilot_artifacts(
    db: Session,
    *,
    pilot: CommercialPilotRun,
    project_request_id: UUID | None = None,
    quote_id: UUID | None = None,
    market_response_review_id: UUID | None = None,
) -> CommercialPilotRun:
    if project_request_id:
        pilot.project_request_id = project_request_id
    if quote_id:
        pilot.quote_id = quote_id
    if market_response_review_id:
        pilot.market_response_review_id = market_response_review_id
    db.flush()
    return pilot


def get_pilot_by_code(db: Session, pilot_code: str) -> CommercialPilotRun | None:
    return db.query(CommercialPilotRun).filter(CommercialPilotRun.pilot_code == pilot_code).first()


def ensure_pilot_run(db: Session, *, spec: dict[str, Any], actor_id: UUID) -> CommercialPilotRun:
    existing = get_pilot_by_code(db, spec["pilot_code"])
    if existing:
        return existing
    row = CommercialPilotRun(
        pilot_code=spec["pilot_code"],
        pilot_name=spec["pilot_name"],
        industry_vertical=spec["industry_vertical"],
        status=CommercialPilotStatus.draft.value,
        synthetic_customer_json=spec["synthetic_customer_json"],
        requirements_json=spec["requirements_json"],
        scenario_pricing_blocked=True,
        result_summary=spec.get("result_summary"),
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(row)
    db.flush()
    return row


def seed_platform_benchmark_backlog(db: Session, *, actor_id: UUID) -> int:
    platforms = [
        ("Alibaba", "supplier_discovery", "build", "P1", "B2B marketplace supplier search"),
        ("Made-in-China", "supplier_discovery", "integrate", "P2", "Category supplier research"),
        ("Thomasnet", "supplier_discovery", "integrate", "P1", "U.S. industrial supplier directory"),
        ("Shopify B2B", "customer_portal", "do-not-build", "P2", "Customer portal is separate stack"),
        ("Faire", "channel_intelligence", "do-not-build", "P2", "Wholesale channel not core loop"),
        ("Zoho CRM", "crm_sync", "integrate", "P1", "Optional CRM bridge"),
        ("Zoho Books", "accounting", "do-not-build", "P2", "Accounting outside scope"),
        ("Zoho Inventory", "inventory", "integrate", "P2", "Sample inventory reference only"),
    ]
    created = 0
    for name, area, action, priority, desc in platforms:
        exists = (
            db.query(PlatformBenchmarkRecord)
            .filter(PlatformBenchmarkRecord.platform_name == name, PlatformBenchmarkRecord.capability_area == area)
            .first()
        )
        if exists:
            exists.build_action = action
            exists.build_priority = priority
            exists.gap_description = desc
            exists.updated_by_id = actor_id
            continue
        db.add(
            PlatformBenchmarkRecord(
                platform_name=name,
                capability_area=area,
                capability_description=desc,
                partneros_has=action == "build",
                build_recommended=action in ("build", "integrate"),
                build_priority=priority,
                build_action=action,
                business_value=desc,
                implementation_cost="medium" if priority == "P1" else "low",
                evidence_source="official_public_pages",
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
        )
        created += 1
    db.flush()
    return created
