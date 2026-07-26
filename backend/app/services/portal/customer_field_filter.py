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
    "fit_risk",
    "internal_fit",
    "internal_risk",
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
    "internal_attachment",
)

FORBIDDEN_KEY_SUBSTRINGS = (
    "margin",
    "internal_cost",
    "cost_snapshot",
    "pricing_breakdown",
    "supplier_private",
    "supplier_reference",
    "supplier_note",
    "internal_attachment",
    "fit_risk",
)


def _key_is_forbidden(key: str) -> bool:
    lowered = str(key).lower()
    if lowered in FORBIDDEN_FIELD_NAMES:
        return True
    if any(marker in lowered for marker in ("token", "secret", "password")):
        return True
    return any(marker in lowered for marker in FORBIDDEN_KEY_SUBSTRINGS)


def strip_forbidden_internal_fields(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if _key_is_forbidden(key):
                continue
            cleaned[key] = strip_forbidden_internal_fields(item)
        return cleaned
    if isinstance(value, list):
        return [strip_forbidden_internal_fields(item) for item in value]
    return value


def assert_no_forbidden_internal_fields(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _key_is_forbidden(key):
                raise ValueError(f"Forbidden customer portal field leaked: {key}")
            assert_no_forbidden_internal_fields(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_forbidden_internal_fields(item)
