"""D5.12 / D5.17 — derived product fit and project opportunity planner (read-only, no DB writes)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.a_domain.follow_up_rhythm import NO_NEXT_ACTION

PRODUCT_FOCUS_HOSUN = "hosun_lifting_systems"
PRODUCT_FOCUS_FRAMES = "adjustable_desk_frames"
PRODUCT_FOCUS_COLUMNS = "lifting_columns"
PRODUCT_FOCUS_DESK_LEGS = "desk_legs"
PRODUCT_FOCUS_HEAVY_DUTY = "heavy_duty_lifting_systems"
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
        "Are you looking for complete adjustable desk frames, desk legs, lifting columns, or component-level systems?",
        "Is this for dealer supply, a specific project, or OEM/ODM development?",
        "What quantity range and timeline should we consider?",
        "Are there load capacity, frame size, color, or finish requirements?",
    ],
    PRODUCT_FOCUS_PROJECT: [
        "Is this tied to a specific FF&E or office buildout project?",
        "What quantity range and timeline should we consider?",
        "Would a catalog, spec sheet, or sample discussion help the next step?",
    ],
    PRODUCT_FOCUS_EDUCATION: [
        "Is this for classroom, training room, or campus furniture procurement?",
        "Do you have an RFP timeline or estimated volume?",
        "Are you looking for standard models or configurable options?",
    ],
    PRODUCT_FOCUS_MEDICAL: [
        "Is the use case clinical workstation, lab bench, or general healthcare workspace?",
        "Are there stability, cleaning, or load requirements?",
    ],
    PRODUCT_FOCUS_OEM: [
        "Are you looking for private label, component sourcing, or custom development?",
        "Which components are most relevant: lifting columns, desk legs, frames, or control systems?",
        "What volume range and customization requirements should we consider?",
    ],
    PRODUCT_FOCUS_FRAMES: [
        "Are you currently sourcing adjustable desk frames or lifting columns?",
        "What quantity range and timeline should we consider?",
    ],
    PRODUCT_FOCUS_COLUMNS: [
        "Do you mainly need lifting columns, desk legs, or complete frame systems?",
        "Do you have target load capacity or stroke height requirements?",
    ],
    PRODUCT_FOCUS_DESK_LEGS: [
        "Are you sourcing desk legs, lifting legs, or table leg modules?",
        "What load capacity and finish requirements should we note?",
    ],
    PRODUCT_FOCUS_HEAVY_DUTY: [
        "Is this for industrial workstation, lab bench, or heavy-load desk applications?",
        "What load capacity or stability requirements should we understand?",
    ],
}

_INTENT_KEYWORDS = re.compile(
    r"\b(quote|quotation|sample|meeting|rfp|project timeline|timeline|procurement|"
    r"installation|buildout|ff&e|volume|quantity|moq|budget|spec sheet|specification)\b",
    re.I,
)
_FRAME_KW = re.compile(
    r"\b(adjustable desk frame|sit-stand frame|height adjustable desk|standing desk frame|"
    r"electric desk frame|dual motor frame|desk frame)\b",
    re.I,
)
_LEGS_KW = re.compile(
    r"\b(desk legs|lifting legs|adjustable legs|table legs|height adjustable legs|lifting leg)\b",
    re.I,
)
_COLUMNS_KW = re.compile(
    r"\b(lifting column|lifting columns|telescopic column|column actuator|"
    r"electric lifting column|linear column|lift column)\b",
    re.I,
)
_HEAVY_KW = re.compile(
    r"\b(heavy duty|heavy-duty|high load|300kg|660 lb|industrial workstation|"
    r"bench lifting|lab bench lifting|heavy load desk)\b",
    re.I,
)
_OEM_KW = re.compile(
    r"\b(oem|odm|private label|component sourcing|customization|custom development|"
    r"control box|actuator|lifting component|manufacturer)\b",
    re.I,
)
_LIFT_EXPLICIT = re.compile(
    r"\b(adjustable desk|height adjustable|sit-stand|lifting column|desk frame|lifting system)\b",
    re.I,
)
_PROJECT_KEYWORDS = re.compile(
    r"\b(project|installation|procurement|buildout|contract|ff&e|rollout|ffe)\b",
    re.I,
)
_QUOTE_SAMPLE_MEETING = re.compile(r"\b(quote|quotation|sample|meeting)\b", re.I)
_QUOTE_KEYWORDS = re.compile(r"\b(quote|quotation|pricing|price|budget)\b", re.I)
_SAMPLE_KEYWORDS = re.compile(r"\b(sample|mock-up|mockup|prototype)\b", re.I)
_QUANTITY_KEYWORDS = re.compile(r"\b(quantity|volume|units|moq|qty)\b", re.I)
_TIMELINE_KEYWORDS = re.compile(r"\b(timeline|deadline|delivery|schedule|rfp|procurement)\b", re.I)
_PRODUCT_TYPE_KEYWORDS = re.compile(
    r"\b(desk frame|lifting column|desk leg|workstation|chair|table|furniture type)\b",
    re.I,
)
_SIZE_KEYWORDS = re.compile(r"\b(size|dimension|width|depth|height|stroke|frame size|desktop)\b", re.I)
_LOAD_KEYWORDS = re.compile(r"\b(load|capacity|weight|rating|heavy-duty|heavy duty)\b", re.I)
_CERT_KEYWORDS = re.compile(r"\b(certification|certified|ul\b|ce\b|bifma|iso)\b", re.I)
_DELIVERY_KEYWORDS = re.compile(r"\b(delivery|ship|location|address|country|region)\b", re.I)
_COLOR_KEYWORDS = re.compile(r"\b(color|colour|finish|powder coat)\b", re.I)
_CONTROL_KW = re.compile(r"\b(control system|control box|handset|controller)\b", re.I)

_EDUCATION_STRONG = re.compile(
    r"\b(school|classroom|campus|student desk|training room|university procurement|"
    r"school district|learning space|classroom project|education procurement|"
    r"campus furniture|school furniture procurement|rfp.*education|education rfp)\b",
    re.I,
)
_EDUCATION_WEAK = re.compile(
    r"\b(jooboo|education option|school furniture line|education catalog|"
    r"also provide school|education line also|jooboo education)\b",
    re.I,
)

_MISSING_PRIORITY = (
    "contact_email_or_linkedin",
    "product_type",
    "quantity_or_volume",
    "project_timeline",
    "delivery_location",
    "frame_size_or_desktop_size",
    "load_capacity_requirement",
    "color_or_finish",
    "component_type",
    "control_system_requirement",
    "installation_or_packaging_need",
    "classroom_or_campus_use_case",
    "rfp_or_procurement_timeline",
    "volume_estimate",
    "workstation_use_case",
    "stability_or_load_requirement",
    "component_category",
    "customization_requirement",
    "decision_maker_role",
    "certification_requirement",
    "sample_quantity",
    "target_price_or_budget",
    "desktop/frame size",
)


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


def _is_education_company(company_type: str | None, industry: str | None) -> bool:
    blob = f"{company_type or ''} {industry or ''}".lower()
    return "education" in blob and "office furniture dealer" not in blob


def _strong_education_signal(blob: str, company_type: str | None, industry: str | None) -> bool:
    if _EDUCATION_STRONG.search(blob):
        return True
    if _is_education_company(company_type, industry):
        return True
    if re.search(r"\beducation furniture\b", blob, re.I):
        if _PROJECT_KEYWORDS.search(blob) or "ff&e" in blob:
            return False
        if _is_education_company(company_type, industry):
            return True
        return "classroom" in blob or "campus" in blob or "school" in blob
    return False


def _refine_segments(segments: list[str], blob: str, company_type: str | None, industry: str | None) -> list[str]:
    segs = list(segments)
    has_project = "project_based_furniture" in segs or _PROJECT_KEYWORDS.search(blob)

    if "education_vertical" in segs and not _strong_education_signal(blob, company_type, industry):
        segs = [s for s in segs if s != "education_vertical"]
    elif "education_vertical" in segs and has_project and not _is_education_company(company_type, industry):
        if not _EDUCATION_STRONG.search(blob):
            segs = [s for s in segs if s != "education_vertical"]

    if _PROJECT_KEYWORDS.search(blob) and "project_based_furniture" not in segs:
        segs.append("project_based_furniture")
    if (_OEM_KW.search(blob) and (_COLUMNS_KW.search(blob) or _LEGS_KW.search(blob) or _FRAME_KW.search(blob))):
        if "oem_odm_fit" not in segs:
            segs.append("oem_odm_fit")
    if (_FRAME_KW.search(blob) or _COLUMNS_KW.search(blob) or _LEGS_KW.search(blob)) and "lift_system_signal" not in segs:
        if not ("general_office_furniture_only" in segs and not _LIFT_EXPLICIT.search(blob)):
            segs.append("lift_system_signal")
    if _HEAVY_KW.search(blob) and "heavy_duty_fit" not in segs:
        segs.append("heavy_duty_fit")

    seen: set[str] = set()
    out: list[str] = []
    for s in segs:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


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


def _append_unique(focus: list[str], item: str) -> None:
    if item not in focus:
        focus.append(item)


def _recommended_product_focus(segments: list[str], blob: str, company_type: str | None, industry: str | None) -> list[str]:
    focus: list[str] = []
    has_lift_seg = "lift_system_signal" in segments or "heavy_duty_fit" in segments
    has_explicit_lift = bool(_FRAME_KW.search(blob) or _COLUMNS_KW.search(blob) or _LEGS_KW.search(blob) or _LIFT_EXPLICIT.search(blob))

    if "oem_odm_fit" in segments or (_OEM_KW.search(blob) and has_explicit_lift):
        _append_unique(focus, PRODUCT_FOCUS_OEM)
        if _COLUMNS_KW.search(blob):
            _append_unique(focus, PRODUCT_FOCUS_COLUMNS)
        if _LEGS_KW.search(blob):
            _append_unique(focus, PRODUCT_FOCUS_DESK_LEGS)

    if "project_based_furniture" in segments:
        _append_unique(focus, PRODUCT_FOCUS_PROJECT)

    if has_lift_seg or has_explicit_lift:
        _append_unique(focus, PRODUCT_FOCUS_HOSUN)
        if _FRAME_KW.search(blob) or has_lift_seg:
            _append_unique(focus, PRODUCT_FOCUS_FRAMES)
        if _COLUMNS_KW.search(blob):
            _append_unique(focus, PRODUCT_FOCUS_COLUMNS)
        if _LEGS_KW.search(blob):
            _append_unique(focus, PRODUCT_FOCUS_DESK_LEGS)

    if _HEAVY_KW.search(blob) or "heavy_duty_fit" in segments:
        _append_unique(focus, PRODUCT_FOCUS_HEAVY_DUTY)

    if "medical_vertical" in segments:
        _append_unique(focus, PRODUCT_FOCUS_MEDICAL)

    if "education_vertical" in segments and _strong_education_signal(blob, company_type, industry):
        _append_unique(focus, PRODUCT_FOCUS_EDUCATION)

    if "general_office_furniture_only" in segments and not focus:
        focus.extend([PRODUCT_FOCUS_FRAMES, PRODUCT_FOCUS_HOSUN])
    if not focus:
        focus.append(PRODUCT_FOCUS_FRAMES)
    return focus


def _score_product_fit(segments: list[str], blob: str) -> int:
    score = 0
    if "lift_system_signal" in segments:
        score += 15
    if _FRAME_KW.search(blob) or _COLUMNS_KW.search(blob) or _LEGS_KW.search(blob):
        score += 10
    if "project_based_furniture" in segments:
        score += 10
    if "oem_odm_fit" in segments or (_OEM_KW.search(blob) and (_COLUMNS_KW.search(blob) or _LEGS_KW.search(blob))):
        score += 10
    if _HEAVY_KW.search(blob) or "heavy_duty_fit" in segments:
        score += 8
    if "education_vertical" in segments and _EDUCATION_STRONG.search(blob):
        score += 8
    if "medical_vertical" in segments:
        score += 8
    if "general_office_furniture_only" in segments and score <= 4:
        score += 4
    return min(score, 40)


def _score_contact_readiness(inp: ProductFitInput) -> int:
    score = 0
    if _has_contact_method(inp):
        score += 8
    if _has_text(inp.contact_name):
        score += 5
    if _has_text(inp.contact_title):
        score += 4
    if _has_text(inp.contact_phone):
        score += 3
    return min(score, 20)


def _score_intent(inp: ProductFitInput, blob: str) -> int:
    score = 0
    if _QUOTE_SAMPLE_MEETING.search(blob):
        score += 8
    if _TIMELINE_KEYWORDS.search(blob) or re.search(r"\brfp\b", blob, re.I):
        score += 7
    if _QUANTITY_KEYWORDS.search(blob) or _PRODUCT_TYPE_KEYWORDS.search(blob):
        score += 5
    na = (inp.next_action or "").strip()
    if _has_text(na) and na != NO_NEXT_ACTION and len(na) > 12:
        score += 5
    elif _has_text(na) and na != NO_NEXT_ACTION:
        score += 2
    return min(score, 25)


def _score_operational(inp: ProductFitInput) -> int:
    score = 0
    if inp.completeness_score >= 80:
        score += 5
    elif inp.completeness_score >= 60:
        score += 3
    if inp.follow_up_date_set:
        score += 4
    if _has_enrichment(inp.enrichment_status):
        score += 3
    if inp.touch_count > 0:
        score += 3
    return min(score, 15)


def _opportunity_level(score: int) -> str:
    if score >= 80:
        return "high_opportunity"
    if score >= 60:
        return "promising"
    if score >= 40:
        return "needs_qualification"
    return "low_incomplete"


def _has_lifting_signal(segments: list[str], blob: str) -> bool:
    return (
        "lift_system_signal" in segments
        or "heavy_duty_fit" in segments
        or "oem_odm_fit" in segments
        or bool(_LIFT_EXPLICIT.search(blob) or _FRAME_KW.search(blob) or _COLUMNS_KW.search(blob))
    )


def _collect_missing_candidates(inp: ProductFitInput, blob: str, focus: list[str], segments: list[str]) -> list[str]:
    missing: list[str] = []
    is_medical = "medical_vertical" in segments or PRODUCT_FOCUS_MEDICAL in focus
    is_education = PRODUCT_FOCUS_EDUCATION in focus
    is_project = PRODUCT_FOCUS_PROJECT in focus or "project_based_furniture" in segments
    is_oem = PRODUCT_FOCUS_OEM in focus or "oem_odm_fit" in segments
    is_lifting = _has_lifting_signal(segments, blob)
    is_general = "general_office_furniture_only" in segments and not is_lifting

    if not _has_contact_method(inp):
        missing.append("contact_email_or_linkedin")
    if not focus:
        missing.append("product_type")
    elif not (_PRODUCT_TYPE_KEYWORDS.search(blob) or inp.lead_product_interest):
        missing.append("product_type")
    if not (_QUANTITY_KEYWORDS.search(blob) or _has_text(inp.estimated_value)):
        missing.append("quantity_or_volume")
    if not (_TIMELINE_KEYWORDS.search(blob) or _has_text(inp.expected_timeline)):
        missing.append("project_timeline")
    if not _DELIVERY_KEYWORDS.search(blob):
        missing.append("delivery_location")

    if is_lifting:
        if not _SIZE_KEYWORDS.search(blob):
            missing.append("frame_size_or_desktop_size")
        if not _LOAD_KEYWORDS.search(blob):
            missing.append("load_capacity_requirement")
        if not _COLOR_KEYWORDS.search(blob):
            missing.append("color_or_finish")
        if _CONTROL_KW.search(blob) is None and "control" in blob:
            missing.append("control_system_requirement")
        if _LEGS_KW.search(blob) or _COLUMNS_KW.search(blob):
            missing.append("component_type")

    if is_project:
        if not re.search(r"\binstall|packag", blob, re.I):
            missing.append("installation_or_packaging_need")

    if is_education:
        if not re.search(r"\b(classroom|campus|training|school)\b", blob, re.I):
            missing.append("classroom_or_campus_use_case")
        if not (_TIMELINE_KEYWORDS.search(blob) or _has_text(inp.expected_timeline)):
            missing.append("rfp_or_procurement_timeline")
        if not _QUANTITY_KEYWORDS.search(blob):
            missing.append("volume_estimate")

    if is_medical:
        if not re.search(r"\b(clinical|lab|healthcare|medical|nurse)\b", blob, re.I):
            missing.append("workstation_use_case")
        if is_lifting and not _LOAD_KEYWORDS.search(blob):
            missing.append("stability_or_load_requirement")

    if is_oem:
        if not re.search(r"\b(private label|component|custom|odm|oem)\b", blob, re.I):
            missing.append("component_category")
        if not re.search(r"\b(custom|private label|development)\b", blob, re.I):
            missing.append("customization_requirement")

    if _SAMPLE_KEYWORDS.search(blob) and not _QUANTITY_KEYWORDS.search(blob):
        missing.append("sample_quantity")
    if _QUOTE_KEYWORDS.search(blob) and not re.search(r"\bbudget\b", blob, re.I):
        missing.append("target_price_or_budget")
    if not _has_text(inp.contact_title):
        missing.append("decision_maker_role")

    if is_medical and not _CERT_KEYWORDS.search(blob):
        missing.append("certification_requirement")

    seen: set[str] = set()
    ordered: list[str] = []
    for key in _MISSING_PRIORITY:
        if key in missing and key not in seen:
            seen.add(key)
            ordered.append(key)
    for key in missing:
        if key not in seen:
            ordered.append(key)
    return ordered


def _cap_missing(missing: list[str], quote_readiness: str) -> list[str]:
    if quote_readiness == "not_ready":
        limit = 4
    elif quote_readiness == "almost_ready":
        limit = 6
    else:
        limit = 3
    return missing[:limit]


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
    return pool[:4]


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
    segments = _refine_segments(inp.segments, blob, inp.company_type, inp.industry)
    focus = _recommended_product_focus(segments, blob, inp.company_type, inp.industry)
    project_type = _infer_project_type(segments)

    opp_score = (
        _score_product_fit(segments, blob)
        + _score_contact_readiness(inp)
        + _score_intent(inp, blob)
        + _score_operational(inp)
    )
    opp_score = min(100, max(0, opp_score))

    missing_raw = _collect_missing_candidates(inp, blob, focus, segments)
    quote_readiness = _quote_readiness(inp, focus, project_type, blob, missing_raw)
    missing = _cap_missing(missing_raw, quote_readiness)
    if quote_readiness == "ready" and len(missing) > 3:
        quote_readiness = "almost_ready"
        missing = _cap_missing(missing_raw, quote_readiness)

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
