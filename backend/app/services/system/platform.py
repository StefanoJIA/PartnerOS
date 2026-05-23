"""Platform readiness / doctor / manifest builders (no secrets in output)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.database_lifecycle import check_database, get_migration_revisions, inspect_lifecycle_dev
from app.core.db_url_utils import mask_database_url
from app.core.version import APP_VERSION

API_VERSION = "v1"
SERVICE_ID = "intellioffice"


def _storage_path(settings: Settings) -> Path:
    raw = (settings.LOCAL_STORAGE_PATH or settings.UPLOAD_DIR or "./uploads").strip()
    return Path(raw)


def build_readiness_payload(settings: Settings) -> dict[str, Any]:
    """Reuse DLM + Alembic; optional deps may be false with warnings (non-blocking MVP)."""
    warnings: list[str] = []

    db_status, db_errors = check_database(settings)
    database_ready = db_status == "ready"
    database_at_head = False
    current_rev: str | None = None
    head_rev: str | None = None

    if not database_ready:
        if db_errors:
            warnings.extend(db_errors[:3])
        else:
            warnings.append(f"database_status={db_status}")
    else:
        try:
            current_rev, head_rev, _ = get_migration_revisions(settings)
            database_at_head = current_rev == head_rev
            if not database_at_head:
                warnings.append(
                    f"Schema migration pending (current={current_rev}, head={head_rev}). "
                    "Run: alembic upgrade head"
                )
        except Exception as e:  # noqa: BLE001
            warnings.append(f"Could not inspect Alembic revisions: {str(e)[:200]}")
            database_at_head = False

    redis_ready = False
    redis_url = (getattr(settings, "REDIS_URL", None) or "").strip()
    if redis_url:
        warnings.append("REDIS_URL is set but Redis ping is not implemented in Phase 1.")
    else:
        warnings.append("REDIS_URL not configured; redis_ready=false (optional for MVP).")

    storage_ready = False
    storage_path = _storage_path(settings)
    try:
        storage_path.mkdir(parents=True, exist_ok=True)
        probe = storage_path / ".readiness_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        storage_ready = True
    except OSError as e:
        warnings.append(f"Local storage not writable at {storage_path}: {e}")

    auth_ready = bool((settings.SECRET_KEY or "").strip())
    if auth_ready and settings.SECRET_KEY == "dev-secret-change-in-production":
        warnings.append("SECRET_KEY is still the development default; rotate for production.")

    worker_ready = False
    warnings.append("Background worker not configured in Phase 1; worker_ready=false.")

    # MVP: core DB + auth sufficient for ok=true; optional deps only add warnings.
    ok = database_ready and database_at_head and auth_ready

    return {
        "ok": ok,
        "service": SERVICE_ID,
        "database_ready": database_ready,
        "database_at_head": database_at_head,
        "redis_ready": redis_ready,
        "storage_ready": storage_ready,
        "auth_ready": auth_ready,
        "worker_ready": worker_ready,
        "warnings": warnings,
        "database_status": db_status,
        "alembic_current_revision": current_rev,
        "alembic_head_revision": head_rev,
    }


def build_doctor_payload(
    settings: Settings,
    *,
    started_at: str | None = None,
) -> dict[str, Any]:
    """Sanitized diagnostics for operators / Portal (no passwords or tokens)."""
    db_status, db_errors = check_database(settings)
    current_rev: str | None = None
    head_rev: str | None = None
    migration_pending = False

    if db_status == "ready":
        try:
            current_rev, head_rev, _ = get_migration_revisions(settings)
            migration_pending = current_rev != head_rev
        except Exception as e:  # noqa: BLE001
            db_errors = list(db_errors) + [str(e)[:200]]

    dlm = inspect_lifecycle_dev(settings)
    storage_path = _storage_path(settings)
    redis_url = (getattr(settings, "REDIS_URL", None) or "").strip()

    return {
        "ok": db_status == "ready" and not migration_pending,
        "runtime": {
            "mode": settings.APP_RUNTIME_MODE.value,
            "version": APP_VERSION,
            "api_version": API_VERSION,
            "app_name": getattr(settings, "APP_NAME", SERVICE_ID),
            "started_at": started_at,
            "commit": os.environ.get("GIT_COMMIT") or os.environ.get("APP_COMMIT") or None,
        },
        "database": {
            "reachable": db_status == "ready",
            "status": db_status,
            "current_revision": current_rev or dlm.alembic_current_revision,
            "head_revision": head_rev or dlm.alembic_head_revision,
            "migration_pending": migration_pending or dlm.migration_pending,
            "database_url_masked": mask_database_url(settings.DATABASE_URL),
            "errors": db_errors[:5] if db_errors else [],
        },
        "redis": {
            "reachable": False,
            "configured": bool(redis_url),
            "note": "Redis health check deferred to a later phase.",
        },
        "storage": {
            "type": getattr(settings, "STORAGE_BACKEND", "local") or "local",
            "path": str(storage_path),
            "reachable": storage_path.exists(),
            "writable": os.access(storage_path, os.W_OK) if storage_path.exists() else False,
        },
        "portal": {
            "enabled": bool(getattr(settings, "PORTAL_INTEGRATION_ENABLED", True)),
            "service_id": SERVICE_ID,
        },
        "auth": {
            "jwt_configured": bool((settings.SECRET_KEY or "").strip()),
            "secret_is_dev_default": settings.SECRET_KEY == "dev-secret-change-in-production",
        },
    }


def build_manifest_payload(settings: Settings) -> dict[str, Any]:
    public_base = (getattr(settings, "PUBLIC_BASE_URL", None) or "").strip().rstrip("/")
    health_path = "/health"
    readiness_path = "/api/v1/system/readiness"
    summary_path = "/api/v1/portal/summary"
    a_domain_status_path = "/api/v1/portal/a-domain/status"

    base_url = public_base or "http://127.0.0.1:8000"

    modules = [
        {"key": "crm", "name": "CRM", "path": "/companies", "frontend_route": "/companies"},
        {
            "key": "leads",
            "name": "Lead Intelligence",
            "path": "/leads",
            "frontend_route": "/lead-intelligence",
            "description": "Daily manual outreach queue with human-reviewed drafts (D5.2.x)",
        },
        {"key": "contacts", "name": "Contacts", "path": "/contacts", "frontend_route": "/contacts"},
        {"key": "system_health", "name": "System Health", "path": "/health", "frontend_route": "/system-health"},
        {"key": "rfq", "name": "RFQ Workspace", "path": "/rfqs", "frontend_route": "/rfqs"},
        {"key": "quotes", "name": "Quotations", "path": "/quotations", "frontend_route": "/rfqs"},
        {"key": "orders", "name": "Orders", "path": "/orders", "frontend_route": "/orders"},
        {"key": "production", "name": "Production Tracking", "path": "/orders", "frontend_route": "/orders"},
        {"key": "shipments", "name": "Shipment Tracking", "path": "/orders", "frontend_route": "/orders"},
        {"key": "tasks", "name": "Tasks", "path": "/tasks", "frontend_route": "/tasks"},
        {"key": "partners", "name": "Manufacturing Partners", "path": "/partners", "frontend_route": "/partners"},
        {"key": "products", "name": "Products", "path": "/products", "frontend_route": "/products"},
    ]

    capabilities = [
        "crm",
        "lead_scoring",
        "lead_intelligence_workbench",
        "manual_outreach_queue",
        "human_reviewed_outreach_drafts",
        "public_source_enrichment",
        "system_health",
        "rfq",
        "quotations",
        "samples",
        "orders",
        "production_milestones",
        "shipment_records",
        "tasks",
        "knowledge",
        "ai_assistant",
    ]

    return {
        "service_id": SERVICE_ID,
        "service_name": "intelliOffice",
        "description": (
            "CRM and A-domain lead intelligence with daily manual outreach rhythm. "
            "Read-only portal integration exposes system status and outreach summaries; "
            "no automatic sending or LinkedIn/Outlook automation in D5.2.x."
        ),
        "version": APP_VERSION,
        "api_version": API_VERSION,
        "runtime_mode": settings.APP_RUNTIME_MODE.value,
        "base_url": base_url,
        "health_url": f"{base_url}{health_path}",
        "readiness_url": f"{base_url}{readiness_path}",
        "summary_url": f"{base_url}{summary_path}",
        "a_domain_status_url": f"{base_url}{a_domain_status_path}",
        "legacy_api_prefix": "/api",
        "v1_api_prefix": "/api/v1",
        "portal_integration_enabled": bool(getattr(settings, "PORTAL_INTEGRATION_ENABLED", True)),
        "portal_read_only": True,
        "automatic_sending_enabled": False,
        "modules": modules,
        "capabilities": capabilities,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
