from fastapi.testclient import TestClient

from app.core.version import APP_VERSION
from app.main import app


def test_health_contract():
    with TestClient(app) as c:
        r = c.get("/health")
    assert r.status_code == 200
    data = r.json()
    required = {
        "status",
        "version",
        "runtime_mode",
        "bootstrap_status",
        "database_status",
        "database_lifecycle_phase",
        "migration_pending",
        "alembic_current_revision",
        "alembic_head_revision",
    }
    assert required <= set(data.keys())
    assert data["version"] == APP_VERSION
    assert data["status"] in ("ok", "degraded", "error")
    assert data["bootstrap_status"] in ("ready", "degraded", "error")
    assert data["database_status"] in (
        "ready",
        "unavailable",
        "not_configured",
        "error",
        "auth_failed",
        "database_missing",
    )
    assert data["runtime_mode"] in (
        "development",
        "desktop",
        "demo",
        "future_cloud",
    )
    assert data["database_lifecycle_phase"] in (
        "not_configured",
        "checking",
        "initializing",
        "migrating",
        "ready",
        "error",
    )
    assert isinstance(data["migration_pending"], bool)
