"""JSON-safe serialization for JSONB columns (activity log diff, etc.)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


def serialize_for_json(value: Any) -> Any:
    """Convert UUID, datetime, Decimal, and nested structures for JSON storage."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): serialize_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_for_json(v) for v in value]
    return value
