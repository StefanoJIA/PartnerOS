"""D5.19 — quote input contract for Phase 2 handoff boundary (read-only, no quote creation)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.services.a_domain.pre_quote_prep import PRE_QUOTE_SAFETY
from app.services.a_domain.quote_handoff import FORBIDDEN_HANDOFF_PHRASES, ROUTE_LABELS, SCOPE_LABELS

READINESS_LEVELS = frozenset(
    {
        "ready_for_phase2_quote_draft",
        "needs_more_customer_info",
        "not_quote_ready",
    }
)

_KNOWN_FIELD_KEYS = (
    "quantity_or_volume",
    "product_type",
    "frame_size_or_desktop_size",
    "load_capacity_requirement",
    "color_or_finish",
    "delivery_location",
    "project_timeline",
    "certification_requirement",
    "sample_quantity",
    "oem_customization_requirement",
    "component_category",
)

_QTY_EXPLICIT = re.compile(
    r"\b(\d{1,6})\s*(units|unit|frames|frame|desks|desk|pcs|pieces|qty|moq)\b",
    re.I,
)
_SIZE_EXPLICIT = re.compile(
    r"\b(\d{2,4}\s*x\s*\d{2,4}|\d+\s*mm|\d+\s*cm|\d+\s*inch|\d+\s*in\b|stroke\s*\d+)",
    re.I,
)
_LOAD_EXPLICIT = re.compile(r"\b(\d{2,4}\s*(kg|lb|lbs|pounds)|load\s*capacity\s*[\d]+)", re.I)
_COLOR_EXPLICIT = re.compile(r"\b(black|white|gray|grey|silver|powder\s*coat\w*|ral\s*\d+)\b", re.I)
_DELIVERY_EXPLICIT = re.compile(
    r"\b(ship\s*to|delivery\s*(to|location|address)|deliver\s*to)\s+([A-Za-z][\w\s,]{2,40})",
    re.I,
)
_CERT_EXPLICIT = re.compile(r"\b(ul\b|ce\b|bifma|iso\s*\d+|certification\s*required)\b", re.I)
_PRODUCT_TYPE_EXPLICIT = re.compile(
    r"\b(adjustable desk frame|lifting column|desk leg|lifting system|oem|odm|component)\b",
    re.I,
)
_OEM_CUSTOM = re.compile(r"\b(private label|custom development|customization|odm|oem)\b", re.I)
_COMPONENT = re.compile(r"\b(lifting column|desk leg|control system|desk frame|actuator)\b", re.I)


@dataclass
class QuoteInputContractInput:
    lead_id: str = ""
    company_name: str = ""
    contact_name: str | None = None
    has_contact_method: bool = False
    handoff: dict[str, Any] = field(default_factory=dict)
    product_fit: dict[str, Any] = field(default_factory=dict)
    notes_blob: str = ""
    lead_product_interest: str | None = None
    expected_timeline: str | None = None
    estimated_value: str | None = None


def _extract_known_requirements(inp: QuoteInputContractInput) -> dict[str, str | None]:
    blob = inp.notes_blob
    known: dict[str, str | None] = {k: None for k in _KNOWN_FIELD_KEYS}

    if inp.expected_timeline and inp.expected_timeline.strip():
        known["project_timeline"] = inp.expected_timeline.strip()

    if inp.estimated_value and inp.estimated_value.strip():
        val = inp.estimated_value.strip()
        if re.search(r"\d", val):
            known["quantity_or_volume"] = val

    m = _QTY_EXPLICIT.search(blob)
    if m:
        known["quantity_or_volume"] = m.group(0).strip()

    if inp.lead_product_interest and inp.lead_product_interest.strip():
        interest = inp.lead_product_interest.strip()
        if len(interest) <= 120:
            known["product_type"] = interest
    elif _PRODUCT_TYPE_EXPLICIT.search(blob):
        known["product_type"] = _PRODUCT_TYPE_EXPLICIT.search(blob).group(0).strip()

    m = _SIZE_EXPLICIT.search(blob)
    if m:
        known["frame_size_or_desktop_size"] = m.group(0).strip()

    m = _LOAD_EXPLICIT.search(blob)
    if m:
        known["load_capacity_requirement"] = m.group(0).strip()

    m = _COLOR_EXPLICIT.search(blob)
    if m:
        known["color_or_finish"] = m.group(0).strip()

    m = _DELIVERY_EXPLICIT.search(blob)
    if m:
        known["delivery_location"] = m.group(3).strip()[:80]

    m = _CERT_EXPLICIT.search(blob)
    if m:
        known["certification_requirement"] = m.group(0).strip()

    if re.search(r"\bsample\b", blob, re.I) and _QTY_EXPLICIT.search(blob):
        known["sample_quantity"] = _QTY_EXPLICIT.search(blob).group(0).strip()

    if _OEM_CUSTOM.search(blob):
        known["oem_customization_requirement"] = _OEM_CUSTOM.search(blob).group(0).strip()

    if _COMPONENT.search(blob):
        known["component_category"] = _COMPONENT.search(blob).group(0).strip()

    return known


def _quote_module_readiness(
    handoff_status: str,
    scope: list[str],
    has_contact: bool,
    missing: list[str],
    known: dict[str, str | None],
    product_focus: list[str],
) -> str:
    missing_count = len(missing)
    product_type_clear = bool(
        known.get("product_type")
        or product_focus
        or any(known.get(k) for k in ("component_category",))
    )

    if (
        handoff_status == "ready_for_manual_quote_prep"
        and scope
        and has_contact
        and missing_count <= 2
        and product_type_clear
    ):
        return "ready_for_phase2_quote_draft"

    if (
        handoff_status == "needs_customer_clarification"
        and product_focus
        and 3 <= missing_count <= 6
    ):
        return "needs_more_customer_info"
    if handoff_status == "needs_customer_clarification" and product_focus:
        return "needs_more_customer_info"

    if handoff_status == "ready_for_manual_quote_prep" and product_focus and missing_count <= 3:
        return "needs_more_customer_info"

    return "not_quote_ready"


def _handoff_summary_text(
    inp: QuoteInputContractInput,
    readiness: str,
    routes: list[str],
    scope: list[str],
    known_ctx: list[str],
    missing: list[str],
    questions: list[str],
    supplier: list[str],
) -> str:
    route_text = "; ".join(ROUTE_LABELS.get(r, r) for r in routes) or "—"
    scope_text = "; ".join(SCOPE_LABELS.get(s, s.replace("_", " ")) for s in scope) or "—"
    readiness_label = readiness.replace("_", " ").title()

    lines = [
        f"Quote Input Contract — {inp.company_name}",
        "",
        f"Quote module readiness: {readiness_label}",
        f"Recommended route: {route_text}",
        f"Product scope: {scope_text}",
        "",
        "Known:",
    ]
    for ctx in known_ctx[:6]:
        lines.append(f"- {ctx}")
    lines.extend(["", "Missing before formal quote:"])
    if missing:
        for m in missing:
            lines.append(f"- {m.replace('_', ' ').title()}")
    else:
        lines.append("- None flagged — still confirm latest specs with customer.")
    lines.extend(["", "Recommended customer questions:"])
    for i, q in enumerate(questions[:5], 1):
        lines.append(f"{i}. {q}")
    lines.extend(["", "Supplier preparation:"])
    for n in supplier[:5]:
        lines.append(f"- {n}")
    lines.extend(
        [
            "",
            "Safety:",
            "No quote has been created. No pricing, inventory, certification, or lead-time commitment is included.",
        ]
    )
    return "\n".join(lines)


def build_quote_input_contract(inp: QuoteInputContractInput) -> dict[str, Any]:
    """Build Phase 2 quote input contract from handoff + product fit context."""
    handoff = inp.handoff or {}
    fit = inp.product_fit or {}

    routes = handoff.get("recommended_partner_route") or []
    scope = handoff.get("recommended_product_scope") or []
    missing_raw = handoff.get("missing_customer_info") or []
    missing_labels = [m.replace("_", " ").title() for m in missing_raw]
    questions = handoff.get("customer_clarification_questions") or []
    supplier = handoff.get("supplier_preparation_notes") or []
    handoff_status = handoff.get("handoff_status", "not_ready")
    known_req = _extract_known_requirements(inp)

    readiness = _quote_module_readiness(
        handoff_status,
        scope,
        inp.has_contact_method,
        missing_raw,
        known_req,
        fit.get("recommended_product_focus") or [],
    )

    known_context = handoff.get("known_context") or []
    if inp.contact_name:
        known_context = [f"Primary contact: {inp.contact_name}.", *known_context]

    quote_input_fields = {
        "customer": {
            "company_name": inp.company_name,
            "contact_name": inp.contact_name,
            "contact_method_available": inp.has_contact_method,
        },
        "product_intent": {
            "product_focus": fit.get("recommended_product_focus") or [],
            "project_type": fit.get("project_type", "unknown"),
            "sample_readiness": handoff.get("sample_readiness", fit.get("sample_readiness", "not_ready")),
            "quote_readiness": handoff.get("quote_readiness", fit.get("quote_readiness", "not_ready")),
        },
        "known_requirements": known_req,
        "missing_requirements": missing_raw,
        "recommended_questions": questions,
        "supplier_preparation_notes": supplier,
    }

    summary = _handoff_summary_text(
        inp, readiness, routes, scope, known_context, missing_labels, questions, supplier
    )

    payload = {
        "lead_id": inp.lead_id,
        "company_name": inp.company_name,
        "handoff_status": handoff_status,
        "quote_module_readiness": readiness,
        "recommended_partner_route": routes,
        "recommended_product_scope": scope,
        "quote_input_fields": quote_input_fields,
        "safety": dict(PRE_QUOTE_SAFETY),
    }
    copyable_json = json.dumps(payload, indent=2, ensure_ascii=False)

    warnings = [
        "Quote input contract is a Phase 2 handoff boundary only — no quote record is created.",
        "No pricing, inventory, certification, or lead-time commitments are generated.",
    ]
    if readiness == "not_quote_ready":
        warnings.append("Lead is not ready for formal quote module intake — complete discovery first.")

    return {
        **payload,
        "copyable_json": copyable_json,
        "copyable_handoff_summary": summary,
        "warnings": warnings,
    }


def assert_no_forbidden_contract_phrases(text: str) -> None:
    lower = text.lower()
    for phrase in FORBIDDEN_HANDOFF_PHRASES:
        if phrase in lower:
            raise ValueError(f"Forbidden phrase in contract: {phrase}")
