"""D5.10 — daily work session & end-of-day summary (read-only)."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from sqlalchemy import cast, Date
from sqlalchemy.orm import Session

from app.models import Company, Interaction, Lead
from app.services.a_domain.daily_ops_summary import _build_today_focus
from app.services.a_domain.follow_up_rhythm import HIGH_PRIORITY_SEGMENTS
from app.services.a_domain.follow_up_queue import build_follow_up_queue_rows, summarize_follow_up_queue
from app.services.a_domain.lead_completeness_board import (
    build_lead_completeness_rows,
    summarize_completeness,
)
from app.services.a_domain.lead_timeline import _is_contact_research, _is_manual_send

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _mask_text(text: str | None) -> str:
    if not text:
        return ""
    return EMAIL_RE.sub("[email]", text.strip())


def _is_follow_up_scheduled(ix: Interaction) -> bool:
    summary_lower = (ix.summary or "").lower()
    return ix.interaction_type == "follow_up_scheduled" or "manually_scheduled=true" in summary_lower


def _interactions_on_date(db: Session, target: date) -> list[Interaction]:
    return (
        db.query(Interaction)
        .filter(
            Interaction.related_object_type == "lead",
            cast(Interaction.interaction_date, Date) == target,
        )
        .order_by(Interaction.interaction_date.desc())
        .all()
    )


def _action_label(ix: Interaction) -> str:
    if _is_manual_send(ix.summary, ix.subject):
        channel = (ix.channel or "outreach").replace("_", " ")
        it = ix.interaction_type or ""
        if it == "email_intro":
            return "Manual email intro marked as sent"
        if it == "linkedin_connect_note":
            return "Manual LinkedIn connect marked as sent"
        return f"Manual {channel} marked as sent"
    if _is_contact_research(ix.interaction_type, ix.channel, ix.summary):
        return "Contact research updated"
    if _is_follow_up_scheduled(ix):
        return "Follow-up scheduled"
    return (ix.interaction_type or "Activity").replace("_", " ")


def _lead_company_map(db: Session, lead_ids: set[Any]) -> dict[Any, tuple[str, str | None]]:
    if not lead_ids:
        return {}
    leads = db.query(Lead).filter(Lead.id.in_(list(lead_ids))).all()
    company_ids = {l.company_id for l in leads if l.company_id}
    companies: dict[Any, Company] = {}
    if company_ids:
        companies = {
            c.id: c for c in db.query(Company).filter(Company.id.in_(list(company_ids))).all()
        }
    out: dict[Any, tuple[str, str | None]] = {}
    for lead in leads:
        company = companies.get(lead.company_id)
        out[lead.id] = (
            company.company_name if company else "—",
            lead.next_action,
        )
    return out


def _build_highlights(
    db: Session,
    interactions: list[Interaction],
    limit: int = 5,
) -> list[dict[str, Any]]:
    lead_ids = {ix.related_object_id for ix in interactions}
    ctx = _lead_company_map(db, lead_ids)
    highlights: list[dict[str, Any]] = []
    for ix in interactions[:limit]:
        company_name, next_action = ctx.get(ix.related_object_id, ("—", None))
        highlights.append(
            {
                "lead_id": str(ix.related_object_id),
                "company_name": company_name,
                "action": _action_label(ix),
                "next_action": next_action,
            }
        )
    return highlights


def _build_tomorrow_focus(
    fu_rows: list[dict[str, Any]],
    comp_by_lead: dict[str, dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    focus = _build_today_focus(fu_rows, comp_by_lead, limit=limit)
    return [
        {
            "lead_id": item["lead_id"],
            "company_name": item["company_name"],
            "reason": item["reason"],
            "next_action": item.get("next_action"),
        }
        for item in focus
    ]


def build_copyable_summary(
    target: date,
    summary: dict[str, Any],
    highlights: list[dict[str, Any]],
    tomorrow_focus: list[dict[str, Any]],
) -> str:
    lines = [
        f"Daily intelliOffice Summary — {target.isoformat()}",
        "",
        f"Manual outreach sent: {summary.get('manual_outreach_sent', 0)}",
        f"Contact research updates: {summary.get('contact_research_updates', 0)}",
        f"Follow-ups scheduled: {summary.get('follow_ups_scheduled', 0)}",
        f"Leads touched: {summary.get('leads_touched', 0)}",
    ]
    drafts = summary.get("drafts_generated")
    if drafts is not None:
        lines.append(f"Drafts generated: {drafts}")
    else:
        lines.append("Drafts generated: not tracked")

    lines.extend(
        [
            "",
            f"Remaining — overdue: {summary.get('overdue_remaining', 0)}, "
            f"due today: {summary.get('due_today_remaining', 0)}, "
            f"due soon: {summary.get('due_soon', 0)}",
            "",
            "Highlights:",
        ]
    )
    if highlights:
        for h in highlights:
            na = h.get("next_action") or "—"
            lines.append(
                f"- {_mask_text(h.get('company_name'))} — "
                f"{_mask_text(h.get('action'))}; next action: {_mask_text(na)}."
            )
    else:
        lines.append("- No recorded manual actions for this date.")

    lines.extend(["", "Tomorrow focus:"])
    if tomorrow_focus:
        for t in tomorrow_focus:
            na = t.get("next_action") or "—"
            lines.append(
                f"- {_mask_text(t.get('company_name'))} — "
                f"{_mask_text(t.get('reason'))}; next action: {_mask_text(na)}."
            )
    else:
        lines.append("- No follow-up priorities queued.")

    lines.extend(
        [
            "",
            "Safety:",
            "No automatic messages were sent by intelliOffice. "
            "All outreach actions were manual and human-reviewed.",
        ]
    )
    return "\n".join(lines)


def build_daily_work_summary(db: Session, target_date: date | None = None) -> dict[str, Any]:
    target = target_date or date.today()
    interactions = _interactions_on_date(db, target)

    manual_outreach = sum(1 for ix in interactions if _is_manual_send(ix.summary, ix.subject))
    contact_research = sum(
        1 for ix in interactions if _is_contact_research(ix.interaction_type, ix.channel, ix.summary)
    )
    follow_ups = sum(1 for ix in interactions if _is_follow_up_scheduled(ix))
    leads_touched = len({ix.related_object_id for ix in interactions})

    fu_rows = build_follow_up_queue_rows(db, today=target)
    fu_summary = summarize_follow_up_queue(fu_rows)
    comp_rows = build_lead_completeness_rows(db)
    comp_summary = summarize_completeness(comp_rows)
    comp_by_lead = {r["lead_id"]: r for r in comp_rows}
    high_priority = sum(
        1
        for r in fu_rows
        if any(s in HIGH_PRIORITY_SEGMENTS for s in (r.get("segments") or []))
    )

    summary = {
        "manual_outreach_sent": manual_outreach,
        "contact_research_updates": contact_research,
        "follow_ups_scheduled": follow_ups,
        "drafts_generated": None,
        "leads_touched": leads_touched,
        "overdue_remaining": fu_summary.get("overdue", 0),
        "due_today_remaining": fu_summary.get("due_today", 0),
        "due_soon": fu_summary.get("due_soon", 0),
        "needs_contact_research": comp_summary.get("needs_contact_research", 0),
        "high_priority_remaining": high_priority,
    }

    highlights = _build_highlights(db, interactions)
    tomorrow_focus = _build_tomorrow_focus(fu_rows, comp_by_lead)
    copyable = build_copyable_summary(target, summary, highlights, tomorrow_focus)

    return {
        "date": target.isoformat(),
        "summary": summary,
        "highlights": highlights,
        "tomorrow_focus": tomorrow_focus,
        "copyable_summary": copyable,
        "warnings": [],
        "degraded": False,
    }


def build_daily_work_summary_degraded(target: date, warning: str) -> dict[str, Any]:
    zero = {
        "manual_outreach_sent": 0,
        "contact_research_updates": 0,
        "follow_ups_scheduled": 0,
        "drafts_generated": None,
        "leads_touched": 0,
        "overdue_remaining": 0,
        "due_today_remaining": 0,
        "due_soon": 0,
        "needs_contact_research": 0,
        "high_priority_remaining": 0,
    }
    return {
        "date": target.isoformat(),
        "summary": zero,
        "highlights": [],
        "tomorrow_focus": [],
        "copyable_summary": (
            f"Daily intelliOffice Summary — {target.isoformat()}\n\n"
            f"{warning}\n\n"
            "No automatic messages were sent by intelliOffice."
        ),
        "warnings": [warning],
        "degraded": True,
    }
