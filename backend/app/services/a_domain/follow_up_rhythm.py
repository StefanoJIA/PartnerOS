"""D5.2.7 — derived follow-up categories (read-only, no DB writes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

NO_NEXT_ACTION = "No next action set."

HIGH_PRIORITY_SEGMENTS = frozenset(
    {"lift_system_signal", "project_based_furniture", "medical_vertical"}
)

TODAY_FOCUS_CATEGORIES = frozenset(
    {
        "high_priority",
        "needs_first_outreach",
        "waiting_for_reply",
        "follow_up_soon",
    }
)

STATUS_LABELS = {
    "needs_first_outreach": "First outreach",
    "waiting_for_reply": "Waiting reply",
    "follow_up_soon": "Follow up soon",
    "needs_contact_research": "Research contact",
    "high_priority": "High priority",
    "needs_enrichment": "Needs enrichment",
    "ready_for_catalog_quote": "Catalog / quote",
}

BADGE_ORDER = [
    "high_priority",
    "needs_contact_research",
    "waiting_for_reply",
    "follow_up_soon",
    "needs_first_outreach",
    "ready_for_catalog_quote",
    "needs_enrichment",
]


@dataclass
class RhythmLead:
    company_name: str
    score: int
    segments: list[str]
    next_action: str
    touch_count: int
    last_touch: str
    last_touch_date: str | None
    contact_email: str | None
    linkedin_url: str | None
    enrichment_status: str
    company_website: str | None
    categories: list[str] = field(default_factory=list)


def _lower(text: str) -> str:
    return (text or "").lower()


def _matches_any(text: str, phrases: tuple[str, ...]) -> bool:
    t = _lower(text)
    return any(p in t for p in phrases)


def _is_older_than_days(iso: str | None, days: int) -> bool:
    if not iso:
        return False
    try:
        raw = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
        return delta.total_seconds() >= days * 86400
    except (ValueError, TypeError):
        return False


def classify_follow_up_categories(lead: RhythmLead) -> list[str]:
    cats: list[str] = []
    na = lead.next_action
    lt = lead.last_touch
    has_email = bool((lead.contact_email or "").strip())
    has_linkedin = bool((lead.linkedin_url or "").strip())
    has_segments = bool(lead.segments)
    enrich_lower = _lower(lead.enrichment_status)
    manually_sent = "manually_sent=true" in _lower(lt) or "manual outreach" in _lower(lt)

    if lead.touch_count == 0 and has_segments:
        cats.append("needs_first_outreach")

    if (
        (manually_sent and _matches_any(na, ("wait", "follow up", "waiting")))
        or (lead.touch_count > 0 and _matches_any(na, ("wait for reply", "waiting for")))
    ):
        cats.append("waiting_for_reply")

    if (
        _matches_any(na, ("follow up", "follow-up"))
        or (lead.touch_count > 0 and manually_sent and _is_older_than_days(lead.last_touch_date, 3))
    ):
        cats.append("follow_up_soon")

    if (not has_email and not has_linkedin) or _matches_any(na, ("research contact",)):
        cats.append("needs_contact_research")

    if (
        lead.score >= 70
        or any(s in HIGH_PRIORITY_SEGMENTS for s in lead.segments)
        or _matches_any(na, ("quotation", "quote", "sample", "meeting"))
    ):
        cats.append("high_priority")

    needs_enrich = (
        lead.enrichment_status in ("No runs", "—")
        or "no run" in enrich_lower
        or (bool((lead.company_website or "").strip()) and not enrich_lower.startswith("completed"))
    )
    if needs_enrich and not enrich_lower.startswith("completed"):
        cats.append("needs_enrichment")

    if _matches_any(na, ("catalog", "quotation", "quote", "sample", "meeting")):
        cats.append("ready_for_catalog_quote")

    return cats


def primary_status_badge(categories: list[str]) -> str | None:
    for c in BADGE_ORDER:
        if c in categories:
            return c
    return None


def summarize_counts(leads: list[RhythmLead]) -> dict[str, int]:
    counts = {
        "total": len(leads),
        "needs_first_outreach": 0,
        "waiting_for_reply": 0,
        "follow_up_soon": 0,
        "needs_contact_research": 0,
        "high_priority": 0,
        "needs_enrichment": 0,
        "ready_for_catalog_quote": 0,
    }
    for lead in leads:
        lead.categories = classify_follow_up_categories(lead)
        for c in lead.categories:
            if c in counts:
                counts[c] += 1
    return counts


def segment_breakdown(leads: list[RhythmLead]) -> dict[str, int]:
    keys = [
        "lift_system_signal",
        "project_based_furniture",
        "medical_vertical",
        "education_vertical",
        "general_office_furniture_only",
    ]
    out = {k: 0 for k in keys}
    for lead in leads:
        for s in lead.segments:
            if s in out:
                out[s] += 1
    return out


def recommend_top_actions(leads: list[RhythmLead], limit: int = 10) -> list[tuple[str, str, str]]:
    priority = [
        "high_priority",
        "needs_first_outreach",
        "waiting_for_reply",
        "follow_up_soon",
        "needs_contact_research",
        "ready_for_catalog_quote",
        "needs_enrichment",
    ]
    ranked: list[tuple[int, int, RhythmLead, str]] = []
    for lead in leads:
        if not lead.categories:
            lead.categories = classify_follow_up_categories(lead)
        rank = len(priority)
        for i, cat in enumerate(priority):
            if cat in lead.categories:
                rank = i
                break
        primary = primary_status_badge(lead.categories)
        reason = STATUS_LABELS.get(primary or "", "Review queue")
        ranked.append((rank, -lead.score, lead, reason))
    ranked.sort(key=lambda x: (x[0], x[1]))
    rows: list[tuple[str, str, str]] = []
    for rank, _neg_score, lead, reason in ranked[:limit]:
        action = lead.next_action if lead.next_action != NO_NEXT_ACTION else "Set next action in Lead Intelligence"
        rows.append((lead.company_name, action, reason))
    return rows
