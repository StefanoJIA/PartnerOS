"""D5.12 — derived product fit and project opportunity planner (read-only, no DB writes)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.a_domain.follow_up_rhythm import NO_NEXT_ACTION

PRODUCT_FOCUS_HOSUN = "hosun_lifting_systems"
PRODUCT_FOCUS_FRAMES = "adjustable_desk_frames"
PRODUCT_FOCUS_COLUMNS = "lifting_columns"
PRODUCT_FOCUS_EDUCATION = "jooboo_education_furniture"
PRODUCT_FOCUS_MEDICAL = "medical_workspace"
PRODUCT_FOCUS_PROJECT = "project_supply"
PRODUCT_FOCUS_OEM = "oem_odm_components"

OPPORTUNITY_LEVELS = {
    "high_opportunity": (80, 100),
    "promising": (60, 79),
    "needs_qualification": (40, 59),
    "low_incomplete": (0, 39),
}

DISCOVERY_BY_FOCUS: dict[str, list[str]] = {
    PRODUCT_FOCUS_HOSUN: [
        "Are you currently sourcing adjustable desk frames or lifting columns?",
        "Do you mainly need complete frames, desk legs, or component-level lifting systems?",
        "Do you have target load capacity, frame size, or color requirements?",
        "Is this for dealer stock, a specific project, or OEM/ODM development?",
    ],
    PRODUCT_FOCUS_PROJECT: [
        "Is this tied to a specific office buildout or FF&E project?",
        "Do you have a target project timeline and estimated quantity?",
        "Would a sample or technical spec sheet help the next discussion?",
    ],
    PRODUCT_FOCUS_EDUCATION: [
        "Is this for classroom, training room, or campus furniture procurement?",
        "Do you have an RFP timeline or volume estimate?",
        "Are you looking for standard models or configurable options?",
    ],
    PRODUCT_FOCUS_MEDICAL: [
        "Is the use case clinical workstation, lab bench, or general healthcare workspace?",
        "Are there stability, cleaning, or load requirements?",
        "Would you like to review adjustable workstation options first?",
    ],
    PRODUCT_FOCUS_OEM: [
        "Are you looking for private label, component sourcing, or custom development?",
        "Which components are most relevant: lifting columns, desk legs, frames, control systems?",
        "What volume range and customization requirements should we consider?",
    ],
    PRODUCT_FOCUS_FRAMES: [
        "Are you currently sourcing adjustable desk frames or lifting columns?",
        "Do you have target load capacity, frame size, or color requirements?",
    ],
    PRODUCT_FOCUS_COLUMNS: [
        "Do you mainly need lifting columns, desk legs, or complete frame systems?",
        "Do you have target load capacity or stroke height requirements?",
    ],
}

_INTENT_KEYWORDS = re.compile(
    r"\b(quote|quotation|sample|meeting|rfp|project timeline|timeline|procurement|"
    r"installation|buildout|ff&e|volume|quantity|moq|budget|spec sheet|specification)\b",
    re.I,
)
_LIFT_EXPLICIT = re.compile(
    r"\b(adjustable desk|height adjustable|sit-stand|lifting column|desk frame|lifting system)\b",
    re.I,
)
_PROJECT_KEYWORDS = re.compile(
    r"\b(project|installation|procurement|buildout|contract|ff&e|rollout)\b",
    re.I,
)
_QUOTE_KEYWORDS = re.compile(r"\b(quote|quotation|pricing|price|budget)\b", re.I)
_SAMPLE_KEYWORDS = re.compile(r"\b(sample|mock-up|mockup|prototype)\b", re.I)
_QUANTITY_KEYWORDS = re.compile(r"\b(quantity|volume|units|moq|qty)\b", re.I)
_TIMELINE_KEYWORDS = re.compile(r"\b(timeline|deadline|delivery|schedule|rfp)\b", re.I)
_PRODUCT_TYPE_KEYWORDS = re.compile(
    r"\b(desk frame|lifting column|desk leg|workstation|chair|table|furniture type)\b",
    re.I,
)
_SIZE_KEYWORDS = re.compile(r"\b(size|dimension|width|depth|height|stroke)\b", re.I)
_LOAD_KEYWORDS = re.compile(r"\b(load|capacity|weight|rating|heavy-duty|heavy duty)\b", re.I)
_CERT_KEYWORDS = re.compile(r"\b(certification|certified|ul\b|ce\b|bifma|iso)\b", re.I)
_DELIVERY_KEYWORDS = re.compile(r"\b(delivery|ship|location|address|country|region)\b", re.I)
_COLOR_KEYWORDS = re.compile(r"\b(color|colour|finish|powder coat)\b", re.I)


@dataclass
class ProductFitInput:
    lead_id: str = ""
    company_name: str = ""
    company_type: str | None = None
    industry: str | None = None
    notes: str | None = None
    business_description: str | None = None
    product_interest_tags: str | None = None
    lead_product_interest: str | None = None
    lead_notes: str | None = None
    expected_timeline: str | None = None
    estimated_value: str | None = None
    contact_name: str | None = None
    contact_title: str | None = None
    contact_email: str | None = None
    contact_linkedin_url: str | None = None
    company_linkedin_url: str | None = None
    contact_phone: str | None = None
    segments: list[str] = field(default_factory=list)
    next_action: str | None = None
    follow_up_date_set: bool = False
    completeness_score: int = 0
    enrichment_status: str = ""
    touch_count: int = 0


def _has_text(value: str | None) -> bool:
    if value is None:
        return False
    s = value.strip()
    return bool(s) and s not in ("—", "-", "N/A", "n/a")


def _text_blob(inp: ProductFitInput) -> str:
    parts = [
        inp.notes,
        inp.business_description,
        inp.product_interest_tags,
        inp.lead_product_interest,
        inp.lead_notes,
        inp.expected_timeline,
        inp.estimated_value,
        inp.next_action,
        inp.company_type,
        inp.industry,
    ]
    return " ".join(p for p in parts if p).lower()


def _has_contact_method(inp: ProductFitInput) -> bool:
    return (
        _has_text(inp.contact_email)
        or _has_text(inp.contact_linkedin_url)
        or _has_text(inp.company_linkedin_url)
    )


def _has_enrichment(status: str) -> bool:
    s = (status or "").strip().lower()
    return bool(s) and s not in ("—", "no runs", "no_runs")


def _infer_project_type(segments: list[str]) -> str:
    if "oem_odm_fit" in segments:
        return "oem_odm"
    if "education_vertical" in segments:
        return "education_project"
    if "medical_vertical" in segments:
        return "medical_workspace"
    if "project_based_furniture" in segments:
        return "project_based"
    if "lift_system_signal" in segments or "heavy_duty_fit" in segments:
        return "dealer_supply"
    if "general_office_furniture_only" in segments:
        return "general_office"
    return "unknown"


def _recommended_product_focus(segments: list[str]) -> list[str]:
    focus: list[str] = []
    if "lift_system_signal" in segments or "heavy_duty_fit" in segments:
        focus.extend([PRODUCT_FOCUS_HOSUN, PRODUCT_FOCUS_FRAMES, PRODUCT_FOCUS_COLUMNS])
    if "oem_odm_fit" in segments:
        if PRODUCT_FOCUS_OEM not in focus:
            focus.append(PRODUCT_FOCUS_OEM)
        if PRODUCT_FOCUS_COLUMNS not in focus:
            focus.append(PRODUCT_FOCUS_COLUMNS)
    if "project_based_furniture" in segments:
        if PRODUCT_FOCUS_PROJECT not in focus:
            focus.append(PRODUCT_FOCUS_PROJECT)
    if "education_vertical" in segments:
        focus.append(PRODUCT_FOCUS_EDUCATION)
    if "medical_vertical" in segments:
        focus.append(PRODUCT_FOCUS_MEDICAL)
    if "general_office_furniture_only" in segments and not focus:
        focus.extend([PRODUCT_FOCUS_FRAMES, PRODUCT_FOCUS_HOSUN])
    if not focus:
        focus.append(PRODUCT_FOCUS_FRAMES)
    seen: set[str] = set()
    ordered: list[str] = []
    for item in focus:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _score_product_fit(segments: list[str]) -> int:
    score = 0
    if "lift_system_signal" in segments:
        score += 15
    if "project_based_furniture" in segments:
        score += 10
    if "education_vertical" in segments:
        score += 8
    if "medical_vertical" in segments:
        score += 8
    if "oem_odm_fit" in segments:
        score += 10
    if "general_office_furniture_only" in segments and score == 0:
        score += 5
    return min(score, 35)


def _score_contact_readiness(inp: ProductFitInput) -> int:
    score = 0
    if _has_text(inp.contact_name):
        score += 5
    if _has_contact_method(inp):
        score += 8
    if _has_text(inp.contact_title):
        score += 4
    if _has_text(inp.contact_phone):
        score += 3
    return min(score, 20)


def _score_intent(inp: ProductFitInput, blob: str) -> int:
    score = 0
    if _INTENT_KEYWORDS.search(blob):
        score += 10
    if _LIFT_EXPLICIT.search(blob) or "lift_system_signal" in inp.segments:
        score += 8
    if _PROJECT_KEYWORDS.search(blob) or "project_based_furniture" in inp.segments:
        score += 5
    na = (inp.next_action or "").strip()
    if _has_text(na) and na != NO_NEXT_ACTION:
        score += 2
    return min(score, 25)


def _score_operational(inp: ProductFitInput) -> int:
    score = 0
    if inp.completeness_score >= 80:
        score += 8
    elif inp.completeness_score >= 60:
        score += 4
    if inp.follow_up_date_set:
        score += 4
    if _has_enrichment(inp.enrichment_status):
        score += 4
    if inp.touch_count > 0:
        score += 4
    return min(score, 20)


def _opportunity_level(score: int) -> str:
    if score >= 80:
        return "high_opportunity"
    if score >= 60:
        return "promising"
    if score >= 40:
        return "needs_qualification"
    return "low_incomplete"


def _detect_missing_quote_info(inp: ProductFitInput, blob: str, focus: list[str]) -> list[str]:
    missing: list[str] = []
    if not _has_contact_method(inp):
        missing.append("contact_email_or_linkedin")
    if not focus:
        missing.append("product_type")
    elif not (_PRODUCT_TYPE_KEYWORDS.search(blob) or inp.lead_product_interest):
        missing.append("product_type")
    if not (_QUANTITY_KEYWORDS.search(blob) or _has_text(inp.estimated_value)):
        missing.append("quantity_or_volume")
    if not _SIZE_KEYWORDS.search(blob):
        missing.append("desktop/frame size")
    if "lift_system_signal" in inp.segments and not _LOAD_KEYWORDS.search(blob):
        missing.append("load_capacity_requirement")
    if not _COLOR_KEYWORDS.search(blob):
        missing.append("color_or_finish")
    if not (_TIMELINE_KEYWORDS.search(blob) or _has_text(inp.expected_timeline)):
        missing.append("project_timeline")
    if not _DELIVERY_KEYWORDS.search(blob):
        missing.append("delivery_location")
    if not _CERT_KEYWORDS.search(blob):
        missing.append("certification_requirement")
    if _SAMPLE_KEYWORDS.search(blob) and not _QUANTITY_KEYWORDS.search(blob):
        missing.append("sample_quantity")
    if _QUOTE_KEYWORDS.search(blob) and not re.search(r"\bbudget\b", blob, re.I):
        missing.append("target_price_or_budget")
    if not _has_text(inp.contact_title):
        missing.append("decision_maker_role")
    return missing


def _quote_readiness(
    inp: ProductFitInput,
    focus: list[str],
    project_type: str,
    blob: str,
    missing: list[str],
) -> str:
    if not _has_text(inp.company_name) or not _has_contact_method(inp) or not focus:
        return "not_ready"
    if project_type == "unknown" and not inp.segments:
        return "not_ready"

    has_project_signal = bool(
        _QUANTITY_KEYWORDS.search(blob)
        or _PRODUCT_TYPE_KEYWORDS.search(blob)
        or _SAMPLE_KEYWORDS.search(blob)
        or _TIMELINE_KEYWORDS.search(blob)
        or _QUOTE_KEYWORDS.search(blob)
        or _has_text(inp.expected_timeline)
        or _has_text(inp.lead_product_interest)
    )
    if has_project_signal and len(missing) <= 4:
        return "ready"
    if focus and project_type != "unknown":
        return "almost_ready"
    return "not_ready"


def _sample_readiness(blob: str, quote_readiness: str, missing: list[str]) -> str:
    if quote_readiness == "not_ready":
        return "not_ready"
    if _SAMPLE_KEYWORDS.search(blob):
        if "sample_quantity" in missing or "product_type" in missing:
            return "needs_specs"
        return "ready"
    if quote_readiness == "ready":
        return "needs_specs"
    return "needs_specs"


def _discovery_questions(focus: list[str]) -> list[str]:
    primary = focus[0] if focus else PRODUCT_FOCUS_FRAMES
    pool: list[str] = []
    for key in [primary] + focus[1:]:
        for q in DISCOVERY_BY_FOCUS.get(key, []):
            if q not in pool:
                pool.append(q)
    if not pool:
        pool = DISCOVERY_BY_FOCUS[PRODUCT_FOCUS_FRAMES][:]
    return pool[:5]


def _sales_angle(focus: list[str], project_type: str, company_name: str) -> str:
    name = company_name or "this lead"
    if PRODUCT_FOCUS_OEM in focus:
        return (
            f"Position intelliOffice as an OEM/ODM lifting components partner for {name} — "
            "focus on columns, legs, and control systems without promising pricing or lead times."
        )
    if project_type == "project_based":
        return (
            f"Position intelliOffice as a project supply partner for adjustable desk frames and "
            f"lifting systems on {name}'s FF&E or buildout work."
        )
    if PRODUCT_FOCUS_EDUCATION in focus:
        return (
            f"Position JOOBOO education furniture and scalable classroom supply options for {name}."
        )
    if PRODUCT_FOCUS_MEDICAL in focus:
        return (
            f"Position stable adjustable workstation and lifting system options for {name}'s "
            "healthcare or lab environment."
        )
    if PRODUCT_FOCUS_HOSUN in focus:
        return (
            f"Position HOSUN lifting systems — adjustable desk frames, desk legs, and lifting columns — "
            f"for {name}."
        )
    return (
        f"Introduce adjustable desk frame and lifting system capabilities to {name}; "
        "qualify project scope before any quote discussion."
    )


def _next_product_action(
    quote_readiness: str,
    missing: list[str],
    focus: list[str],
) -> str:
    if quote_readiness == "ready":
        return "Confirm missing details with the customer, then prepare a human-reviewed quote outline."
    if quote_readiness == "almost_ready":
        gaps = ", ".join(m.replace("_", " ") for m in missing[:3]) or "project details"
        return f"Ask for quantity, product type, and project timeline before preparing quote. Still missing: {gaps}."
    if not focus:
        return "Clarify product interest and project type before discussing samples or quotes."
    return "Confirm contact method and product direction, then ask discovery questions before quote or sample talk."


def compute_product_fit(inp: ProductFitInput) -> dict[str, Any]:
    """Derive product fit, opportunity score, and quote readiness from lead context."""
    blob = _text_blob(inp)
    focus = _recommended_product_focus(inp.segments)
    project_type = _infer_project_type(inp.segments)

    opp_score = (
        _score_product_fit(inp.segments)
        + _score_contact_readiness(inp)
        + _score_intent(inp, blob)
        + _score_operational(inp)
    )
    opp_score = min(100, max(0, opp_score))

    missing = _detect_missing_quote_info(inp, blob, focus)
    quote_readiness = _quote_readiness(inp, focus, project_type, blob, missing)
    sample_readiness = _sample_readiness(blob, quote_readiness, missing)

    questions = _discovery_questions(focus)
    sales_angle = _sales_angle(focus, project_type, inp.company_name)
    next_action = _next_product_action(quote_readiness, missing, focus)

    warnings: list[str] = []
    warnings.append(
        "Suggestions only — no prices, inventory, certifications, or lead times are confirmed."
    )
    if quote_readiness == "ready":
        warnings.append("Quote-ready means information sufficiency for discovery — not an auto-generated quote.")
    if not inp.segments:
        warnings.append("No market fit segments assigned; product focus is a default starting point.")

    return {
        "lead_id": inp.lead_id,
        "company_name": inp.company_name,
        "recommended_product_focus": focus,
        "project_opportunity_score": opp_score,
        "opportunity_level": _opportunity_level(opp_score),
        "project_type": project_type,
        "quote_readiness": quote_readiness,
        "sample_readiness": sample_readiness,
        "missing_quote_info": missing,
        "recommended_discovery_questions": questions,
        "recommended_next_product_action": next_action,
        "sales_angle": sales_angle,
        "warnings": warnings,
    }
