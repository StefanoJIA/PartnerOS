#!/usr/bin/env python3
"""Create backend/.env from .env.example when missing (local development)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.local_env_setup import init_env_from_example  # noqa: E402


def main() -> int:
    result, msg = init_env_from_example(backend_root=BACKEND_ROOT)
    print("[init_local_env]")
    print(msg)
    if result == "missing_template":
        return 1
    if result == "error":
        return 1
    if result == "created":
        print()
        print("Next:")
        print("  1. Ensure PostgreSQL is running.")
        print("  2. Align DATABASE_URL in backend/.env with your DB user/password/database.")
        print("  3. Run: python scripts/check_database_config.py")
        print("  4. Run: python -m alembic upgrade head")
        print("  5. Run: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print()
        print("Health check: http://127.0.0.1:8000/health (root / may return Not Found — expected).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
