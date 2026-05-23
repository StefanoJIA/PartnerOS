"""Helpers for safe display of database URLs (never log full passwords)."""

from __future__ import annotations

import re

from sqlalchemy.engine.url import make_url


def mask_database_url(url: str | None) -> str:
    """Return a connection string with password redacted for logs and terminal output."""
    u = (url or "").strip()
    if not u:
        return "not configured"
    try:
        parsed = make_url(u)
        if parsed.password is not None:
            return str(parsed.set(password="****"))
        return str(parsed)
    except Exception:  # noqa: BLE001
        return "(unparseable DATABASE_URL)"


def extract_db_user_from_error(message: str) -> str | None:
    """Best-effort parse of PostgreSQL authentication error for clearer /health text."""
    m = re.search(r'user\s+"([^"]+)"', message, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"user\s+'([^']+)'", message, re.IGNORECASE)
    if m:
        return m.group(1)
    return None
