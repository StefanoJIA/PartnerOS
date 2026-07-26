"""Partner-neutral product capability vocabulary for lifting systems and project furniture."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

LIFTING_CAPABILITY_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("frame_column_type", "Frame / column type", "frame | column | leg | complete_system"),
    ("stage_count", "Stage count", "integer"),
    ("stroke_range_mm", "Stroke / height range (mm)", "range"),
    ("width_range_mm", "Width range (mm)", "range"),
    ("load_capacity_kg", "Load capacity (kg)", "number"),
    ("speed_mm_s", "Speed (mm/s)", "number"),
    ("noise_db", "Noise level (dB)", "number"),
    ("stability_rating", "Stability rating", "text"),
    ("duty_cycle", "Duty cycle", "text"),
    ("anti_collision", "Anti-collision", "boolean"),
    ("controller_type", "Controller", "text"),
    ("finish_options", "Finish / color options", "list"),
    ("packaging", "Packaging", "text"),
    ("moq", "MOQ", "integer"),
    ("lead_time_days", "Lead time (days)", "integer"),
    ("certifications", "Certifications", "list"),
    ("warranty", "Warranty", "text"),
    ("custom_engineering", "Custom engineering capability", "boolean"),
)

PROJECT_REQUIREMENT_SIGNALS: tuple[tuple[str, str, str], ...] = (
    ("heavy_load", "Heavy load / industrial", "load_capacity_kg"),
    ("extra_wide_multi_leg", "Extra-wide / multi-leg", "width_range_mm"),
    ("medical_industrial", "Medical / industrial use", "certifications"),
    ("quiet_operation", "Quiet operation", "noise_db"),
    ("high_stability", "High stability", "stability_rating"),
    ("custom_mount_holes", "Custom mounting / install holes", "custom_engineering"),
    ("sample_validation", "Sample validation required", "moq"),
    ("certification_required", "Certification required", "certifications"),
    ("lead_time_sensitive", "Lead time sensitive", "lead_time_days"),
    ("target_cost_pressure", "Target cost pressure", "moq"),
)


def normalize_capability(attrs: dict[str, Any] | None) -> dict[str, Any]:
    raw = attrs if isinstance(attrs, dict) else {}
    out: dict[str, Any] = {}
    for key, _label, _kind in LIFTING_CAPABILITY_FIELDS:
        if key in raw and raw[key] not in (None, "", []):
            out[key] = raw[key]
    return out


def capability_coverage(attrs: dict[str, Any] | None) -> dict[str, Any]:
    normalized = normalize_capability(attrs)
    total = len(LIFTING_CAPABILITY_FIELDS)
    filled = len(normalized)
    missing = [key for key, label, _ in LIFTING_CAPABILITY_FIELDS if key not in normalized]
    return {
        "filled_count": filled,
        "total_fields": total,
        "coverage_pct": round(filled * 100 / total, 1) if total else 0,
        "missing_fields": missing,
        "missing_labels": [label for key, label, _ in LIFTING_CAPABILITY_FIELDS if key in missing],
    }


def evaluate_project_requirement_fit(
    requirement_key: str,
    attrs: dict[str, Any] | None,
    *,
    evidence: str | None = None,
) -> dict[str, Any]:
    """Explainable fit for a single project requirement signal."""
    normalized = normalize_capability(attrs)
    signal = next((s for s in PROJECT_REQUIREMENT_SIGNALS if s[0] == requirement_key), None)
    if not signal:
        return {
            "requirement_key": requirement_key,
            "fit_score": 0,
            "status": "unknown_requirement",
            "missing_conditions": [],
            "risks": ["Unknown requirement key"],
            "recommended_next": "Clarify requirement with customer.",
            "evidence_source": evidence or "",
            "confidence": "low",
        }

    _key, label, capability_field = signal
    value = normalized.get(capability_field)
    missing: list[str] = []
    risks: list[str] = []
    score = 40

    if value in (None, "", [], False):
        missing.append(capability_field)
        risks.append(f"Missing {capability_field} for {label}")
        score = 25
    else:
        score = 70
        if requirement_key == "heavy_load":
            try:
                load = Decimal(str(value))
                score = 90 if load >= Decimal("120") else 55
                if load < Decimal("80"):
                    risks.append("Declared load may be below heavy-duty threshold")
            except Exception:
                score = 50
                risks.append("Load capacity not numeric")
        elif requirement_key == "quiet_operation":
            try:
                noise = Decimal(str(value))
                score = 88 if noise <= Decimal("50") else 60
            except Exception:
                score = 50
        elif requirement_key == "sample_validation":
            score = 75
        else:
            score = 78

    status = "strong_fit" if score >= 80 else "partial_fit" if score >= 55 else "gap"
    return {
        "requirement_key": requirement_key,
        "requirement_label": label,
        "fit_score": score,
        "status": status,
        "missing_conditions": missing,
        "risks": risks,
        "recommended_next": (
            "Proceed to interval quote with engineering review."
            if status == "strong_fit"
            else "Collect missing capability data or schedule sample/engineering review."
        ),
        "evidence_source": evidence or "",
        "confidence": "high" if value and score >= 70 else "medium" if value else "low",
    }
