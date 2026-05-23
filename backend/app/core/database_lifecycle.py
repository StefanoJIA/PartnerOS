"""Database Lifecycle Manager (DLM) — D4 product runtime path.

Orchestrates connection checks and Alembic migrations for **desktop / demo /
future_cloud** (`PRODUCT_AUTO_MIGRATE_MODES`). Does not bundle or init
PostgreSQL (see docs/database_lifecycle.md). Structural truth remains Alembic + models.

**Open decision**: final desktop DB carrier (PostgreSQL vs SQLite vs dual path) is
**not** decided by this module; D4 targets the repo's existing PostgreSQL stack only.
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.core.db_url_utils import extract_db_user_from_error
from app.core.runtime_mode import AppRuntimeMode

logger = logging.getLogger(__name__)

DatabaseLifecyclePhase = Literal[
    "not_configured",
    "checking",
    "initializing",
    "migrating",
    "ready",
    "error",
]

DatabaseStatus = Literal[
    "ready",
    "unavailable",
    "not_configured",
    "error",
    "auth_failed",
    "database_missing",
]

_NOT_CONFIGURED_HINT = (
    "DATABASE_URL is not configured. Copy backend/.env.example to backend/.env "
    "or run: python scripts/init_local_env.py (from the backend directory), then set DATABASE_URL."
)

PRODUCT_AUTO_MIGRATE_MODES: frozenset[AppRuntimeMode] = frozenset(
    {
        AppRuntimeMode.desktop,
        AppRuntimeMode.demo,
        AppRuntimeMode.future_cloud,
    }
)


@dataclass
class LifecycleSnapshot:
    phase: DatabaseLifecyclePhase
    database_status: DatabaseStatus
    errors: list[str] = field(default_factory=list)
    alembic_current_revision: str | None = None
    alembic_head_revision: str | None = None
    migration_pending: bool = False
    detail: str | None = None


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    ini = _backend_root() / "alembic.ini"
    return Config(str(ini))


def check_database(settings: Settings) -> tuple[DatabaseStatus, list[str]]:
    """Return (database_status, error_messages). Does not raise for expected failures."""
    errors: list[str] = []
    val = getattr(settings, "DATABASE_URL", None)
    url = (str(val) if val is not None else "").strip()
    if not url:
        errors.append(_NOT_CONFIGURED_HINT)
        return "not_configured", errors

    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ready", errors
    except SQLAlchemyError as e:
        raw = str(e)
        msg = raw.split("\n")[0][:500]
        lowered = msg.lower()
        errors.append(msg)

        if "password authentication failed" in lowered:
            user = extract_db_user_from_error(msg) or "unknown"
            errors.append(
                f"PostgreSQL rejected the configured credentials for user {user!r}. "
                "Check DATABASE_URL in backend/.env (password must match the database role)."
            )
            return "auth_failed", errors
        if "does not exist" in lowered and "database" in lowered:
            errors.append(
                "The database named in DATABASE_URL does not exist on the server. "
                "Create it (e.g. CREATE DATABASE partneros; ) or fix the URL."
            )
            return "database_missing", errors
        if "invalid dsn" in lowered:
            return "error", errors
        if (
            "could not translate host name" in lowered
            and "name or service not known" in lowered
        ):
            return "error", errors
        # connection refused, timeout, TLS, etc.
        if (
            "connection refused" in lowered
            or "actively refused" in lowered
            or "could not connect" in lowered
            or "timeout" in lowered
        ):
            errors.append(
                "Could not reach PostgreSQL at the host/port in DATABASE_URL. "
                "Confirm the server is running and the URL is correct."
            )
            return "unavailable", errors
        return "unavailable", errors
    except OSError as e:
        errors.append(str(e)[:500])
        return "unavailable", errors


def get_migration_revisions(settings: Settings) -> tuple[str | None, str | None, Config]:
    """(current_revision, head_revision, alembic_config). Raises on Alembic misconfig."""
    cfg = _alembic_config()
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    if not heads:
        raise RuntimeError("No Alembic heads found")
    head = heads[0] if len(heads) == 1 else sorted(heads)[-1]

    url = (settings.DATABASE_URL or "").strip()
    if not url:
        return None, head, cfg

    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        current = ctx.get_current_revision()
    return current, head, cfg


def run_alembic_upgrade_to_head() -> None:
    """Run ``alembic upgrade head`` with ``backend`` as working directory (env.py / imports)."""
    root = _backend_root()
    old = os.getcwd()
    try:
        os.chdir(root)
        command.upgrade(_alembic_config(), "head")
    finally:
        os.chdir(old)


ProgressCallback = Callable[[LifecycleSnapshot], None]


def run_desktop_lifecycle(
    settings: Settings,
    *,
    progress: ProgressCallback | None = None,
) -> LifecycleSnapshot:
    """Full DLM for desktop: connect, migrate if needed, verify head. Not for development auto-migrate."""

    def emit(s: LifecycleSnapshot) -> None:
        if progress:
            progress(s)

    if settings.APP_RUNTIME_MODE not in PRODUCT_AUTO_MIGRATE_MODES:
        return LifecycleSnapshot(
            phase="ready",
            database_status="ready",
            detail="DLM auto-migrate runs only in product runtime modes (desktop/demo/future_cloud)",
        )

    emit(LifecycleSnapshot(phase="checking", database_status="not_configured"))
    db_status, errors = check_database(settings)
    if db_status == "not_configured":
        err = LifecycleSnapshot(
            phase="not_configured",
            database_status="not_configured",
            errors=["DATABASE_URL is not configured"],
        )
        emit(err)
        return err
    if db_status != "ready":
        err = LifecycleSnapshot(phase="error", database_status=db_status, errors=errors or ["database unreachable"])
        emit(err)
        return err

    try:
        current, head, _cfg = get_migration_revisions(settings)
    except Exception as e:  # noqa: BLE001
        logger.exception("DLM: migration inspection failed")
        err = LifecycleSnapshot(
            phase="error",
            database_status="ready",
            errors=[str(e)[:500]],
            detail="alembic_inspect",
        )
        emit(err)
        return err

    pending = current != head
    if pending:
        emit(
            LifecycleSnapshot(
                phase="initializing",
                database_status="ready",
                alembic_current_revision=current,
                alembic_head_revision=head,
                migration_pending=True,
                detail="preparing schema migration",
            )
        )
        emit(
            LifecycleSnapshot(
                phase="migrating",
                database_status="ready",
                alembic_current_revision=current,
                alembic_head_revision=head,
                migration_pending=True,
                detail="alembic upgrade head",
            )
        )
        try:
            run_alembic_upgrade_to_head()
        except Exception as e:  # noqa: BLE001
            logger.exception("DLM: alembic upgrade failed")
            err = LifecycleSnapshot(
                phase="error",
                database_status="ready",
                errors=[f"Migration failed: {str(e)[:400]}"],
                alembic_current_revision=current,
                alembic_head_revision=head,
                migration_pending=True,
                detail="alembic_upgrade",
            )
            emit(err)
            return err
        try:
            current_after, head_after, _ = get_migration_revisions(settings)
        except Exception as e:  # noqa: BLE001
            err = LifecycleSnapshot(
                phase="error",
                database_status="ready",
                errors=[str(e)[:500]],
                detail="post_migration_inspect",
            )
            emit(err)
            return err
        if current_after != head_after:
            err = LifecycleSnapshot(
                phase="error",
                database_status="ready",
                errors=["After upgrade, revision still does not match head"],
                alembic_current_revision=current_after,
                alembic_head_revision=head_after,
                migration_pending=True,
            )
            emit(err)
            return err
        current, head = current_after, head_after

    snap = LifecycleSnapshot(
        phase="ready",
        database_status="ready",
        alembic_current_revision=current,
        alembic_head_revision=head,
        migration_pending=False,
    )
    emit(snap)
    return snap


def inspect_lifecycle_dev(settings: Settings) -> LifecycleSnapshot:
    """Read-only inspect for development / reporting (no auto-upgrade)."""
    db_status, errors = check_database(settings)
    if db_status == "not_configured":
        return LifecycleSnapshot(
            phase="not_configured",
            database_status="not_configured",
            errors=errors,
        )
    if db_status != "ready":
        return LifecycleSnapshot(
            phase="error",
            database_status=db_status,
            errors=errors,
        )
    try:
        current, head, _ = get_migration_revisions(settings)
        pending = current != head
        phase: DatabaseLifecyclePhase = "initializing" if pending else "ready"
        return LifecycleSnapshot(
            phase=phase,
            database_status="ready",
            alembic_current_revision=current,
            alembic_head_revision=head,
            migration_pending=pending,
            detail="development: run alembic upgrade head" if pending else None,
        )
    except Exception as e:  # noqa: BLE001
        return LifecycleSnapshot(
            phase="error",
            database_status="ready",
            errors=[str(e)[:500]],
            detail="alembic_inspect",
        )


def snapshot_progress(phase: DatabaseLifecyclePhase, snapshot: LifecycleSnapshot | None) -> LifecycleSnapshot:
    """In-progress desktop thread: build a snapshot for /health polling."""
    if snapshot is not None:
        return snapshot
    return LifecycleSnapshot(phase=phase, database_status="not_configured")


def start_desktop_lifecycle_thread(
    app: object,
    settings: Settings,
    *,
    lock: threading.Lock,
    attr_progress: str = "dlm_progress",
    attr_snapshot: str = "dlm_snapshot",
) -> None:
    """Spawn daemon thread that runs DLM and writes progress/snapshot on app.state."""

    state = app.state

    def progress_cb(snap: LifecycleSnapshot) -> None:
        with lock:
            setattr(state, attr_progress, snap)

    def work() -> None:
        try:
            final = run_desktop_lifecycle(settings, progress=progress_cb)
            with lock:
                setattr(state, attr_snapshot, final)
                setattr(state, attr_progress, None)
        except Exception as e:  # noqa: BLE001
            logger.exception("desktop DLM thread")
            final = LifecycleSnapshot(
                phase="error",
                database_status="error",
                errors=[str(e)[:500]],
            )
            with lock:
                setattr(state, attr_snapshot, final)
                setattr(state, attr_progress, None)

    with lock:
        setattr(state, attr_progress, LifecycleSnapshot(phase="checking", database_status="not_configured"))

    threading.Thread(target=work, daemon=True, name="dlm-desktop").start()
