"""D5.6 — read-only outreach history timeline for a lead."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Interaction, Lead
from app.services.a_domain.lead_completeness_board import build_lead_completeness_row_for_lead


def _lower(text: str | None) -> str:
    return (text or "").lower()


def _is_manual_send(summary: str | None, subject: str | None) -> bool:
    blob = f"{summary or ''} {subject or ''}".lower()
    return "manually_sent=true" in blob or "manual outreach" in blob


def _is_contact_research(
    interaction_type: str,
    channel: str,
    summary: str | None,
) -> bool:
    if interaction_type == "contact_research" or channel == "manual_research":
        return True
    return "manually_researched=true" in _lower(summary)


def _timeline_title(ix: Interaction) -> str:
    if _is_contact_research(ix.interaction_type, ix.channel, ix.summary):
        return "Contact research updated"
    if _is_manual_send(ix.summary, ix.subject):
        it = ix.interaction_type or ""
        if it in ("catalog_sent", "email_intro"):
            return "Email intro marked as sent"
        if it == "linkedin_connect_note":
            return "LinkedIn connect marked as sent"
        if it == "quotation_follow_up":
            return "Follow-up marked as sent"
        channel = _lower(ix.channel)
        if channel == "email":
            return "Email outreach marked as sent"
        if channel == "linkedin":
            return "LinkedIn outreach marked as sent"
        return "Outreach marked as sent"
    if ix.subject and ix.subject.strip():
        return ix.subject.strip()
    return (ix.interaction_type or "touchpoint").replace("_", " ").title()


def _item_from_interaction(ix: Interaction) -> dict[str, Any]:
    summary = (ix.summary or ix.content or "").strip() or None
    return {
        "id": str(ix.id),
        "timestamp": ix.interaction_date.isoformat() if ix.interaction_date else None,
        "type": ix.interaction_type,
        "channel": ix.channel,
        "title": _timeline_title(ix),
        "summary": summary,
        "is_manual_send": _is_manual_send(ix.summary, ix.subject),
        "is_contact_research": _is_contact_research(ix.interaction_type, ix.channel, ix.summary),
    }


def compute_follow_up_hint(
    *,
    completeness_status: str | None,
    touch_count: int,
    latest: Interaction | None,
    next_action: str | None,
) -> str:
    """Derived hint; priority: research > first outreach > follow up soon > waiting > ready > review."""
    candidates: list[tuple[str, str]] = []

    if completeness_status == "needs_contact_research":
        candidates.append(("needs_contact_research", "Needs contact research"))
    if touch_count == 0:
        candidates.append(("needs_first_outreach", "Needs first outreach"))

    na = _lower(next_action)
    if "follow up" in na or "follow-up" in na or "followup" in na:
        candidates.append(("follow_up_soon", "Follow up soon"))

    if latest:
        sm = _lower(latest.summary)
        if "manually_sent=true" in sm:
            candidates.append(("waiting_for_reply", "Waiting for reply"))
        if _is_contact_research(latest.interaction_type, latest.channel, latest.summary):
            candidates.append(("ready_to_prepare", "Ready to prepare outreach"))

    priority = (
        "needs_contact_research",
        "needs_first_outreach",
        "follow_up_soon",
        "waiting_for_reply",
        "ready_to_prepare",
    )
    for key in priority:
        for k, label in candidates:
            if k == key:
                return label
    return "Review next action"


def build_lead_timeline(db: Session, lead_id: UUID) -> dict[str, Any]:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.is_active.is_(True)).first()
    if not lead:
        raise ValueError("Lead not found")

    company = db.query(Company).filter(Company.id == lead.company_id).first()
    company_name = company.company_name if company else "—"

    rows = (
        db.query(Interaction)
        .filter(
            Interaction.related_object_type == "lead",
            Interaction.related_object_id == lead.id,
        )
        .order_by(Interaction.interaction_date.desc())
        .all()
    )

    items = [_item_from_interaction(ix) for ix in rows]
    latest = rows[0] if rows else None
    last_touch_at: datetime | None = latest.interaction_date if latest else None

    manual_sent = sum(1 for i in items if i["is_manual_send"])
    research_count = sum(1 for i in items if i["is_contact_research"])

    completeness_row = build_lead_completeness_row_for_lead(db, lead.id)
    completeness_status = completeness_row.get("status") if completeness_row else None

    next_action = (lead.next_action or "").strip() or None

    return {
        "lead_id": str(lead.id),
        "company_name": company_name,
        "next_action": next_action,
        "last_touchpoint_at": last_touch_at.isoformat() if last_touch_at else None,
        "follow_up_hint": compute_follow_up_hint(
            completeness_status=completeness_status,
            touch_count=len(rows),
            latest=latest,
            next_action=next_action,
        ),
        "items": items,
        "stats": {
            "total_touchpoints": len(rows),
            "manual_sent_count": manual_sent,
            "contact_research_count": research_count,
            "last_channel": latest.channel if latest else None,
        },
    }
