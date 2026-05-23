#!/usr/bin/env python3
"""Print masked DATABASE_URL and run connectivity + migration diagnostics (local development)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    import os

    os.chdir(BACKEND_ROOT)
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))

    from app.core.config import get_settings
    from app.core.database_lifecycle import check_database, get_migration_revisions
    from app.core.db_url_utils import mask_database_url

    env_path = BACKEND_ROOT / ".env"
    print("[env]")
    print(f"backend/.env: {'found' if env_path.is_file() else 'missing'}")

    get_settings.cache_clear()
    settings = get_settings()
    url_raw = (settings.DATABASE_URL or "").strip()
    if url_raw:
        print(f"DATABASE_URL: {mask_database_url(url_raw)}")
    else:
        print("DATABASE_URL: not configured")

    db_status, errors = check_database(settings)
    print()
    print("[result]")
    if db_status == "not_configured":
        print("Database is not configured.")
    elif db_status == "ready":
        print("Database connection: OK")
    elif db_status == "auth_failed":
        print("Authentication failed for the configured database user (wrong password or pg_hba rules).")
    elif db_status == "database_missing":
        print("The database in DATABASE_URL does not exist on the server.")
    elif db_status == "unavailable":
        print("PostgreSQL appears unreachable (host/port or server not running).")
    else:
        print(f"Database status: {db_status}")

    if errors:
        print()
        print("[errors]")
        for e in errors:
            print(f"  - {e}")

    if db_status == "ready":
        try:
            current, head, _ = get_migration_revisions(settings)
            pending = current != head
            print()
            print("[migrations]")
            print(f"  current revision: {current}")
            print(f"  head revision:    {head}")
            print(f"  migration pending: {pending}")
        except Exception as e:  # noqa: BLE001
            print()
            print("[migrations]")
            print(f"  (could not inspect Alembic: {e})")

    print()
    print("[next steps]")
    if db_status == "not_configured":
        print("  Run: python scripts/init_local_env.py")
        print("  Then edit backend/.env and re-run this script.")
    elif db_status == "auth_failed":
        print("  Verify the password in DATABASE_URL matches the role, e.g. in psql as superuser:")
        print("    ALTER USER partneros WITH PASSWORD 'your-password';")
    elif db_status == "database_missing":
        print("  Create the database, e.g. psql:")
        print("    CREATE DATABASE partneros;")
    elif db_status == "unavailable":
        print("  Start Docker DB: docker compose up -d db")
        print("  If Docker Desktop is not running, start it first, then retry.")
        print("  Confirm host/port in DATABASE_URL (default local port 5435).")
    elif db_status == "ready":
        try:
            current, head, _ = get_migration_revisions(settings)
            if current != head:
                print("  Run: python -m alembic upgrade head")
        except Exception:
            pass
        print("  Start API: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

    return 0 if db_status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
