"""Shared redaction checks for committed handoff and operating records."""

from __future__ import annotations

import re
from pathlib import Path

COMMON_FORBIDDEN_MARKERS = (
    "backend/storage",
    "local_data",
    "raw command output",
    "raw response body",
    "internal_cost",
    "estimated_margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "supplier_private",
    "storage_key",
    "portal_customer_api_token",
    "secret_key",
    "password_hash",
    "database_url",
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY|DATABASE_URL)[A-Z0-9_]*)"
    r"\b:?\s*=\s*['\"]?([^'\"\s]+)",
    re.IGNORECASE,
)
BEARER_PATTERN = re.compile(r"\bAuthorization:?\s*Bearer\s+([^\s`'\"|]+)", re.IGNORECASE)
ALLOWED_SECRET_PLACEHOLDERS = {"<portal-server-token>", "<redacted>", "***", "REDACTED"}


def _is_placeholder(value: str) -> bool:
    stripped = value.strip()
    return stripped in ALLOWED_SECRET_PLACEHOLDERS or (stripped.startswith("<") and stripped.endswith(">"))


def redaction_issues(
    path: Path,
    text: str,
    extra_forbidden_markers: tuple[str, ...] = (),
    *,
    include_common_markers: bool = True,
) -> list[str]:
    """Return redaction issue labels for a committed record body."""

    issues: list[str] = []
    lowered = text.lower()
    common_markers = COMMON_FORBIDDEN_MARKERS if include_common_markers else ()
    for marker in (*common_markers, *extra_forbidden_markers):
        if marker in lowered:
            issues.append(f"{path.name}:{marker}")

    for line_no, line in enumerate(text.splitlines(), start=1):
        assignment = SECRET_ASSIGNMENT_PATTERN.search(line)
        if assignment and not _is_placeholder(assignment.group(2)):
            issues.append(f"{path.name}:{line_no}")
            continue
        bearer = BEARER_PATTERN.search(line)
        if bearer and not _is_placeholder(bearer.group(1)):
            issues.append(f"{path.name}:{line_no}")
    return issues
