"""Minimal startup/bootstrap state for desktop-oriented deployment (D1 + D4 DLM)."""

from __future__ import annotations

import logging
from typing import Any, Literal

from app.core.config import Settings
from app.core.database_lifecycle import (
    PRODUCT_AUTO_MIGRATE_MODES,
    LifecycleSnapshot,
    check_database,
    DatabaseStatus,
    inspect_lifecycle_dev,
)
from app.core.runtime_mode import AppRuntimeMode

logger = logging.getLogger(__name__)

BootstrapStatus = Literal["ready", "degraded", "error"]
HealthStatus = Literal["ok", "degraded", "error"]


def _bootstrap_status(
    runtime_mode: AppRuntimeMode,
    db_status: DatabaseStatus,
    dlm: LifecycleSnapshot,
) -> BootstrapStatus:
    if db_status == "ready":
        if runtime_mode is AppRuntimeMode.development and dlm.migration_pending:
            return "degraded"
        if dlm.phase == "error":
            return "error"
        if dlm.phase != "ready":
            return "degraded"
        return "ready"
    if runtime_mode is AppRuntimeMode.development:
        if db_status in ("unavailable", "not_configured"):
            return "degraded"
        return "error"
    return "error"


def _overall_status(bootstrap_status: BootstrapStatus) -> HealthStatus:
    if bootstrap_status == "error":
        return "error"
    if bootstrap_status == "degraded":
        return "degraded"
    return "ok"


def _snapshot_to_payload(
    version: str,
    settings: Settings,
    dlm: LifecycleSnapshot,
) -> dict[str, Any]:
    runtime_mode = settings.APP_RUNTIME_MODE
    payload: dict[str, Any] = {
        "status": "error",
        "version": version,
        "runtime_mode": runtime_mode.value,
        "bootstrap_status": "error",
        "database_status": dlm.database_status,
        "database_lifecycle_phase": dlm.phase,
        "alembic_current_revision": dlm.alembic_current_revision,
        "alembic_head_revision": dlm.alembic_head_revision,
        "migration_pending": dlm.migration_pending,
    }
    if dlm.detail:
        payload["database_lifecycle_detail"] = dlm.detail

    errors = list(dlm.errors)
    if runtime_mode is not AppRuntimeMode.development and dlm.database_status == "not_configured":
        msg = "DATABASE_URL is not configured"
        if msg not in errors:
            errors.append(msg)

    bootstrap_status = _bootstrap_status(runtime_mode, dlm.database_status, dlm)
    status = _overall_status(bootstrap_status)
    payload["bootstrap_status"] = bootstrap_status
    payload["status"] = status
    if errors:
        payload["errors"] = errors
    if status != "ok":
        logger.warning(
            "health: status=%s bootstrap=%s db=%s dlm=%s mode=%s",
            status,
            bootstrap_status,
            dlm.database_status,
            dlm.phase,
            runtime_mode.value,
        )
    return payload


def merge_snapshot_with_live_db(
    settings: Settings,
    dlm: LifecycleSnapshot,
) -> LifecycleSnapshot:
    """Refresh connectivity; if DB is down, surface error even when DLM snapshot lags."""
    db_status, errors = check_database(settings)
    if db_status == "not_configured":
        return LifecycleSnapshot(
            phase="not_configured",
            database_status="not_configured",
            errors=errors or list(dlm.errors),
            alembic_current_revision=dlm.alembic_current_revision,
            alembic_head_revision=dlm.alembic_head_revision,
            migration_pending=dlm.migration_pending,
            detail=dlm.detail,
        )
    if db_status != "ready":
        merged_err = list(dict.fromkeys(list(dlm.errors) + list(errors)))
        return LifecycleSnapshot(
            phase="error",
            database_status=db_status,
            errors=merged_err or ["database unreachable"],
            alembic_current_revision=dlm.alembic_current_revision,
            alembic_head_revision=dlm.alembic_head_revision,
            migration_pending=dlm.migration_pending,
            detail=dlm.detail,
        )
    if db_status == "ready":
        in_progress = dlm.phase in ("checking", "initializing", "migrating")
        stale = dlm.phase == "error" or dlm.database_status != "ready"
        if stale and not in_progress:
            return inspect_lifecycle_dev(settings)
        return dlm


def build_health_payload(
    version: str,
    settings: Settings,
    *,
    app: Any | None = None,
) -> dict[str, Any]:
    """Compute health JSON (startup, /health, and desktop DLM thread state)."""
    runtime_mode = settings.APP_RUNTIME_MODE

    if app is not None and runtime_mode in PRODUCT_AUTO_MIGRATE_MODES:
        lock = getattr(app.state, "dlm_lock", None)
        prog = getattr(app.state, "dlm_progress", None)
        snap = getattr(app.state, "dlm_snapshot", None)

        if lock is not None:
            with lock:
                active = prog if prog is not None else snap
        else:
            active = prog if prog is not None else snap

        if active is not None:
            dlm = merge_snapshot_with_live_db(settings, active)
            return _snapshot_to_payload(version, settings, dlm)

    if app is not None and runtime_mode not in PRODUCT_AUTO_MIGRATE_MODES:
        cached = getattr(app.state, "dlm_snapshot", None)
        if isinstance(cached, LifecycleSnapshot):
            dlm = merge_snapshot_with_live_db(settings, cached)
            return _snapshot_to_payload(version, settings, dlm)

    if runtime_mode in PRODUCT_AUTO_MIGRATE_MODES:
        dlm = merge_snapshot_with_live_db(
            settings,
            LifecycleSnapshot(phase="checking", database_status="not_configured"),
        )
        return _snapshot_to_payload(version, settings, dlm)

    dlm = inspect_lifecycle_dev(settings)
    dlm = merge_snapshot_with_live_db(settings, dlm)
    return _snapshot_to_payload(version, settings, dlm)


# Re-export for callers that imported check_database from bootstrap
__all__ = [
    "build_health_payload",
    "check_database",
    "BootstrapStatus",
    "DatabaseStatus",
    "HealthStatus",
]
