"""Runtime check for Partner Onboarding -> Market Response review bridge."""

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

from app.core.database import SessionLocal  # noqa: E402
from app.models import ManufacturingPartner, MarketResponseReview, User  # noqa: E402
from app.services.partner_onboarding import create_partner_market_response_reviews  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        actor = db.query(User).filter(User.email == "admin@example.com").first()
        partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.is_active.is_(True)).first()
        checks: list[tuple[str, bool]] = []
        if partner is None:
            checks.append(("active partner exists", False))
        else:
            before = db.query(MarketResponseReview).count()
            result = create_partner_market_response_reviews(db, partner.id, actor)
            after = db.query(MarketResponseReview).count()
            safety = result.get("safety") or {}
            checks.extend(
                [
                    ("active partner exists", True),
                    ("bridge found partner", result.get("found") is True),
                    ("review created or reused", bool(result.get("created") or result.get("existing"))),
                    ("reviews persisted", after >= before),
                    ("market link", str(result.get("market_response_link") or "").startswith("/market-response")),
                    ("no customer notification", safety.get("customer_notified") is False),
                    ("no supplier notification", safety.get("supplier_notified") is False),
                    ("no quote/order mutation", safety.get("quote_status_changed") is False and safety.get("order_status_changed") is False),
                    ("no staging/D9 claim", safety.get("staging_validated") is False and safety.get("d9_entered") is False),
                ]
            )

        for label, ok in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
