"""Runtime check for the persistent External Execution workspace."""

from __future__ import annotations

import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_database_url() -> None:
    if os.getenv("DATABASE_URL"):
        return
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "DATABASE_URL":
            os.environ["DATABASE_URL"] = value.strip().strip('"').strip("'")
            return


_load_database_url()

from app.core.database import SessionLocal  # noqa: E402
from app.models import ExternalExecutionAction, User  # noqa: E402
from app.services.external_execution import build_external_execution_console  # noqa: E402
from app.main import create_app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        actor = db.query(User).filter(User.email == "admin@example.com").first()
        payload = build_external_execution_console(db, actor)
        actions = payload.get("actions") or []
        safety = payload.get("safety") or {}
        db_count = db.query(ExternalExecutionAction).count()
        checks = [
            ("status", payload.get("status") == "READY_FOR_STAGING_HANDOFF"),
            ("external staging boundary", payload.get("external_staging_state") == "WAITING_FOR_REAL_STAGING_EVIDENCE"),
            ("actions persisted", db_count >= 5 and len(actions) >= 5),
            ("manual safety", safety.get("email_sent") is False and safety.get("external_api_called") is False),
            ("no staging validation", safety.get("staging_validated") is False and safety.get("d9_entered") is False),
            ("lifting systems field review", any(row.get("field") == "load" for row in payload.get("lifting_systems_field_review") or [])),
            ("multi partner coverage", any(row.get("partner") == "JOOBOO" for row in payload.get("partner_coverage") or [])),
        ]
        app = create_app()
        with TestClient(app) as client:
            login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
            token = login.json()["access_token"]
            response = client.get("/api/v1/external-execution/console", headers={"Authorization": f"Bearer {token}"})
        checks.append(("route console", response.status_code == 200 and response.json()["data"]["actions"]))
        for label, ok in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
