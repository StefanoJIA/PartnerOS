"""Market signal drafts from project requests — operator approval required."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import CustomerProjectRequest, MarketResponseReview
from app.services.activity import log_activity


def build_market_signal_draft(db: Session, row: CustomerProjectRequest) -> dict[str, Any]:
    req = row.requirements_json or {}
    fit = row.fit_summary_json or {}
    customer_type = "unknown"
    if row.company_name_text:
        lower = row.company_name_text.lower()
        if "school" in lower or "education" in lower:
            customer_type = "education_furniture_buyer"
        elif "oem" in lower or "manufactur" in lower:
            customer_type = "oem_component_buyer"
        elif "dealer" in lower or "distributor" in lower:
            customer_type = "dealer"

    gaps = [m for m in fit.get("matches", []) if m.get("match_status") in {"UNKNOWN", "NOT_SUPPORTED", "PARTIAL"}]
    priority = "P1" if any(m.get("match_status") == "NOT_SUPPORTED" for m in gaps) else "P2"

    return {
        "source_type": "project_request",
        "signal_class": "REAL" if row.source == "customer_site" else "ASSUMPTION",
        "request_reference": row.request_reference,
        "request_id": str(row.id),
        "customer_type": customer_type,
        "partner_code": fit.get("partner_code"),
        "product_sku": row.sku,
        "customer_verbatim": row.project_scenario or row.operator_notes,
        "requirements_summary": {
            "load": req.get("load_capacity_kg") or req.get("load_capacity_lb"),
            "noise": req.get("noise_db_target"),
            "stability": req.get("stability_requirement"),
            "width_legs": req.get("width_mm") or req.get("leg_count"),
            "certifications": req.get("certifications"),
        },
        "fit_overall": fit.get("overall_status"),
        "gap_dimensions": [g.get("dimension") for g in gaps[:8]],
        "priority": priority,
        "confidence": "medium" if row.source == "customer_site" else "low",
        "requires_operator_approval": True,
        "disclaimer": "Draft only — not published until operator review.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def promote_market_signal_to_review(
    db: Session,
    row: CustomerProjectRequest,
    *,
    actor_id: UUID,
    owner: str = "operator",
) -> MarketResponseReview:
    draft = build_market_signal_draft(db, row)
    focus_category = "adjustable_desk_frames"
    partner_focus = draft.get("partner_code") or "multi-partner"
    if partner_focus and str(partner_focus).upper().startswith("JOO"):
        focus_category = "education_furniture"

    review = MarketResponseReview(
        partner_focus=partner_focus,
        focus_category=focus_category,
        product_focus=[row.product_interest or row.sku or "project request"],
        review_dimension="project_requirement",
        visibility_class="needs validation",
        priority=draft.get("priority", "P2"),
        status="needs review",
        source_type="project_request",
        source_summary=f"Project request {row.request_reference}: {row.project_scenario or 'requirements intake'}",
        evidence_summary=f"Fit overall {draft.get('fit_overall')}; gaps: {', '.join(draft.get('gap_dimensions') or [])}",
        customer_safe_summary=None,
        internal_notes=f"Auto-draft from request {row.request_reference}. Operator must verify before customer-facing use.",
        next_action="Review requirement gaps and confirm validation path.",
        owner=owner,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(review)
    log_activity(
        db,
        object_type="customer_project_request",
        object_id=row.id,
        action="market_signal_promoted",
        actor_id=actor_id,
        diff={"review_id": str(review.id), "priority": draft.get("priority")},
    )
    db.commit()
    db.refresh(review)
    return review
