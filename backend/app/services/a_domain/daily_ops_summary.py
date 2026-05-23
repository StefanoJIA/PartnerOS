"""D5.8 — daily operations command center (read-only aggregation)."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Company, Interaction, Lead
from app.services.a_domain.follow_up_rhythm import HIGH_PRIORITY_SEGMENTS
from app.services.a_domain.follow_up_queue import build_follow_up_queue_rows, summarize_follow_up_queue
from app.services.a_domain.lead_completeness_board import (
    build_lead_completeness_rows,
    summarize_completeness,
)

QUICK_ACTIONS: list[dict[str, str]] = [
    {"label": "Import Leads", "path": "/lead-intake"},
    {"label": "Review Completeness", "path": "/lead-intelligence?filter=needs_contact_research"},
    {"label": "Follow Up Due", "path": "/lead-intelligence?filter=due_today"},
    {"label": "Generate Drafts", "path": "/lead-intelligence"},
    {"label": "System Health", "path": "/system-health"},
    {"label": "Portal Mock", "path": "/portal-consumer-mock"},
]

SAFETY = {
    "automatic_sending_enabled": False,
    "linkedin_automation_enabled": False,
    "outlook_integration_enabled": False,
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


def _recent_manual_outreach(db: Session, limit: int = 5) -> list[dict[str, Any]]:
    rows = (
        db.query(Interaction)
        .filter(
            Interaction.related_object_type == "lead",
            Interaction.summary.ilike("%manually_sent=true%"),
        )
        .order_by(Interaction.interaction_date.desc())
        .limit(limit)
        .all()
    )
    out: list[dict[str, Any]] = []
    for ix in rows:
        company_name = "—"
        next_action = None
        lead = db.query(Lead).filter(Lead.id == ix.related_object_id).first()
        if lead:
            next_action = lead.next_action
            company = db.query(Company).filter(Company.id == lead.company_id).first()
            if company:
                company_name = company.company_name
        out.append(
            {
                "lead_id": str(ix.related_object_id),
                "company_name": company_name,
                "interaction_type": ix.interaction_type,
                "channel": ix.channel,
                "timestamp": ix.interaction_date.isoformat() if ix.interaction_date else None,
                "next_action": next_action,
            }
        )
    return out


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

    return {
        "summary": summary,
        "today_focus": _build_today_focus(fu_rows, comp_by_lead),
        "recent_outreach": _recent_manual_outreach(db),
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
        "recent_outreach": [],
        "quick_actions": QUICK_ACTIONS,
        "safety": SAFETY,
        "warnings": [warning],
        "degraded": True,
    }
