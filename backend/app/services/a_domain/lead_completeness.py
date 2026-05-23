"""D5.4 — derived lead completeness score (read-only, no DB writes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.a_domain.follow_up_rhythm import NO_NEXT_ACTION

STATUS_LABELS = {
    "complete": "Complete",
    "ready_for_outreach": "Ready for Outreach",
    "needs_contact_research": "Needs Contact Research",
    "incomplete": "Incomplete",
}


@dataclass
class LeadCompletenessInput:
    company_name: str = ""
    company_type: str | None = None
    industry: str | None = None
    notes: str | None = None
    business_description: str | None = None
    website: str | None = None
    contact_name: str | None = None
    contact_title: str | None = None
    contact_email: str | None = None
    contact_linkedin_url: str | None = None
    company_linkedin_url: str | None = None
    contact_phone: str | None = None
    segments: list[str] = field(default_factory=list)
    intelligence_score: int = 0
    suggested_next_actions: list[str] = field(default_factory=list)
    next_action: str | None = None
    enrichment_status: str = ""
    touch_count: int = 0


def _has_text(value: str | None) -> bool:
    if value is None:
        return False
    s = value.strip()
    return bool(s) and s not in ("—", "-", "N/A", "n/a")


def _has_enrichment(status: str) -> bool:
    s = (status or "").strip().lower()
    if not s or s in ("—", "no runs", "no_runs"):
        return False
    return True


def _has_contact_method(inp: LeadCompletenessInput) -> bool:
    return (
        _has_text(inp.contact_email)
        or _has_text(inp.contact_linkedin_url)
        or _has_text(inp.company_linkedin_url)
    )


def _status_from_score(score: int) -> str:
    if score >= 80:
        return "complete"
    if score >= 60:
        return "ready_for_outreach"
    if score >= 40:
        return "needs_contact_research"
    return "incomplete"


def _recommend_action_for_missing(missing: list[str], inp: LeadCompletenessInput, status: str) -> str:
    if "website" in missing:
        return "Add website before enrichment."
    if "contact_name" in missing:
        return "Find decision maker contact."
    if "contact_email_or_linkedin" in missing:
        return "Add email or LinkedIn URL."
    if "contact_title" in missing:
        return "Add contact title."
    if "enrichment" in missing:
        return "Run enrichment before outreach."
    if "next_action" in missing:
        return "Set next action."
    if status in ("complete", "ready_for_outreach"):
        return "Generate draft and send by manual review."
    if "touchpoint" in missing:
        return "Generate draft after contact is confirmed."
    return "Review lead profile and fill missing fields."


def compute_lead_completeness(inp: LeadCompletenessInput) -> dict[str, Any]:
    score = 0
    missing: list[str] = []

    if _has_text(inp.company_name):
        score += 10
    if (
        _has_text(inp.company_type)
        or _has_text(inp.industry)
        or _has_text(inp.notes)
        or _has_text(inp.business_description)
    ):
        score += 10
    if _has_text(inp.website):
        score += 10
    else:
        missing.append("website")

    if _has_text(inp.contact_name):
        score += 10
    else:
        missing.append("contact_name")
    if _has_text(inp.contact_title):
        score += 5
    else:
        missing.append("contact_title")
    if _has_contact_method(inp):
        score += 10
    else:
        missing.append("contact_email_or_linkedin")
    if _has_text(inp.contact_phone):
        score += 5

    if inp.segments:
        score += 10
    if inp.intelligence_score > 0:
        score += 5
    has_rec = any(_has_text(a) for a in inp.suggested_next_actions)
    na = (inp.next_action or "").strip()
    if has_rec or (_has_text(na) and na != NO_NEXT_ACTION):
        score += 5

    if _has_text(na) and na != NO_NEXT_ACTION:
        score += 5
    else:
        missing.append("next_action")
    if _has_enrichment(inp.enrichment_status):
        score += 5
    else:
        missing.append("enrichment")
    if inp.touch_count > 0:
        score += 5
    else:
        missing.append("touchpoint")
    draft_ok = _has_contact_method(inp) and bool(inp.segments or inp.intelligence_score > 0)
    if draft_ok:
        score += 5

    status = _status_from_score(score)
    return {
        "score": score,
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "missing_fields": missing,
        "recommended_research_action": _recommend_action_for_missing(missing, inp, status),
    }
