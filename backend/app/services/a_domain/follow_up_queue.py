"""D5.7 — follow-up scheduling and due queue (uses lead.next_action_due_date)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Contact, Interaction, Lead, MarketIntelligenceItem, User
from app.services.activity import log_activity
from app.services.a_domain.follow_up_rhythm import NO_NEXT_ACTION
from app.services.a_domain.intelligence_score import IntelligenceScoreInput, compute_intelligence_score


def compute_due_status(due: date | None, today: date | None = None) -> tuple[str, int | None]:
    """Return (due_status, days_until_due). days_until_due negative when overdue."""
    if due is None:
        return "no_follow_up_date", None
    ref = today or date.today()
    delta = (due - ref).days
    if delta < 0:
        return "overdue", delta
    if delta == 0:
        return "due_today", 0
    if delta <= 7:
        return "due_soon", delta
    return "scheduled", delta


def _is_waiting_reply(next_action: str | None, last_touch_summary: str | None) -> bool:
    na = (next_action or "").lower()
    lt = (last_touch_summary or "").lower()
    manually_sent = "manually_sent=true" in lt or "manual outreach" in lt
    if manually_sent and any(p in na for p in ("wait", "follow up", "waiting")):
        return True
    return any(p in na for p in ("wait for reply", "waiting for"))


def _last_touch(db: Session, lead_id: UUID) -> tuple[str, datetime | None]:
    row = (
        db.query(Interaction)
        .filter(
            Interaction.related_object_type == "lead",
            Interaction.related_object_id == lead_id,
        )
        .order_by(Interaction.interaction_date.desc())
        .first()
    )
    if not row:
        return "—", None
    summary = row.summary or row.subject or row.interaction_type or "—"
    return summary, row.interaction_date


def _recommended_action(due_status: str, segments: list[str], waiting: bool) -> str:
    if due_status == "overdue":
        return "Follow up today — overdue"
    if due_status == "due_today":
        return "Follow up today"
    if waiting:
        return "Check for reply; send gentle follow-up if no response"
    if segments:
        if "lift_system_signal" in segments:
            return "Follow up by email or LinkedIn on lifting systems"
        if "medical_vertical" in segments:
            return "Follow up on medical workspace solutions"
    if due_status == "due_soon":
        return "Prepare follow-up message before due date"
    if due_status == "no_follow_up_date":
        return "Set a follow-up date after outreach"
    return "Review next action"


def build_follow_up_queue_rows(db: Session, today: date | None = None) -> list[dict[str, Any]]:
    ref = today or date.today()
    leads = db.query(Lead).filter(Lead.is_active.is_(True)).order_by(Lead.created_at.desc()).all()
    rows: list[dict[str, Any]] = []

    for lead in leads:
        company = db.query(Company).filter(Company.id == lead.company_id).first()
        if not company:
            continue
        contact = None
        if lead.primary_contact_id:
            contact = db.query(Contact).filter(Contact.id == lead.primary_contact_id).first()

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

        last_touch, last_at = _last_touch(db, lead.id)
        touch_count = (
            db.query(Interaction)
            .filter(
                Interaction.related_object_type == "lead",
                Interaction.related_object_id == lead.id,
            )
            .count()
        )

        na = (lead.next_action or "").strip() or NO_NEXT_ACTION
        due_status, days_until = compute_due_status(lead.next_action_due_date, ref)
        waiting = _is_waiting_reply(lead.next_action, last_touch)

        rows.append(
            {
                "lead_id": str(lead.id),
                "company_name": company.company_name,
                "lead_score": intel.score,
                "segments": intel.market_fit_segments,
                "next_action": na if na != NO_NEXT_ACTION else None,
                "next_follow_up_date": lead.next_action_due_date.isoformat() if lead.next_action_due_date else None,
                "due_status": due_status,
                "days_until_due": days_until,
                "last_touchpoint_at": last_at.isoformat() if last_at else None,
                "waiting_reply": waiting,
                "recommended_action": _recommended_action(due_status, intel.market_fit_segments, waiting),
                "touch_count": touch_count,
            }
        )

    return rows


def summarize_follow_up_queue(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(rows),
        "overdue": sum(1 for r in rows if r.get("due_status") == "overdue"),
        "due_today": sum(1 for r in rows if r.get("due_status") == "due_today"),
        "due_soon": sum(1 for r in rows if r.get("due_status") == "due_soon"),
        "no_follow_up_date": sum(1 for r in rows if r.get("due_status") == "no_follow_up_date"),
        "waiting_reply": sum(1 for r in rows if r.get("waiting_reply")),
    }


def apply_follow_up_schedule(
    db: Session,
    user: User,
    lead_id: UUID,
    *,
    next_follow_up_date: date | None,
    next_action: str | None,
    status_note: str | None,
    clear_date: bool = False,
) -> dict[str, Any]:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    if not lead:
        raise ValueError("Lead not found")

    company = db.query(Company).filter(Company.id == lead.company_id).first()
    company_name = company.company_name if company else "—"

    if clear_date:
        lead.next_action_due_date = None
    elif next_follow_up_date is not None:
        lead.next_action_due_date = next_follow_up_date

    if next_action is not None and next_action.strip():
        lead.next_action = next_action.strip()

    lead.updated_by_id = user.id

    note = (status_note or "").strip() or "Manual follow-up scheduled."
    date_str = lead.next_action_due_date.isoformat() if lead.next_action_due_date else "cleared"
    summary = f"{note} [manually_scheduled=true] follow_up_date={date_str}"

    intr = Interaction(
        related_object_type="lead",
        related_object_id=lead.id,
        interaction_type="follow_up_scheduled",
        channel="internal",
        subject="Follow-up scheduled",
        summary=summary,
        direction="internal",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(intr)
    db.flush()

    log_activity(
        db,
        object_type="lead",
        object_id=lead.id,
        action="follow_up_scheduled",
        actor_id=user.id,
        diff={
            "next_action_due_date": date_str,
            "interaction_id": str(intr.id),
        },
    )

    db.commit()
    db.refresh(lead)
    db.refresh(intr)

    due_status, days_until = compute_due_status(lead.next_action_due_date)
    return {
        "lead_id": str(lead.id),
        "company_name": company_name,
        "next_action": lead.next_action,
        "next_follow_up_date": lead.next_action_due_date.isoformat() if lead.next_action_due_date else None,
        "due_status": due_status,
        "days_until_due": days_until,
        "interaction_id": str(intr.id),
    }
