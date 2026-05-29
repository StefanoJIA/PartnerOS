"""Customer-visible field filtering for the D7.7 portal bridge."""

from __future__ import annotations

from typing import Any

FORBIDDEN_FIELD_NAMES = {
    "internal_cost",
    "margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "description_internal",
    "internal_notes",
    "supplier_private_notes",
    "supplier_reference",
    "backend_path",
    "storage_key",
    "token",
    "secret",
    "password",
}

FORBIDDEN_TEXT_MARKERS = (
    "internal_cost",
    "margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "supplier private",
    "backend/storage",
    "local_data",
    "portal_customer_api_token",
)


def strip_forbidden_internal_fields(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            lowered = key.lower()
            if lowered in FORBIDDEN_FIELD_NAMES:
                continue
            if any(marker in lowered for marker in ("token", "secret", "password")):
                continue
            cleaned[key] = strip_forbidden_internal_fields(item)
        return cleaned
    if isinstance(value, list):
        return [strip_forbidden_internal_fields(item) for item in value]
    return value


def assert_no_forbidden_internal_fields(value: Any) -> None:
    text = str(value).lower()
    for marker in FORBIDDEN_TEXT_MARKERS:
        if marker in text:
            raise ValueError(f"Forbidden customer portal field leaked: {marker}")
