"""Canonical object_type strings for polymorphic links (API + DB)."""

from enum import Enum


class ObjectType(str, Enum):
    company = "company"
    contact = "contact"
    lead = "lead"
    manufacturing_partner = "manufacturing_partner"
    product = "product"
    rfq = "rfq"
    quotation = "quotation"
    sample = "sample"
    order = "order"
    field_visit = "field_visit"
    field_visit_plan = "field_visit_plan"
    task = "task"
    interaction = "interaction"
    user = "user"
    file = "file"
    market_intelligence = "market_intelligence"


ALLOWED_OBJECT_TYPES = frozenset(m.value for m in ObjectType)


def normalize_object_type(value: str) -> str:
    v = value.strip().lower()
    if v not in ALLOWED_OBJECT_TYPES:
        raise ValueError(f"Invalid object_type: {value}")
    return v
