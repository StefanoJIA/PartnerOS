"""Customer project request intake, fit matching, and operator workflow."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models import Company, Contact, CustomerProjectRequest, ManufacturingPartner, ProductCatalog
from app.models.enums import CustomerProjectRequestStatus
from app.schemas.customer_project_request_domain import ProjectRequirementFields, SiteProjectRequestIn
from app.services.activity import log_activity
from app.services.product_capability_schema import (
    LIFTING_CAPABILITY_FIELDS,
    capability_coverage,
    normalize_capability,
)

_RATE_WINDOW_SECONDS = 300
_RATE_MAX_PER_WINDOW = 20
_rate_buckets: dict[str, list[float]] = defaultdict(list)

LIFTING_MATCH_DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    ("heavy_load", "300kg / 660lb heavy load", "load_capacity_kg"),
    ("quiet_operation", "Noise / vibration target", "noise_db"),
    ("high_stability", "Lateral / front-back stability", "stability_rating"),
    ("extra_wide_multi_leg", "Ultra-wide / multi-leg / conference", "width_range_mm"),
    ("medical_industrial", "Medical / industrial integration", "certifications"),
    ("custom_mount_holes", "Mounting / install holes", "custom_engineering"),
    ("controller", "Controller requirements", "controller_type"),
    ("anti_collision", "Anti-collision", "anti_collision"),
    ("finish_color", "Powder coat / color", "finish_options"),
    ("certification", "Certifications", "certifications"),
    ("sample_validation", "Sample validation", "moq"),
    ("lead_time", "Lead time", "lead_time_days"),
    ("warranty", "Warranty", "warranty"),
    ("stroke_range", "Stroke / height range", "stroke_range_mm"),
    ("speed_duty", "Speed / duty cycle", "speed_mm_s"),
)

REQUIREMENT_COMPLETENESS_FIELDS = (
    "customer_name",
    "customer_email",
    "product_interest",
    "quantity_min",
    "delivery_region",
    "project_scenario",
    "load_capacity_kg",
    "width_range",
    "noise_db_target",
    "stability_requirement",
    "color_finish",
    "certifications",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _next_reference() -> str:
    return f"CPR-{uuid.uuid4().hex[:8].upper()}"


def _hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()[:32]


def check_rate_limit(client_key: str) -> bool:
    now = _now().timestamp()
    bucket = _rate_buckets[client_key]
    _rate_buckets[client_key] = [t for t in bucket if now - t < _RATE_WINDOW_SECONDS]
    if len(_rate_buckets[client_key]) >= _RATE_MAX_PER_WINDOW:
        return False
    _rate_buckets[client_key].append(now)
    return True


def requirements_to_json(req: ProjectRequirementFields | None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if req:
        payload.update(req.model_dump(exclude_none=True))
    if extra:
        payload.update({k: v for k, v in extra.items() if v is not None})
    return payload


def _parse_quantity_from_items(items: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    qtys = []
    for item in items:
        q = item.get("quantity") or item.get("qty")
        if q is not None:
            try:
                qtys.append(int(q))
            except (TypeError, ValueError):
                pass
    if not qtys:
        return None, None
    return min(qtys), max(qtys)


def _parse_product_interest(items: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    names: list[str] = []
    skus: list[str] = []
    for item in items:
        if item.get("product_name"):
            names.append(str(item["product_name"]))
        if item.get("sku"):
            skus.append(str(item["sku"]))
        if item.get("name"):
            names.append(str(item["name"]))
    interest = "; ".join(names[:5]) if names else None
    sku = skus[0] if skus else None
    return interest, sku


def _parse_shipping_region(shipping_address: str | None) -> str | None:
    if not shipping_address:
        return None
    try:
        data = json.loads(shipping_address)
        if isinstance(data, dict):
            parts = [data.get("city"), data.get("state"), data.get("country") or data.get("country_name")]
            return ", ".join(p for p in parts if p)
    except json.JSONDecodeError:
        pass
    return shipping_address[:255]


def compute_completeness(row: CustomerProjectRequest) -> dict[str, Any]:
    req = row.requirements_json or {}
    filled = 0
    missing: list[str] = []
    checks = {
        "customer_name": row.customer_name,
        "customer_email": row.customer_email,
        "product_interest": row.product_interest,
        "quantity_min": row.quantity_min,
        "delivery_region": row.delivery_region,
        "project_scenario": row.project_scenario or row.operator_notes,
        "load_capacity_kg": req.get("load_capacity_kg") or req.get("load_capacity_lb"),
        "width_range": req.get("width_mm") or req.get("leg_count") or req.get("desk_configuration"),
        "noise_db_target": req.get("noise_db_target"),
        "stability_requirement": req.get("stability_requirement"),
        "color_finish": req.get("color_finish") or req.get("powder_coat"),
        "certifications": req.get("certifications"),
    }
    for key, val in checks.items():
        if val not in (None, "", [], {}):
            filled += 1
        else:
            missing.append(key)
    total = len(checks)
    return {
        "filled_count": filled,
        "total_fields": total,
        "completeness_pct": round(filled * 100 / total, 1) if total else 0,
        "missing_fields": missing,
    }


def _match_status_for_dimension(
    dimension_key: str,
    requirement_value: Any,
    catalog_attrs: dict[str, Any],
    *,
    partner_pending: bool,
) -> dict[str, Any]:
    if partner_pending:
        return {
            "match_status": "UNKNOWN",
            "evidence_source": "partner_catalog_pending",
            "gap_notes": "Partner catalog is pending — no production capability data.",
            "engineering_review_required": True,
            "suggested_validation": "Obtain approved partner catalog before customer-facing claims.",
            "confidence": "low",
        }

    cap = normalize_capability(catalog_attrs)
    dim = next((d for d in LIFTING_MATCH_DIMENSIONS if d[0] == dimension_key), None)
    if not dim:
        return {
            "match_status": "UNKNOWN",
            "evidence_source": "schema",
            "gap_notes": "Unknown dimension",
            "engineering_review_required": False,
            "confidence": "low",
        }

    _key, label, cap_field = dim
    cap_val = cap.get(cap_field)

    if requirement_value in (None, "", [], False):
        return {
            "match_status": "UNKNOWN",
            "evidence_source": "customer_request",
            "gap_notes": "Customer did not specify this requirement.",
            "engineering_review_required": False,
            "suggested_validation": "Clarify with customer during triage.",
            "confidence": "low",
        }

    if cap_val in (None, "", [], False):
        return {
            "match_status": "UNKNOWN",
            "evidence_source": "product_catalog",
            "gap_notes": f"Catalog missing {cap_field}.",
            "engineering_review_required": True,
            "suggested_validation": f"Request partner data for {label}.",
            "confidence": "medium",
        }

    if dimension_key == "heavy_load":
        try:
            req_load = float(requirement_value)
            if isinstance(requirement_value, str) and "lb" in requirement_value.lower():
                req_load = req_load * 0.453592
            cat_load = float(cap_val)
            if cat_load >= req_load:
                status = "MATCH"
            elif cat_load >= req_load * 0.85:
                status = "PARTIAL"
            else:
                status = "NOT_SUPPORTED"
            return {
                "match_status": status,
                "evidence_source": "product_catalog.load_capacity_kg",
                "gap_notes": None if status == "MATCH" else f"Catalog {cat_load}kg vs required {req_load}kg.",
                "engineering_review_required": status != "MATCH",
                "suggested_validation": "Confirm load test summary with partner.",
                "confidence": "medium",
            }
        except (TypeError, ValueError):
            pass

    if dimension_key == "quiet_operation":
        try:
            req_noise = float(requirement_value)
            cat_noise = float(cap_val)
            status = "MATCH" if cat_noise <= req_noise else "PARTIAL" if cat_noise <= req_noise + 5 else "NOT_SUPPORTED"
            return {
                "match_status": status,
                "evidence_source": "product_catalog.noise_db",
                "gap_notes": None if status == "MATCH" else f"Catalog {cat_noise}dB vs target {req_noise}dB.",
                "engineering_review_required": True,
                "suggested_validation": "Request validated noise test cycle.",
                "confidence": "medium",
            }
        except (TypeError, ValueError):
            pass

    if dimension_key in {"certification", "medical_industrial"}:
        req_certs = requirement_value if isinstance(requirement_value, list) else [str(requirement_value)]
        cat_certs = cap_val if isinstance(cap_val, list) else [str(cap_val)]
        overlap = set(c.lower() for c in req_certs) & set(c.lower() for c in cat_certs)
        status = "MATCH" if overlap else "PARTIAL" if cat_certs else "UNKNOWN"
        return {
            "match_status": status,
            "evidence_source": "product_catalog.certifications",
            "gap_notes": None if overlap else "Certification overlap not confirmed.",
            "engineering_review_required": True,
            "suggested_validation": "Collect cert index from partner.",
            "confidence": "medium" if overlap else "low",
        }

    return {
        "match_status": "PARTIAL",
        "evidence_source": f"product_catalog.{cap_field}",
        "gap_notes": "Requirement present; catalog has related field — manual review recommended.",
        "engineering_review_required": dimension_key in {"high_stability", "custom_mount_holes", "medical_industrial"},
        "suggested_validation": f"Validate {label} with partner engineering.",
        "confidence": "medium",
    }


def build_fit_summary(
    db: Session,
    row: CustomerProjectRequest,
    *,
    catalog_row: ProductCatalog | None = None,
) -> dict[str, Any]:
    req = row.requirements_json or {}
    partner_pending = False
    partner_code: str | None = None
    catalog_attrs: dict[str, Any] = {}

    if catalog_row is None and row.product_catalog_id:
        catalog_row = db.query(ProductCatalog).filter(ProductCatalog.id == row.product_catalog_id).first()
    if catalog_row:
        catalog_attrs = catalog_row.attributes_json if isinstance(catalog_row.attributes_json, dict) else {}
        if catalog_row.partner_id:
            partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == catalog_row.partner_id).first()
            if partner:
                partner_code = partner.partner_code
                partner_pending = bool(catalog_attrs.get("is_pending") or catalog_attrs.get("catalog_pending"))

    requirement_map = {
        "heavy_load": req.get("load_capacity_kg") or req.get("load_capacity_lb"),
        "quiet_operation": req.get("noise_db_target"),
        "high_stability": req.get("stability_requirement"),
        "extra_wide_multi_leg": req.get("width_mm") or req.get("leg_count") or req.get("desk_configuration"),
        "medical_industrial": req.get("medical_industrial"),
        "custom_mount_holes": req.get("mounting_holes"),
        "controller": req.get("controller_type"),
        "anti_collision": req.get("anti_collision"),
        "finish_color": req.get("color_finish") or req.get("powder_coat"),
        "certification": req.get("certifications"),
        "sample_validation": req.get("sample_required"),
        "lead_time": req.get("lead_time_days_max"),
        "warranty": req.get("warranty_requirement"),
        "stroke_range": req.get("stroke_range_mm"),
        "speed_duty": req.get("speed_mm_s") or req.get("duty_cycle"),
    }

    matches: list[dict[str, Any]] = []
    statuses: list[str] = []
    for dim_key, label, _cap in LIFTING_MATCH_DIMENSIONS:
        result = _match_status_for_dimension(
            dim_key,
            requirement_map.get(dim_key),
            catalog_attrs,
            partner_pending=partner_pending,
        )
        matches.append(
            {
                "dimension": dim_key,
                "label": label,
                **result,
            }
        )
        statuses.append(result["match_status"])

    if partner_pending:
        overall = "UNKNOWN"
    elif "NOT_SUPPORTED" in statuses:
        overall = "NOT_SUPPORTED"
    elif all(s == "MATCH" for s in statuses if s != "UNKNOWN"):
        overall = "MATCH"
    elif "MATCH" in statuses or "PARTIAL" in statuses:
        overall = "PARTIAL"
    else:
        overall = "UNKNOWN"

    coverage = capability_coverage(catalog_attrs)
    return {
        "overall_status": overall,
        "partner_code": partner_code,
        "partner_pending": partner_pending,
        "product_sku": row.sku or (catalog_row.internal_sku if catalog_row else None),
        "coverage_pct": coverage["coverage_pct"],
        "missing_fields": coverage["missing_labels"],
        "matches": matches,
        "disclaimer": "Internal recommendation only — not a customer-facing claim.",
    }


def site_payload_to_request_fields(body: SiteProjectRequestIn) -> dict[str, Any]:
    qty_min, qty_max = _parse_quantity_from_items(body.items)
    product_interest, sku = _parse_product_interest(body.items)
    req = requirements_to_json(
        body.requirements,
        extra={
            "delivery_method": body.delivery_method,
            "payment_method": body.payment_method,
            "order_notes": body.notes,
            "line_items": body.items[:20],
        },
    )
    return {
        "customer_name": body.customer_name or body.shipping_name or body.billing_name,
        "customer_email": str(body.customer_email) if body.customer_email else None,
        "company_name_text": body.company_name,
        "product_interest": product_interest,
        "sku": sku,
        "quantity_min": qty_min,
        "quantity_max": qty_max,
        "delivery_region": _parse_shipping_region(body.shipping_address),
        "project_scenario": body.project_scenario or body.notes,
        "requirements_json": req,
        "attachment_refs": [],
    }


def create_project_request_from_site(
    db: Session,
    body: SiteProjectRequestIn,
    *,
    idempotency_key: str | None,
    client_ip: str | None,
) -> CustomerProjectRequest:
    client_key = idempotency_key or _hash_ip(client_ip) or "anonymous"
    if not check_rate_limit(client_key):
        raise ValueError("rate_limit_exceeded")

    if idempotency_key:
        existing = (
            db.query(CustomerProjectRequest)
            .filter(CustomerProjectRequest.idempotency_key == idempotency_key)
            .first()
        )
        if existing:
            return existing

    fields = site_payload_to_request_fields(body)
    now = _now()
    row = CustomerProjectRequest(
        request_reference=_next_reference(),
        idempotency_key=idempotency_key,
        status=CustomerProjectRequestStatus.submitted.value,
        source="customer_site",
        submitted_at=now,
        client_ip_hash=_hash_ip(client_ip),
        **fields,
    )
    db.add(row)
    db.flush()

    if row.sku and not row.product_catalog_id:
        catalog = db.query(ProductCatalog).filter(ProductCatalog.internal_sku == row.sku).first()
        if catalog:
            row.product_catalog_id = catalog.id
            row.partner_id = catalog.partner_id

    row.completeness_json = compute_completeness(row)
    row.fit_summary_json = build_fit_summary(db, row)
    log_activity(
        db,
        object_type="customer_project_request",
        object_id=row.id,
        action="submitted",
        actor_id=None,
        diff={"source": "customer_site", "request_reference": row.request_reference},
    )
    db.commit()
    db.refresh(row)
    return row
