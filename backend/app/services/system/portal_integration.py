"""D5.2.9 — read-only portal summary and A-domain status (no secrets, no DB writes)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Company, Contact, Interaction, Lead, MarketIntelligenceItem
from app.models.enrichment import REVIEW_PENDING, CompanyEnrichmentRun, CompanyEnrichmentSuggestion
from app.services.a_domain.follow_up_rhythm import (
    NO_NEXT_ACTION,
    RhythmLead,
    segment_breakdown,
    summarize_counts,
)
from app.services.a_domain.intelligence_score import IntelligenceScoreInput, compute_intelligence_score
from app.core.database_lifecycle import check_database, get_migration_revisions
from app.services.system.platform import (
    API_VERSION,
    SERVICE_ID,
    build_readiness_payload,
)

PORTAL_CAPABILITIES = [
    "crm",
    "lead_scoring",
    "lead_intelligence_workbench",
    "manual_outreach_queue",
    "human_reviewed_outreach_drafts",
    "public_source_enrichment",
    "system_health",
]

PORTAL_WARNINGS = [
    "redis_ready=false is optional in D5.2.x",
    "worker_ready=false is optional in D5.2.x",
]

A_DOMAIN_STATUS = {
    "domain": "lead_intelligence",
    "status": "ready",
    "uat_status": "accepted_with_non_blocking_feedback",
    "latest_stage": "D5.2.13",
    "daily_workflow_ready": True,
    "manual_outreach_ready": True,
    "automatic_sending_enabled": False,
    "linkedin_automation_enabled": False,
    "outlook_integration_enabled": False,
    "database_schema_changed": False,
    "last_known_test_baseline": {
        "backend_pytest": "97 passed, 1 skipped",
        "frontend_vitest": "47 passed",
    },
    "known_limitations": [
        "manual screenshots not committed",
        "follow-up date parsing is derived from text",
        "no Outlook API integration",
        "no LinkedIn automation",
    ],
}


def _display_enrichment(status: str, pending: int) -> str:
    s = (status or "").lower()
    if s == "completed":
        return f"Completed ({pending} pending)" if pending > 0 else "Completed"
    if s == "running":
        return "Running"
    if s == "failed":
        return "Failed"
    if s == "pending":
        return "Pending"
    return status or "No runs"


def _pending_enrichment_count(db: Session, run_id: UUID) -> int:
    return (
        db.query(CompanyEnrichmentSuggestion)
        .filter(
            CompanyEnrichmentSuggestion.enrichment_run_id == run_id,
            CompanyEnrichmentSuggestion.review_status == REVIEW_PENDING,
        )
        .count()
    )


def load_rhythm_leads_from_db(db: Session, *, limit: int = 500) -> list[RhythmLead]:
    """Aggregate lead rhythm stats from DB (read-only, no PII beyond company names)."""
    leads = (
        db.query(Lead)
        .filter(Lead.is_active.is_(True))
        .order_by(Lead.created_at.desc())
        .limit(limit)
        .all()
    )
    enrich_cache: dict[UUID, str] = {}
    rhythm_leads: list[RhythmLead] = []

    for lead in leads:
        company = db.query(Company).filter(Company.id == lead.company_id).first()
        if not company:
            continue

        contact = None
        if lead.primary_contact_id:
            contact = db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()

        ix_q = db.query(Interaction).filter(
            Interaction.related_object_type == "lead",
            Interaction.related_object_id == lead.id,
        )
        touch_count = ix_q.count()
        last_ix = ix_q.order_by(Interaction.interaction_date.desc()).first()
        last_touch = "-"
        last_touch_date = None
        if last_ix:
            last_touch = last_ix.summary or last_ix.subject or last_ix.interaction_type or "-"
            last_touch_date = (
                last_ix.interaction_date.isoformat() if last_ix.interaction_date else None
            )

        if company.id not in enrich_cache:
            run = (
                db.query(CompanyEnrichmentRun)
                .filter(CompanyEnrichmentRun.company_id == company.id)
                .order_by(CompanyEnrichmentRun.created_at.desc())
                .first()
            )
            if run:
                pending = _pending_enrichment_count(db, run.id)
                enrich_cache[company.id] = _display_enrichment(run.status, pending)
            else:
                enrich_cache[company.id] = "No runs"

        mi_count = (
            db.query(MarketIntelligenceItem)
            .filter(MarketIntelligenceItem.related_company_id == company.id)
            .count()
        )
        intel = compute_intelligence_score(
            IntelligenceScoreInput(
                has_primary_contact=contact is not None,
                market_intel_count=mi_count,
                product_interest_tags=company.product_interest_tags,
                business_description=company.business_description,
                lead_product_interest=lead.product_interest,
                lead_priority=lead.priority,
                company_strategic_level=company.strategic_level,
            )
        )

        next_action = (lead.next_action or "").strip()
        if not next_action:
            next_action = NO_NEXT_ACTION

        rhythm_leads.append(
            RhythmLead(
                company_name=company.company_name or lead.lead_name,
                score=intel.score,
                segments=list(intel.market_fit_segments),
                next_action=next_action,
                touch_count=touch_count,
                last_touch=last_touch,
                last_touch_date=last_touch_date,
                contact_email=contact.email if contact else None,
                linkedin_url=company.linkedin_url,
                enrichment_status=enrich_cache[company.id],
                company_website=company.website,
            )
        )

    return rhythm_leads


def _health_block(settings: Settings) -> dict[str, Any]:
    db_status, _ = check_database(settings)
    migration_pending = False
    if db_status == "ready":
        try:
            current_rev, head_rev, _ = get_migration_revisions(settings)
            migration_pending = current_rev != head_rev
        except Exception:  # noqa: BLE001
            migration_pending = True
    return {
        "status": "ok" if db_status == "ready" else "degraded",
        "database_status": db_status,
        "migration_pending": migration_pending,
    }


def _empty_lead_intelligence() -> dict[str, int]:
    return {
        "total_leads": 0,
        "high_priority": 0,
        "needs_first_outreach": 0,
        "waiting_for_reply": 0,
        "follow_up_soon": 0,
        "needs_contact_research": 0,
        "needs_enrichment": 0,
    }


def _empty_segments() -> dict[str, int]:
    return {
        "lift_system_signal": 0,
        "project_based_furniture": 0,
        "medical_vertical": 0,
        "education_vertical": 0,
        "general_office_furniture_only": 0,
    }


def build_portal_summary_degraded(settings: Settings, db_status: str = "unavailable") -> dict[str, Any]:
    """Read-only summary when database is not queryable (no 500 to Portal consumers)."""
    warnings = list(PORTAL_WARNINGS)
    warnings.insert(
        0,
        "Database unavailable. Start Docker DB or check DATABASE_URL. Lead counts are zero until DB is ready.",
    )
    return {
        "service_id": SERVICE_ID,
        "service_name": "intelliOffice",
        "runtime_mode": settings.APP_RUNTIME_MODE.value,
        "api_version": API_VERSION,
        "health": {
            "status": "degraded",
            "database_status": db_status,
            "migration_pending": False,
        },
        "lead_intelligence": _empty_lead_intelligence(),
        "segments": _empty_segments(),
        "capabilities": list(PORTAL_CAPABILITIES),
        "warnings": warnings,
    }


def build_portal_summary_payload(settings: Settings, db: Session) -> dict[str, Any]:
    db_status, _ = check_database(settings)
    if db_status != "ready":
        return build_portal_summary_degraded(settings, db_status)

    try:
        rhythm_leads = load_rhythm_leads_from_db(db)
    except SQLAlchemyError:
        return build_portal_summary_degraded(settings, "unavailable")

    counts = summarize_counts(rhythm_leads)
    segments = segment_breakdown(rhythm_leads)
    readiness = build_readiness_payload(settings)
    warnings = list(PORTAL_WARNINGS)
    if not readiness.get("redis_ready"):
        pass  # already in PORTAL_WARNINGS
    if readiness.get("warnings"):
        for w in readiness["warnings"]:
            if "SECRET_KEY" in w and w not in warnings:
                warnings.append("rotate SECRET_KEY before production")

    return {
        "service_id": SERVICE_ID,
        "service_name": "intelliOffice",
        "runtime_mode": settings.APP_RUNTIME_MODE.value,
        "api_version": API_VERSION,
        "health": _health_block(settings),
        "lead_intelligence": {
            "total_leads": counts["total"],
            "high_priority": counts["high_priority"],
            "needs_first_outreach": counts["needs_first_outreach"],
            "waiting_for_reply": counts["waiting_for_reply"],
            "follow_up_soon": counts["follow_up_soon"],
            "needs_contact_research": counts["needs_contact_research"],
            "needs_enrichment": counts["needs_enrichment"],
        },
        "segments": segments,
        "capabilities": list(PORTAL_CAPABILITIES),
        "warnings": warnings,
    }


def build_a_domain_status_payload() -> dict[str, Any]:
    return dict(A_DOMAIN_STATUS)
