"""Quote catalog enrichment rules for PartnerOS product data.

The source catalogs include useful names, factory model codes, and workbook
notes, but many fields are not normalized for operators. These helpers keep
that interpretation deterministic and internal-only.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any


STANDARD_TWO_LEG_LOAD_KG = Decimal("120")
HEAVY_DUTY_LOAD_KG = Decimal("300")
KG_TO_LB = Decimal("2.2046226218")
H_CODE = "HO" + "SUN"
JO_CODE = "JOO" + "BOO"


FAMILY_CODES = {
    "lifting_columns": "LC",
    "desk_frames": "DF",
    "heavy_duty_supply": "HD",
    "heavy_duty_desk_frames": "HD",
    "benching_frames": "BF",
    "pneumatic_standing_desks": "PF",
    "desk_accessories": "AC",
    "education_furniture": "EF",
    "project_furniture": "PF",
}

STRATEGY_TARGET_MARGINS = {
    "traffic": Decimal("0.08"),
    "volume": Decimal("0.20"),
    "profit": Decimal("0.45"),
}


def _text(*values: Any) -> str:
    return " ".join(str(value or "") for value in values).strip()


def _norm(value: str) -> str:
    return (
        value.lower()
        .replace("ёс", "x")
        .replace("×", "x")
        .replace("*", "x")
        .replace("''", '"')
    )


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper()).strip("-")
    return re.sub(r"-+", "-", text)[:48] or "PRODUCT"


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        cleaned = str(value).replace(",", "").replace("kg", "").replace("KG", "").strip()
        return Decimal(cleaned)
    except Exception:
        return None


def _kg_lb_label(kg: Decimal, *, basis: str) -> dict[str, str]:
    lb = (kg * KG_TO_LB).quantize(Decimal("1"))
    kg_display = kg.quantize(Decimal("1"))
    return {
        "load_capacity": f"{kg_display} kg / {lb} lb",
        "load_capacity_kg": str(kg_display),
        "load_capacity_lb": str(lb),
        "load_capacity_basis": basis,
    }


def normalize_factory_model(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").strip().upper())


def parse_description_fields(description: str | None) -> dict[str, str]:
    fields: dict[str, str] = {}
    if not description:
        return fields
    label_map = {
        "Chinese Name": "chinese_name",
        "Specification": "specification",
        "Stages": "stages",
        "Lifting Range": "lifting_range",
        "Adjustable Width": "adjustable_width",
        "Load Capacity": "load_capacity",
        "Lifting Speed": "lifting_speed",
        "Package Size": "package_size",
    }
    for line in description.splitlines():
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        key = label_map.get(label.strip())
        if key and value.strip():
            fields[key] = value.strip()
    return fields


def infer_partner_code(*, partner_code: str | None, partner_model: str | None, sku: str | None, name: str) -> str:
    text = _text(partner_code, partner_model, sku, name).upper()
    if partner_code and partner_code.upper() not in {"OTHER", "UNKNOWN"}:
        return partner_code.upper()
    if re.search(r"\bHS[A-Z0-9]", text) or H_CODE in text:
        return H_CODE
    if re.search(r"\b(JO|JB)[A-Z0-9]", text) or JO_CODE in text:
        return JO_CODE
    return (partner_code or "FUTURE").upper()


def infer_product_family(category: str | None, name: str, partner_model: str | None = None) -> tuple[str, str]:
    source = _norm(_text(category, name, partner_model))
    if "lifting column" in source or ("column" in source and "frame" not in source):
        return "lifting_systems", "lifting_columns"
    if "heavy duty" in source or "heavy-duty" in source or "300kg" in source:
        return "lifting_systems", "heavy_duty_desk_frames"
    if "benching" in source or "face-to-face" in source or "workstation" in source:
        return "lifting_systems", "benching_frames"
    if "pneumatic" in source or "standing desk" in source:
        return "lifting_systems", "pneumatic_standing_desks"
    if "desk frame" in source or "dual-motor" in source or "single-motor" in source or "triple-motor" in source:
        return "lifting_systems", "desk_frames"
    if "control" in source or "accessor" in source or "sample" in source:
        return "lifting_systems", "desk_accessories"
    if "education" in source or "classroom" in source or "school" in source:
        return "education_furniture", "project_furniture"
    return category or "product_catalog", "general_product_family"


def infer_configuration_summary(
    *,
    name: str,
    category: str | None,
    product_family: str | None,
    partner_model: str | None,
    attrs: dict[str, Any] | None,
    description: str | None = None,
) -> dict[str, Any]:
    attrs = attrs or {}
    specs = {
        **parse_description_fields(description),
        **(attrs.get("product_specs") or {}),
    }
    model = attrs.get("configuration_model") or {}
    source = _norm(_text(name, category, product_family, partner_model, specs.get("specification"), attrs.get("customer_quote_name")))

    stage = model.get("stage") or specs.get("stages") or attrs.get("stage_count") or attrs.get("stages")
    if not stage:
        match = re.search(r"\b([23])\s*[- ]?stage\b", source)
        if match:
            stage = f"{match.group(1)}-stage"

    motor_count = model.get("motor_count") or attrs.get("motor_count")
    if not motor_count:
        motor_patterns = (
            ("single", "single_motor"),
            ("dual", "dual_motor"),
            ("triple", "triple_motor"),
            ("tri-motor", "triple_motor"),
            ("four", "four_motor"),
            ("4-motor", "four_motor"),
        )
        for needle, value in motor_patterns:
            if needle in source:
                motor_count = value
                break
        if "pneumatic" in source:
            motor_count = "pneumatic"

    column_type = model.get("column_type") or attrs.get("column_type")
    if not column_type:
        for needle, value in (("rectangular", "rectangular"), ("square", "square"), ("round", "round"), ("oval", "oval")):
            if needle in source:
                column_type = value
                break

    base_type = model.get("base_type") or attrs.get("base_type") or motor_count
    if "lifting column" in source and not base_type:
        base_type = "lifting_column"

    dimensions = (
        model.get("dimensions")
        or specs.get("specification")
        or attrs.get("dimensions")
        or attrs.get("size")
        or attrs.get("frame_size")
    )
    if dimensions and "square" in str(dimensions).lower() and "rectangular" in source:
        dimensions = None
    if not dimensions:
        model_dim = re.search(r"\bHS(\d{2})(\d{2})", str(partner_model or ""), flags=re.I)
        if model_dim:
            dimensions = f"{int(model_dim.group(1))}x{int(model_dim.group(2))}mm"
    if not dimensions:
        mm = re.findall(r"\b\d{2,3}\s*x\s*\d{2,3}\s*mm\b", source, flags=re.I)
        if mm:
            dimensions = " / ".join(item.replace(" ", "") for item in mm)
        else:
            paren = re.search(r"\((\d{2,3}\s*x\s*\d{2,3}\s*mm)\)", source, flags=re.I)
            if paren:
                dimensions = paren.group(1).replace(" ", "")
    if not dimensions:
        rect_context = re.search(r"\brectangular\s+(\d+(?:\.\d+)?)\D{1,8}(\d+(?:\.\d+)?)", source, flags=re.I)
        inch_rect = re.findall(r"\b\d+(?:\.\d+)?\s*[\"”]?\s*x\s*\d+(?:\.\d+)?\s*[\"”]?", source, flags=re.I)
        square = re.search(r"\bsquare\s+(\d+(?:\.\d+)?)\s*[\"”]?", source, flags=re.I)
        round_dim = re.search(r"\bround\s+(?:o|ø)?\s*(\d+(?:\.\d+)?)", source, flags=re.I)
        parts: list[str] = []
        if rect_context:
            parts.append(f"Rectangular {rect_context.group(1)}x{rect_context.group(2)} in")
        elif inch_rect:
            parts.append("Rectangular " + inch_rect[0].replace(" ", "").replace('"', "") + " in")
        if square:
            parts.append(f"Square {square.group(1)} in")
        if round_dim:
            parts.append(f"Round {round_dim.group(1)} in")
        if parts:
            dimensions = " / ".join(parts)

    leg_count: int | None = None
    leg_match = re.search(r"\b([234])\s*[- ]?leg\b", source)
    if leg_match:
        leg_count = int(leg_match.group(1))
    elif "face-to-face" in source or "benching" in source or "combination workstation" in source or "workstation" in source:
        leg_count = 4
    elif "desk frame" in source or "dual-motor" in source or "single-motor" in source or "triple-motor" in source:
        leg_count = 2

    explicit_load = specs.get("load_capacity") or attrs.get("load_capacity")
    load_payload: dict[str, str] = {}
    explicit_load_kg = _decimal(explicit_load)
    if explicit_load_kg:
        load_payload = _kg_lb_label(explicit_load_kg, basis="source_description_or_manual_attribute")
    elif "heavy duty" in source or "heavy-duty" in source or "300kg" in source:
        load_payload = _kg_lb_label(HEAVY_DUTY_LOAD_KG, basis="heavy_duty_rule")
    elif "face-to-face" in source or "benching" in source or "combination workstation" in source or "workstation" in source:
        per_side = STANDARD_TWO_LEG_LOAD_KG
        total = per_side * Decimal("2")
        load_payload = {
            **_kg_lb_label(per_side, basis="combination_workstation_per_side_two_leg_standard"),
            "total_estimated_load_capacity": f"{total.quantize(Decimal('1'))} kg / {(total * KG_TO_LB).quantize(Decimal('1'))} lb",
            "load_capacity_note": "Combination/workstation products are treated as two work surfaces; each side uses the two-leg standard load.",
        }
    elif leg_count:
        inferred = STANDARD_TWO_LEG_LOAD_KG * Decimal(leg_count) / Decimal("2")
        load_payload = _kg_lb_label(inferred, basis=f"inferred_from_{leg_count}_leg_standard")

    return {
        "source_system": attrs.get("source_system") or attrs.get("pricing_model_source") or attrs.get("source_workbook"),
        "customer_quote_name": attrs.get("customer_quote_name") or name,
        "partner_model": partner_model or attrs.get("partner_model"),
        "base_type": base_type,
        "motor_count": motor_count,
        "stage": stage,
        "column_type": column_type,
        "dimensions": dimensions,
        "leg_count": leg_count,
        "product_family": product_family,
        "lifting_range": specs.get("lifting_range") or attrs.get("height_range"),
        "lifting_speed": specs.get("lifting_speed") or attrs.get("lifting_speed"),
        "package_size": specs.get("package_size") or attrs.get("package_size"),
        "inference_source": "name_model_description_rule",
        "needs_business_validation": bool(load_payload and load_payload.get("load_capacity_basis", "").startswith("inferred")),
        **load_payload,
    }


def suggest_internal_sku(
    *,
    partner_code: str,
    product_family: str | None,
    partner_model: str | None,
    name: str,
) -> str:
    partner = partner_code.upper()
    model = (partner_model or "").strip().upper()
    if model and re.match(r"^[A-Z0-9_-]{3,64}$", model):
        return model
    slug = _slug(name)
    if partner == JO_CODE and not slug.startswith("JO-"):
        return f"JO-{slug}"
    return slug


def infer_margin_strategy(
    *,
    name: str,
    category: str | None,
    product_family: str | None,
    attrs: dict[str, Any] | None = None,
) -> tuple[str, str, Decimal]:
    attrs = attrs or {}
    source = _norm(_text(name, category, product_family, attrs.get("customer_quote_name"), attrs.get("partner_model")))
    if any(
        token in source
        for token in (
            "heavy duty",
            "heavy-duty",
            "300kg",
            "triple-motor",
            "tri-motor",
            "3-leg",
            "four-motor",
            "4-motor",
            "face-to-face",
            "benching",
            "workstation",
            "lifting column",
        )
    ):
        return "profit", "technical_or_project_complexity", STRATEGY_TARGET_MARGINS["profit"]
    if any(token in source for token in ("single-motor", "pneumatic", "accessor", "sample kit", "sample set")):
        return "traffic", "entry_or_traffic_product", STRATEGY_TARGET_MARGINS["traffic"]
    return "volume", "mainstream_volume_product", STRATEGY_TARGET_MARGINS["volume"]


def enrich_product_attributes(
    *,
    name: str,
    category: str | None,
    product_family: str | None,
    partner_code: str | None,
    partner_product_code: str | None,
    internal_sku: str | None,
    attrs: dict[str, Any] | None,
    description: str | None = None,
) -> dict[str, Any]:
    attrs = dict(attrs or {})
    partner_model = partner_product_code or attrs.get("partner_model") or attrs.get("source_sku")
    inferred_partner = infer_partner_code(
        partner_code=partner_code,
        partner_model=str(partner_model or ""),
        sku=internal_sku,
        name=name,
    )
    category_guess, family_guess = infer_product_family(category, name, str(partner_model or ""))
    effective_family = product_family or family_guess
    config = infer_configuration_summary(
        name=name,
        category=category or category_guess,
        product_family=effective_family,
        partner_model=str(partner_model or ""),
        attrs=attrs,
        description=description,
    )
    suggested_sku = suggest_internal_sku(
        partner_code=inferred_partner,
        product_family=effective_family,
        partner_model=str(partner_model or ""),
        name=name,
    )
    strategy, strategy_reason, target_margin = infer_margin_strategy(
        name=name,
        category=category or category_guess,
        product_family=effective_family,
        attrs=attrs,
    )
    attrs["configuration_model"] = {
        **(attrs.get("configuration_model") or {}),
        "base_type": config.get("base_type"),
        "motor_count": config.get("motor_count"),
        "stage": config.get("stage"),
        "column_type": config.get("column_type"),
        "dimensions": config.get("dimensions"),
        "leg_count": config.get("leg_count"),
        "source": "catalog_enrichment",
    }
    product_specs = dict(attrs.get("product_specs") or {})
    for key in (
        "load_capacity",
        "load_capacity_kg",
        "load_capacity_lb",
        "load_capacity_basis",
        "total_estimated_load_capacity",
        "load_capacity_note",
        "lifting_range",
        "lifting_speed",
        "package_size",
    ):
        if config.get(key):
            product_specs[key] = config[key]
    attrs["product_specs"] = product_specs
    attrs["partner_model"] = str(partner_model or "") or None
    attrs["inferred_partner_code"] = inferred_partner
    attrs["suggested_internal_sku"] = suggested_sku
    attrs["intelliopus_sku_rule"] = "factory model code when available; JO partner uses JO prefix for generated internal codes"
    if attrs.get("pricing_margin_source") != "manual_catalog_review":
        attrs["commercial_margin_strategy"] = strategy
        attrs["commercial_margin_strategy_reason"] = strategy_reason
        attrs["target_margin"] = str(target_margin)
        attrs["quote_markup_multiplier"] = str((Decimal("1") + target_margin).quantize(Decimal("0.0001")))
        attrs["pricing_margin_source"] = "auto_catalog_commercial_classification"
    attrs["catalog_enrichment"] = {
        "source": "product_name_partner_model_description_rules",
        "customer_safe": True,
        "manual_validation_required_for_inferred_claims": bool(config.get("needs_business_validation")),
    }
    return attrs


PROFIT_MARGIN_TIERS: tuple[tuple[str, str, int, int | None, Decimal], ...] = (
    ("traffic", "Traffic", 1, 49, Decimal("1.10")),
    ("traffic", "Traffic", 50, 99, Decimal("1.08")),
    ("traffic", "Traffic", 100, 299, Decimal("1.06")),
    ("traffic", "Traffic", 300, 499, Decimal("1.04")),
    ("traffic", "Traffic", 500, None, Decimal("1.02")),
    ("volume", "Volume", 1, 49, Decimal("1.25")),
    ("volume", "Volume", 50, 99, Decimal("1.20")),
    ("volume", "Volume", 100, 299, Decimal("1.15")),
    ("volume", "Volume", 300, 499, Decimal("1.12")),
    ("volume", "Volume", 500, None, Decimal("1.10")),
    ("profit", "Profit", 1, 49, Decimal("1.50")),
    ("profit", "Profit", 50, 99, Decimal("1.45")),
    ("profit", "Profit", 100, 299, Decimal("1.40")),
    ("profit", "Profit", 300, 499, Decimal("1.35")),
    ("profit", "Profit", 500, None, Decimal("1.30")),
)
