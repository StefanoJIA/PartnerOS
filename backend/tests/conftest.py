"""Pytest configuration."""

from __future__ import annotations

import os
from urllib.parse import unquote, urlparse


def _partneros_test_database_name(url: str) -> str:
    u = url.strip()
    for prefix in ("postgresql+psycopg://", "postgresql+psycopg2://", "postgresql+asyncpg://"):
        if u.startswith(prefix):
            u = "postgresql://" + u.split("://", 1)[1]
            break
    parsed = urlparse(u)
    path = unquote((parsed.path or "").lstrip("/"))
    if not path:
        return ""
    return path.split("/")[0].split("?")[0]


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: requires PARTNEROS_TEST_DATABASE_URL (isolated PostgreSQL, not the dev DB).",
    )
    test_url = os.environ.get("PARTNEROS_TEST_DATABASE_URL")
    if not test_url:
        return
    dbname = _partneros_test_database_name(test_url).lower()
    if "test" in dbname or "testing" in dbname:
        return
    import pytest

    pytest.exit(
        "PARTNEROS_TEST_DATABASE_URL must use a database name containing 'test' or 'testing' "
        f"(parsed name: {dbname!r}). Refusing to run tests to avoid accidental non-test databases.",
        returncode=2,
    )
