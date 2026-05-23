"""D4 Database Lifecycle Manager unit tests (mocked Alembic)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.core.database_lifecycle import (
    LifecycleSnapshot,
    run_desktop_lifecycle,
)
from app.core.runtime_mode import AppRuntimeMode


@pytest.fixture
def desktop_db_settings() -> Settings:
    return Settings(
        APP_RUNTIME_MODE=AppRuntimeMode.desktop,
        DATABASE_URL="postgresql+psycopg://u:p@127.0.0.1:5432/db",
    )


def test_run_desktop_lifecycle_not_configured() -> None:
    s = Settings(APP_RUNTIME_MODE=AppRuntimeMode.desktop, DATABASE_URL="")
    out = run_desktop_lifecycle(s)
    assert out.phase == "not_configured"
    assert out.database_status == "not_configured"


def test_run_desktop_skipped_when_not_desktop(desktop_db_settings: Settings) -> None:
    dev = Settings(
        APP_RUNTIME_MODE=AppRuntimeMode.development,
        DATABASE_URL=desktop_db_settings.DATABASE_URL,
    )
    out = run_desktop_lifecycle(dev)
    assert "product runtime modes" in (out.detail or "").lower()
    assert out.phase == "ready"


def test_run_desktop_no_upgrade_when_at_head(desktop_db_settings: Settings) -> None:
    with patch("app.core.database_lifecycle.check_database", return_value=("ready", [])):
        with patch(
            "app.core.database_lifecycle.get_migration_revisions",
            return_value=("abc123", "abc123", MagicMock()),
        ):
            with patch("app.core.database_lifecycle.run_alembic_upgrade_to_head") as up:
                out = run_desktop_lifecycle(desktop_db_settings)
    assert out.phase == "ready"
    assert out.migration_pending is False
    up.assert_not_called()


def test_run_desktop_migrates_when_behind(desktop_db_settings: Settings) -> None:
    phases: list[str] = []

    def cb(snap: LifecycleSnapshot) -> None:
        phases.append(snap.phase)

    with patch("app.core.database_lifecycle.check_database", return_value=("ready", [])):
        with patch(
            "app.core.database_lifecycle.get_migration_revisions",
            side_effect=[
                ("0001", "0004", MagicMock()),
                ("0004", "0004", MagicMock()),
            ],
        ):
            with patch("app.core.database_lifecycle.run_alembic_upgrade_to_head"):
                out = run_desktop_lifecycle(desktop_db_settings, progress=cb)
    assert out.phase == "ready"
    assert "migrating" in phases
    assert out.alembic_head_revision == "0004"


def test_run_desktop_migration_failure(desktop_db_settings: Settings) -> None:
    with patch("app.core.database_lifecycle.check_database", return_value=("ready", [])):
        with patch(
            "app.core.database_lifecycle.get_migration_revisions",
            return_value=("0001", "0004", MagicMock()),
        ):
            with patch(
                "app.core.database_lifecycle.run_alembic_upgrade_to_head",
                side_effect=RuntimeError("boom"),
            ):
                out = run_desktop_lifecycle(desktop_db_settings)
    assert out.phase == "error"
    assert out.errors
    assert "Migration failed" in out.errors[0]
