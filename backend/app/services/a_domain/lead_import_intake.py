"""CSV lead intake preview helpers (D5.2.4 — no DB writes)."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

from app.services.a_domain.intelligence_score import infer_market_fit_segments

REQUIRED_HEADERS = {
    "company_name",
    "website",
    "company_type",
    "industry",
    "city",
    "state",
    "country",
    "contact_name",
    "contact_title",
    "contact_email",
    "contact_phone",
    "linkedin_url",
    "source",
    "notes",
    "initial_interest",
    "priority",
    "next_action",
}


@dataclass
class LeadRowPreview:
    company_name: str
    likely_segments: list[str]
    priority_hint: str
    missing_fields: list[str]
    recommended_next_action: str
    status: str  # OK | WARN
    duplicate_hint: str | None = None
    raw: dict[str, str] = field(default_factory=dict)


def parse_csv_text(csv_text: str) -> tuple[list[str], list[dict[str, str]]]:
    """Parse CSV from in-memory text (UTF-8 with optional BOM)."""
    if not (csv_text or "").strip():
        raise ValueError("CSV text is empty")
    f = io.StringIO(csv_text.lstrip("\ufeff"))
    reader = csv.DictReader(f)
    if not reader.fieldnames:
        raise ValueError("CSV has no header row")
    headers = [h.strip() for h in reader.fieldnames if h]
    rows: list[dict[str, str]] = []
    for row in reader:
        cleaned = {k.strip(): (v or "").strip() for k, v in row.items() if k}
        if any(cleaned.values()):
            rows.append(cleaned)
    return headers, rows


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    return parse_csv_text(path.read_text(encoding="utf-8-sig"))


def validate_headers(headers: list[str]) -> list[str]:
    header_set = set(headers)
    missing = sorted(REQUIRED_HEADERS - header_set)
    return missing


def _text_blob(row: dict[str, str]) -> str:
    parts = [
        row.get("notes", ""),
        row.get("industry", ""),
        row.get("company_type", ""),
        row.get("initial_interest", ""),
        row.get("website", ""),
    ]
    return " \n ".join(p for p in parts if p).lower()


def first_semicolon_token(value: str) -> str:
    if not value:
        return ""
    return value.split(";")[0].strip()


def first_email(value: str) -> str:
    if not value:
        return ""
    for part in value.replace(",", ";").split(";"):
        p = part.strip()
        if "@" in p:
            return p
    return ""


def first_phone(value: str) -> str:
    if not value:
        return ""
    return first_semicolon_token(value.replace(",", ";"))


def _missing_fields(row: dict[str, str]) -> list[str]:
    missing: list[str] = []
    if not row.get("company_name"):
        missing.append("company_name")
    if not row.get("company_type") and not row.get("industry"):
        missing.append("company_type or industry")
    if not row.get("website") and not row.get("notes"):
        missing.append("website or notes")
    if not first_semicolon_token(row.get("contact_name", "")):
        missing.append("contact_name")
    if not first_email(row.get("contact_email", "")):
        missing.append("contact_email")
    return missing


def _priority_hint(row: dict[str, str], segments: list[str]) -> str:
    pr = (row.get("priority") or "").strip().lower()
    if pr in ("high", "medium", "low"):
        return pr
    if "lift_system_signal" in segments or "medical_vertical" in segments:
        return "high"
    if segments:
        return "medium"
    return "low"


def recommend_next_action(row: dict[str, str], segments: list[str], missing: list[str]) -> str:
    if missing and ("website or notes" in missing or "company_type or industry" in missing):
        return "Enrich company profile before outreach"
    if row.get("next_action"):
        return row["next_action"]
    if "contact_name" in missing or "contact_email" in missing:
        if "contact research" in (row.get("notes") or "").lower() or not first_semicolon_token(
            row.get("contact_name", "")
        ):
            return "Research contact before outreach"
    if "lift_system_signal" in segments or "oem_odm_fit" in segments:
        return "Send catalog and ask about adjustable desk frame / lifting column needs"
    if "project_based_furniture" in segments:
        return "Ask whether they handle project-based furniture procurement and FF&E lists"
    if "education_vertical" in segments:
        return "Share JOOBOO education line overview and ask about project timeline"
    if "medical_vertical" in segments:
        return "Offer medical / lab workspace intro — confirm compliance documentation needs"
    if "oem_odm_fit" in segments:
        return "Schedule short technical call on OEM/ODM lifting components"
    if "general_office_furniture_only" in segments:
        return "Enrich company before outreach — confirm adjustable frame interest"
    return "Review lead in Lead Intelligence and set next action"


def preview_row(row: dict[str, str], *, duplicate_names: set[str] | None = None) -> LeadRowPreview:
    name = row.get("company_name", "").strip() or "(unnamed)"
    missing = _missing_fields(row)
    segments = infer_market_fit_segments(_text_blob(row))
    if not segments and row.get("company_type"):
        ct = row["company_type"].lower()
        if "education" in ct:
            segments = ["education_vertical"]
        elif "healthcare" in ct or "medical" in ct:
            segments = ["medical_vertical"]
        elif "dealer" in ct or "office" in ct:
            segments = ["general_office_furniture_only"]

    priority = _priority_hint(row, segments)
    next_action = recommend_next_action(row, segments, missing)
    status = "WARN" if missing else "OK"
    dup = None
    if duplicate_names and name in duplicate_names:
        dup = "possible duplicate — company name already exists in CRM"

    return LeadRowPreview(
        company_name=name,
        likely_segments=segments,
        priority_hint=priority,
        missing_fields=missing,
        recommended_next_action=next_action,
        status=status,
        duplicate_hint=dup,
        raw=row,
    )


def split_contact_name(full: str) -> tuple[str, str]:
    parts = full.strip().split(None, 1)
    if not parts:
        return "Contact", "Unknown"
    if len(parts) == 1:
        return parts[0], "—"
    return parts[0], parts[1]
