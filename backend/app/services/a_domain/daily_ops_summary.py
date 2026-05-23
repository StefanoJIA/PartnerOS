"""D5.8 / D5.9 — daily operations command center (read-only aggregation)."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models import Company, Interaction, Lead
from app.services.a_domain.follow_up_rhythm import HIGH_PRIORITY_SEGMENTS
from app.services.a_domain.follow_up_queue import build_follow_up_queue_rows, summarize_follow_up_queue
from app.services.a_domain.lead_completeness_board import (
    build_lead_completeness_rows,
    summarize_completeness,
)
from app.services.a_domain.lead_timeline import _is_contact_research, _is_manual_send

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

QUICK_ACTIONS: list[dict[str, str]] = [
    {"label": "Import Leads", "path": "/lead-intake"},
    {"label": "Review Completeness", "path": "/lead-intelligence?filter=needs_contact_research"},
    {"label": "Follow Up Due", "path": "/lead-intelligence?filter=due_today"},
    {"label": "Overdue Follow-up", "path": "/lead-intelligence?filter=overdue"},
    {"label": "Generate Drafts", "path": "/lead-intelligence"},
    {"label": "System Health", "path": "/system-health"},
    {"label": "Portal Mock", "path": "/portal-consumer-mock"},
]

SAFETY = {
    "automatic_sending_enabled": False,
    "linkedin_automation_enabled": False,
    "outlook_integration_enabled": False,
}


def _mask_summary(text: str | None) -> str | None:
    if not text:
        return None
    masked = EMAIL_RE.sub("[email]", text.strip())
    if len(masked) > 200:
        return masked[:197] + "..."
    return masked


def _activity_badge(ix: Interaction) -> tuple[str, bool, bool]:
    if _is_manual_send(ix.summary, ix.subject):
        return "Manual sent", True, False
    if _is_contact_research(ix.interaction_type, ix.channel, ix.summary):
        return "Contact research", False, True
    summary_lower = (ix.summary or "").lower()
    if ix.interaction_type == "follow_up_scheduled" or "manually_scheduled=true" in summary_lower:
        return "Follow-up scheduled", False, False
    return "Activity", False, False


def _build_lead_context(
    db: Session,
    lead_ids: set[Any],
) -> dict[str, tuple[Lead | None, Company | None]]:
    if not lead_ids:
        return {}
    leads = db.query(Lead).filter(Lead.id.in_(list(lead_ids))).all()
    company_ids = {l.company_id for l in leads if l.company_id}
    companies: dict[Any, Company] = {}
    if company_ids:
        companies = {
            c.id: c for c in db.query(Company).filter(Company.id.in_(list(company_ids))).all()
        }
    return {str(l.id): (l, companies.get(l.company_id)) for l in leads}


def _interaction_to_activity(
    ix: Interaction,
    ctx: dict[str, tuple[Lead | None, Company | None]],
) -> dict[str, Any]:
    lead_id = str(ix.related_object_id)
    lead, company = ctx.get(lead_id, (None, None))
    company_name = company.company_name if company else "—"
    badge, is_manual, is_research = _activity_badge(ix)
    return {
        "lead_id": lead_id,
        "company_name": company_name,
        "type": ix.interaction_type or "touchpoint",
        "interaction_type": ix.interaction_type or "touchpoint",
        "channel": ix.channel or "—",
        "summary": _mask_summary(ix.summary or ix.content),
        "timestamp": ix.interaction_date.isoformat() if ix.interaction_date else None,
        "badge": badge,
        "is_manual_send": is_manual,
        "is_contact_research": is_research,
        "next_action": lead.next_action if lead else None,
    }


def _fetch_recent_lead_interactions(db: Session, limit: int = 40) -> list[Interaction]:
    return (
        db.query(Interaction)
        .filter(Interaction.related_object_type == "lead")
        .order_by(Interaction.interaction_date.desc())
        .limit(limit)
        .all()
    )


def _build_recent_activity(db: Session, limit: int = 10) -> dict[str, list[dict[str, Any]]]:
    rows = _fetch_recent_lead_interactions(db, limit=40)
    lead_ids = {ix.related_object_id for ix in rows}
    ctx = _build_lead_context(db, lead_ids)

    combined: list[dict[str, Any]] = []
    manual: list[dict[str, Any]] = []
    research: list[dict[str, Any]] = []

    for ix in rows:
        item = _interaction_to_activity(ix, ctx)
        combined.append(item)
        if item["is_manual_send"]:
            manual.append(item)
        if item["is_contact_research"]:
            research.append(item)

    return {
        "recent_activity": combined[:limit],
        "recent_manual_outreach": manual[:5],
        "recent_contact_research": research[:5],
        "recent_outreach": manual[:5],
    }


def _focus_priority_and_reason(
    fu: dict[str, Any],
    comp: dict[str, Any] | None,
) -> tuple[int, str]:
    due = fu.get("due_status") or "no_follow_up_date"
    segments = fu.get("segments") or []
    missing = (comp or {}).get("missing_fields") or []
    comp_status = (comp or {}).get("status")

    if due == "overdue":
        return 1, "Overdue follow-up"
    if due == "due_today":
        return 2, "Due today"
    if due == "due_soon":
        return 3, "Due soon"
    if any(s in HIGH_PRIORITY_SEGMENTS for s in segments):
        if "lift_system_signal" in segments:
            return 4, "High-priority lifting systems lead"
        if "medical_vertical" in segments:
            return 4, "High-priority medical vertical lead"
        if "project_based_furniture" in segments:
            return 4, "High-priority project furniture lead"
        return 4, "High-priority lead"
    if comp_status == "needs_contact_research":
        return 5, "Needs contact research"
    if due == "no_follow_up_date" and (fu.get("lead_score") or 0) >= 70:
        return 6, "No follow-up date — high score"
    if "enrichment" in missing:
        return 7, "Needs enrichment before outreach"
    if comp_status == "ready_for_outreach":
        return 8, "Ready for outreach"
    if fu.get("waiting_reply"):
        return 9, "Waiting for reply"
    return 99, "Review next action"


def _build_today_focus(
    fu_rows: list[dict[str, Any]],
    comp_by_lead: dict[str, dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for fu in fu_rows:
        comp = comp_by_lead.get(fu["lead_id"])
        prio, reason = _focus_priority_and_reason(fu, comp)
        priority_label = "high" if prio <= 4 else ("medium" if prio <= 7 else "normal")
        candidates.append(
            (
                prio,
                {
                    "lead_id": fu["lead_id"],
                    "company_name": fu["company_name"],
                    "reason": reason,
                    "segments": fu.get("segments") or [],
                    "due_status": fu.get("due_status") or "no_follow_up_date",
                    "next_action": fu.get("next_action"),
                    "priority": priority_label,
                    "lead_score": fu.get("lead_score") or 0,
                },
            )
        )
    candidates.sort(key=lambda x: (x[0], -(x[1].get("lead_score") or 0)))
    return [c[1] for c in candidates[:limit]]


def build_daily_ops_summary(db: Session, today: date | None = None) -> dict[str, Any]:
    fu_rows = build_follow_up_queue_rows(db, today=today)
    fu_summary = summarize_follow_up_queue(fu_rows)

    comp_rows = build_lead_completeness_rows(db)
    comp_summary = summarize_completeness(comp_rows)
    comp_by_lead = {r["lead_id"]: r for r in comp_rows}

    high_priority = sum(
        1
        for r in fu_rows
        if any(s in HIGH_PRIORITY_SEGMENTS for s in (r.get("segments") or []))
    )
    needs_enrichment = sum(1 for r in comp_rows if "enrichment" in r.get("missing_fields", []))

    summary = {
        "total_leads": fu_summary.get("total", 0),
        "overdue": fu_summary.get("overdue", 0),
        "due_today": fu_summary.get("due_today", 0),
        "due_soon": fu_summary.get("due_soon", 0),
        "high_priority": high_priority,
        "needs_contact_research": comp_summary.get("needs_contact_research", 0),
        "ready_for_outreach": comp_summary.get("ready_for_outreach", 0),
        "waiting_reply": fu_summary.get("waiting_reply", 0),
        "needs_enrichment": needs_enrichment,
    }

    activity = _build_recent_activity(db)

    return {
        "summary": summary,
        "today_focus": _build_today_focus(fu_rows, comp_by_lead),
        **activity,
        "quick_actions": QUICK_ACTIONS,
        "safety": SAFETY,
        "warnings": [],
        "degraded": False,
    }


def build_daily_ops_summary_degraded(warning: str) -> dict[str, Any]:
    zero = {
        "total_leads": 0,
        "overdue": 0,
        "due_today": 0,
        "due_soon": 0,
        "high_priority": 0,
        "needs_contact_research": 0,
        "ready_for_outreach": 0,
        "waiting_reply": 0,
        "needs_enrichment": 0,
    }
    return {
        "summary": zero,
        "today_focus": [],
        "recent_activity": [],
        "recent_manual_outreach": [],
        "recent_contact_research": [],
        "recent_outreach": [],
        "quick_actions": QUICK_ACTIONS,
        "safety": SAFETY,
        "warnings": [warning],
        "degraded": True,
    }
