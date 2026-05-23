"""Contract tests for /api/v1 system & portal endpoints (Phase 1)."""

from __future__ import annotations

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.runtime_mode import AppRuntimeMode
from app.core.version import APP_VERSION
from app.main import app

SENSITIVE_MARKERS = (
    "dev-secret-change-in-production",
    "partneros:partneros",
    "postgresql+psycopg://partneros:partneros",
    "OPENAI_API_KEY",
)


def _envelope(body: dict) -> tuple[dict, dict]:
    assert body.get("ok") is True
    assert "data" in body
    assert "meta" in body
    assert "request_id" in body["meta"]
    assert "timestamp" in body["meta"]
    return body["data"], body["meta"]


def test_health_legacy_fields_unchanged():
    with TestClient(app) as c:
        r = c.get("/health")
    assert r.status_code == 200
    data = r.json()
    for key in (
        "status",
        "version",
        "runtime_mode",
        "bootstrap_status",
        "database_status",
        "database_lifecycle_phase",
        "migration_pending",
        "alembic_current_revision",
        "alembic_head_revision",
    ):
        assert key in data


def test_v1_readiness_envelope_ok_when_db_ready():
    with patch("app.services.system.platform.check_database", return_value=("ready", [])):
        with patch(
            "app.services.system.platform.get_migration_revisions",
            return_value=("rev_a", "rev_a", None),
        ):
            with TestClient(app) as c:
                r = c.get("/api/v1/system/readiness")
    assert r.status_code == 200
    body = r.json()
    data, meta = _envelope(body)
    assert body["ok"] is True
    assert data["service"] == "intellioffice"
    assert data["database_ready"] is True
    assert data["database_at_head"] is True
    assert data["ok"] is True
    assert r.headers.get("X-Request-ID") == meta["request_id"]


def test_v1_doctor_does_not_leak_secrets():
    settings = Settings(
        APP_RUNTIME_MODE=AppRuntimeMode.development,
        DATABASE_URL="postgresql+psycopg://partneros:supersecret@127.0.0.1:5432/partneros",
        SECRET_KEY="dev-secret-change-in-production",
        OPENAI_API_KEY="sk-test-should-not-appear",
    )
    with patch("app.services.system.platform.check_database", return_value=("ready", [])):
        with patch(
            "app.services.system.platform.get_migration_revisions",
            return_value=("0001", "0001", None),
        ):
            with patch("app.services.system.platform.inspect_lifecycle_dev") as mock_dlm:
                from app.core.database_lifecycle import LifecycleSnapshot

                mock_dlm.return_value = LifecycleSnapshot(
                    phase="ready",
                    database_status="ready",
                    alembic_current_revision="0001",
                    alembic_head_revision="0001",
                    migration_pending=False,
                )
                with patch("app.api.v1.routes.system.get_settings", return_value=settings):
                    with TestClient(app) as c:
                        r = c.get("/api/v1/system/doctor")
    assert r.status_code == 200
    raw = json.dumps(r.json())
    for marker in SENSITIVE_MARKERS:
        assert marker not in raw
    data, _ = _envelope(r.json())
    assert "supersecret" not in json.dumps(data)
    assert data["database"]["database_url_masked"] == "postgresql+psycopg://partneros:***@127.0.0.1:5432/partneros"
    assert data["auth"]["secret_is_dev_default"] is True


def test_v1_portal_manifest_modules_and_capabilities():
    with TestClient(app) as c:
        r = c.get("/api/v1/portal/manifest")
    assert r.status_code == 200
    data, _ = _envelope(r.json())
    assert data["service_id"] == "intellioffice"
    assert data["api_version"] == "v1"
    assert data["version"] == APP_VERSION
    assert "runtime_mode" in data
    assert isinstance(data["modules"], list) and len(data["modules"]) >= 3
    assert isinstance(data["capabilities"], list) and "crm" in data["capabilities"]
    keys = {m["key"] for m in data["modules"]}
    assert "crm" in keys and "leads" in keys
