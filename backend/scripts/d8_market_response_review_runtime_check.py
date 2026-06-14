"""Runtime check for the persisted Market Response review queue."""

from __future__ import annotations

import os
import sys
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

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import MarketResponseReview, User  # noqa: E402
from app.services.market_response_reviews import build_market_response_review_console  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        actor = db.query(User).filter(User.email == "admin@example.com").first()
        payload = build_market_response_review_console(db, actor)
        reviews = payload.get("reviews") or []
        safety = payload.get("safety") or {}
        db_count = db.query(MarketResponseReview).count()
        checks = [
            ("status", payload.get("status") == "READY_FOR_STAGING_HANDOFF"),
            ("external staging boundary", payload.get("external_staging_state") == "WAITING_FOR_REAL_STAGING_EVIDENCE"),
            ("reviews persisted", db_count >= 6 and len(reviews) >= 6),
            ("manual safety", safety.get("email_sent") is False and safety.get("external_api_called") is False),
            ("no status mutation", safety.get("quote_status_changed") is False and safety.get("order_status_changed") is False),
            ("no staging validation", safety.get("staging_validated") is False and safety.get("d9_entered") is False),
            ("lifting dimensions", any(row.get("review_dimension") == "load" for row in reviews)),
            ("JOOBOO coverage", any(row.get("partner_focus") == "JOOBOO" for row in reviews)),
            ("future partner coverage", any(row.get("partner_focus") == "future partner" for row in reviews)),
            (
                "visibility classes",
                {"customer-safe candidate", "needs validation", "internal-only", "pilot blocker"}
                & {row.get("visibility_class") for row in reviews}
                != set(),
            ),
        ]
        app = create_app()
        with TestClient(app) as client:
            login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
            token = login.json()["access_token"]
            response = client.get("/api/v1/market/response-reviews", headers={"Authorization": f"Bearer {token}"})
        checks.append(("route reviews", response.status_code == 200 and response.json()["data"]["reviews"]))
        for label, ok in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
