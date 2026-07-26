"""Supplier discovery intake, dedup, and qualification helpers."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models import ManufacturingPartner, SupplierDiscoveryRecord
from app.models.enums import PartnerLifecycle, SupplierDiscoveryStatus

QUALIFICATION_DIMENSIONS: tuple[str, ...] = (
    "product_capability_completeness",
    "certs_compliance",
    "sample_results",
    "moq_lead_time",
    "quote_completeness",
    "export_experience",
    "communication_response",
    "quality_risk",
    "production_logistics_visibility",
    "commercial_terms",
    "data_trustworthiness",
)

LIFTING_SAMPLE_TEMPLATE_ITEMS: tuple[str, ...] = (
    "load_test",
    "noise_test",
    "speed_test",
    "stroke_test",
    "lateral_stability",
    "front_stability",
    "multi_leg_sync",
    "controller_test",
    "anti_collision",
    "powder_coat",
    "assembly",
    "packaging",
    "continuous_run",
)

EDUCATION_SAMPLE_TEMPLATE_ITEMS: tuple[str, ...] = (
    "structural_strength",
    "surface_finish",
    "ergonomics",
    "fire_rating",
    "assembly_instructions",
    "packaging",
)

SAMPLE_TEMPLATES: dict[str, tuple[str, ...]] = {
    "lifting": LIFTING_SAMPLE_TEMPLATE_ITEMS,
    "education": EDUCATION_SAMPLE_TEMPLATE_ITEMS,
    "generic": ("visual_inspection", "functional_test", "packaging"),
}


def normalize_domain(url: str | None) -> str | None:
    if not url:
        return None
    raw = url.strip().lower()
    if not raw:
        return None
    if "://" not in raw:
        raw = f"https://{raw}"
    try:
        host = urlparse(raw).netloc or urlparse(raw).path
    except Exception:
        return None
    host = host.lower().removeprefix("www.")
    return host or None


def build_dedup_fingerprint(
    *,
    company_name: str,
    domain_key: str | None = None,
    factory_address: str | None = None,
    contact_email: str | None = None,
) -> str:
    parts = [
        company_name.strip().lower(),
        (domain_key or "").strip().lower(),
        (factory_address or "").strip().lower(),
        (contact_email or "").strip().lower(),
    ]
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def find_duplicate_records(db: Session, *, fingerprint: str, exclude_id: UUID | None = None) -> list[SupplierDiscoveryRecord]:
    query = db.query(SupplierDiscoveryRecord).filter(SupplierDiscoveryRecord.dedup_fingerprint == fingerprint)
    if exclude_id:
        query = query.filter(SupplierDiscoveryRecord.id != exclude_id)
    return query.all()


def init_qualification_json() -> dict[str, Any]:
    return {
        "dimensions": {
            key: {"status": "UNKNOWN", "evidence": None, "reviewer_id": None, "reviewed_at": None, "notes": None}
            for key in QUALIFICATION_DIMENSIONS
        }
    }


def update_qualification_dimension(
    record: SupplierDiscoveryRecord,
    *,
    dimension_key: str,
    status: str,
    evidence: str | None,
    reviewer_id: UUID,
    notes: str | None = None,
) -> dict[str, Any]:
    if dimension_key not in QUALIFICATION_DIMENSIONS:
        raise ValueError(f"Unknown qualification dimension: {dimension_key}")
    qual = record.qualification_json or init_qualification_json()
    if "dimensions" not in qual:
        qual["dimensions"] = init_qualification_json()["dimensions"]
    qual["dimensions"][dimension_key] = {
        "status": status,
        "evidence": evidence,
        "reviewer_id": str(reviewer_id),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
    }
    record.qualification_json = qual
    return qual


def parse_csv_import(content: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(content))
    rows: list[dict[str, Any]] = []
    for row in reader:
        company = (row.get("company_name") or row.get("Company") or "").strip()
        if not company:
            continue
        contacts = []
        email = (row.get("contact_email") or row.get("email") or "").strip()
        phone = (row.get("contact_phone") or row.get("phone") or "").strip()
        name = (row.get("contact_name") or row.get("contact") or "").strip()
        if email or phone or name:
            contacts.append({"name": name or None, "email": email or None, "phone": phone or None})
        categories = [c.strip() for c in re.split(r"[;,|]", row.get("categories") or "") if c.strip()]
        capabilities = [c.strip() for c in re.split(r"[;,|]", row.get("capabilities") or "") if c.strip()]
        export_markets = [c.strip() for c in re.split(r"[;,|]", row.get("export_markets") or "") if c.strip()]
        source_url = (row.get("source_url") or row.get("url") or "").strip() or None
        rows.append(
            {
                "company_name": company,
                "brand_name": (row.get("brand_name") or row.get("brand") or "").strip() or None,
                "country": (row.get("country") or "").strip() or None,
                "factory_address": (row.get("factory_address") or row.get("address") or "").strip() or None,
                "source_url": source_url,
                "domain_key": normalize_domain(source_url),
                "categories": categories or None,
                "capabilities": capabilities or None,
                "export_markets": export_markets or None,
                "contacts_json": contacts or None,
                "data_source": (row.get("data_source") or "csv_import").strip(),
                "pricing_doc_status": (row.get("pricing_doc_status") or "unknown").strip(),
                "data_rights_status": (row.get("data_rights_status") or "pending_review").strip(),
                "source_review_status": (row.get("source_review_status") or "pending").strip(),
                "usage_restrictions": (row.get("usage_restrictions") or "").strip() or None,
                "moq_notes": (row.get("moq_notes") or row.get("moq") or "").strip() or None,
                "lead_time_notes": (row.get("lead_time_notes") or row.get("lead_time") or "").strip() or None,
            }
        )
    return rows


def import_discovery_rows(
    db: Session,
    rows: list[dict[str, Any]],
    *,
    actor_id: UUID,
    skip_duplicates: bool = True,
) -> tuple[list[SupplierDiscoveryRecord], list[dict[str, str]]]:
    created: list[SupplierDiscoveryRecord] = []
    skipped: list[dict[str, str]] = []
    for payload in rows:
        contact_email = None
        if payload.get("contacts_json"):
            contact_email = payload["contacts_json"][0].get("email")
        fingerprint = build_dedup_fingerprint(
            company_name=payload["company_name"],
            domain_key=payload.get("domain_key"),
            factory_address=payload.get("factory_address"),
            contact_email=contact_email,
        )
        payload["dedup_fingerprint"] = fingerprint
        if skip_duplicates and find_duplicate_records(db, fingerprint=fingerprint):
            skipped.append({"company_name": payload["company_name"], "reason": "duplicate_fingerprint"})
            continue
        row = SupplierDiscoveryRecord(
            **payload,
            status=SupplierDiscoveryStatus.discovered.value,
            qualification_json=init_qualification_json(),
            owner_user_id=actor_id,
            created_by_id=actor_id,
            updated_by_id=actor_id,
            retrieved_at=datetime.now(timezone.utc),
        )
        db.add(row)
        created.append(row)
    db.flush()
    return created, skipped


def activate_discovery_as_partner(
    db: Session,
    record: SupplierDiscoveryRecord,
    *,
    actor_id: UUID,
) -> ManufacturingPartner:
    if record.status != SupplierDiscoveryStatus.qualified.value:
        raise ValueError("Only qualified suppliers can be activated as partners")
    if record.partner_id:
        partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == record.partner_id).first()
        if partner:
            partner.lifecycle_status = PartnerLifecycle.active.value
            partner.is_active = True
            record.status = SupplierDiscoveryStatus.active.value
            record.updated_by_id = actor_id
            return partner
    partner = ManufacturingPartner(
        partner_name=record.company_name,
        brand_name=record.brand_name,
        partner_type="Other",
        country=record.country,
        address=record.factory_address,
        main_product_categories=", ".join(record.categories or []),
        manufacturing_capabilities=", ".join(record.capabilities or []),
        export_experience=", ".join(record.export_markets or []),
        moq_policy=record.moq_notes,
        sample_policy=record.sample_policy,
        lead_time=record.lead_time_notes,
        certifications=", ".join(record.certifications or []) if isinstance(record.certifications, list) else None,
        lifecycle_status=PartnerLifecycle.active.value,
        is_active=True,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(partner)
    db.flush()
    record.partner_id = partner.id
    record.status = SupplierDiscoveryStatus.active.value
    record.updated_by_id = actor_id
    return partner
