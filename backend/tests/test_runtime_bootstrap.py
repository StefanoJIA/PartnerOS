import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.bootstrap import build_health_payload
from app.core.config import Settings
from app.core.runtime_mode import AppRuntimeMode
from app.core.version import APP_VERSION


@pytest.mark.parametrize("mode", ["development", "desktop", "demo", "future_cloud"])
def test_app_runtime_mode_accepts_valid_values(mode: str) -> None:
    with patch.dict(os.environ, {"APP_RUNTIME_MODE": mode}, clear=False):
        s = Settings()
        assert s.APP_RUNTIME_MODE.value == mode


def test_app_runtime_mode_invalid_raises() -> None:
    with patch.dict(os.environ, {"APP_RUNTIME_MODE": "production"}, clear=False):
        with pytest.raises(ValidationError):
            Settings()


def test_build_health_development_empty_database_url() -> None:
    s = Settings(APP_RUNTIME_MODE=AppRuntimeMode.development, DATABASE_URL="")
    p = build_health_payload(APP_VERSION, s)
    assert p["runtime_mode"] == "development"
    assert p["database_status"] == "not_configured"
    assert p["bootstrap_status"] == "degraded"
    assert p["status"] == "degraded"


def test_settings_jwt_secret_alias_constructor(tmp_path, monkeypatch) -> None:
    """Avoid picking up workspace backend/.env (SECRET_KEY would override JWT_SECRET)."""
    monkeypatch.chdir(tmp_path)
    s = Settings(JWT_SECRET="from-alias", DATABASE_URL="")
    assert s.SECRET_KEY == "from-alias"


def test_build_health_development_auth_failed(monkeypatch) -> None:
    from app.core import database_lifecycle as dl

    def fake_check(_settings: Settings) -> tuple:
        return (
            "auth_failed",
            [
                'FATAL:  password authentication failed for user "partneros"',
                "PostgreSQL rejected the configured credentials for user 'partneros'.",
            ],
        )

    monkeypatch.setattr(dl, "check_database", fake_check)
    s = Settings(
        APP_RUNTIME_MODE=AppRuntimeMode.development,
        DATABASE_URL="postgresql+psycopg://partneros:bad@127.0.0.1:5432/partneros",
    )
    p = build_health_payload(APP_VERSION, s)
    assert p["database_status"] == "auth_failed"
    assert p["status"] == "error"
    assert p["bootstrap_status"] == "error"


def test_merge_snapshot_recovers_when_db_becomes_ready(monkeypatch) -> None:
    from app.core.bootstrap import merge_snapshot_with_live_db
    from app.core.database_lifecycle import LifecycleSnapshot

    stale = LifecycleSnapshot(
        phase="error",
        database_status="unavailable",
        errors=['connection to server at "127.0.0.1", port 5435 failed'],
    )

    def fake_check(_settings: Settings) -> tuple:
        return ("ready", [])

    def fake_inspect(_settings: Settings) -> LifecycleSnapshot:
        return LifecycleSnapshot(
            phase="ready",
            database_status="ready",
            alembic_current_revision="0005",
            alembic_head_revision="0005",
            migration_pending=False,
        )

    monkeypatch.setattr("app.core.bootstrap.check_database", fake_check)
    monkeypatch.setattr("app.core.bootstrap.inspect_lifecycle_dev", fake_inspect)
    s = Settings(APP_RUNTIME_MODE=AppRuntimeMode.development, DATABASE_URL="postgresql://x")
    refreshed = merge_snapshot_with_live_db(s, stale)
    assert refreshed.phase == "ready"
    assert refreshed.database_status == "ready"
    assert not refreshed.errors


def test_build_health_desktop_empty_database_url() -> None:
    s = Settings(APP_RUNTIME_MODE=AppRuntimeMode.desktop, DATABASE_URL="")
    p = build_health_payload(APP_VERSION, s)
    assert p["database_status"] == "not_configured"
    assert p["bootstrap_status"] == "error"
    assert p["status"] == "error"
    assert "errors" in p
