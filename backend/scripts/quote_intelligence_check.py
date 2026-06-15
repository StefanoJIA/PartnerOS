"""Runtime check for Quote Intelligence learning records.

The check records internal quote learning through the local API and verifies
that no quote/order status is automatically changed and no external action is
claimed.
"""

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
from app.models import Quote  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.is_archived.is_(False)).order_by(Quote.updated_at.desc()).first()
        if quote is None:
            print("[FAIL] quote fixture present")
            return 1
        quote_id = str(quote.id)
        status_before = quote.status

        app = create_app()
        with TestClient(app) as client:
            login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "outcome_status": "revision_requested",
                "customer_feedback": "Runtime check: customer asked for clearer lifting system fit and project delivery assumptions.",
                "customer_objection": "Needs validation for load, stability, noise, warranty, certification, and delivery wording.",
                "competitor_signal": "Alternative supplier under review; no real competitor quote is claimed.",
                "price_feedback": "Customer asked for value explanation before next manual quote revision.",
                "delivery_feedback": "Delivery window needs customer-safe planned wording.",
                "product_dimensions": [
                    "load",
                    "stability",
                    "noise",
                    "delivery",
                    "installation",
                    "after-sales",
                    "packaging",
                    "warranty",
                    "test cycle",
                    "certification",
                    "project demand",
                ],
                "next_action": "Update quote wording manually and decide whether this becomes a Market Response review.",
                "owner": "runtime-check",
                "affects_product_intelligence": True,
                "affects_market_response": True,
                "affects_opportunity": True,
                "internal_only": True,
            }
            created = client.post(f"/api/v1/quotes/{quote_id}/learning", headers=headers, json=payload)
            created_data = created.json().get("data", {}) if created.status_code in {200, 201} else {}
            patched = client.patch(
                f"/api/v1/quotes/{quote_id}/learning/{created_data.get('id')}",
                headers=headers,
                json={
                    "outcome_status": "on_hold",
                    "next_action": "Wait for business owner wording before customer-visible revision.",
                },
            ) if created_data.get("id") else None
            listed = client.get(f"/api/v1/quotes/{quote_id}/learning", headers=headers)
            detail = client.get(f"/api/v1/quotes/{quote_id}", headers=headers)
            promoted = client.post(
                f"/api/v1/quotes/{quote_id}/learning/{created_data.get('id')}/market-response-review",
                headers=headers,
            ) if created_data.get("id") else None
            dashboard = client.get("/api/dashboard/business-execution", headers=headers)

        db.expire_all()
        quote_after = db.get(Quote, quote.id)
        promoted_data = promoted.json().get("data", {}) if promoted is not None and promoted.status_code in {200, 201} else {}
        promoted_review = promoted_data.get("review", {})
        checks = [
            ("quote fixture present", bool(quote_id)),
            ("learning create route", created.status_code in {200, 201} and created_data.get("outcome_status") == "revision_requested"),
            ("learning patch route", patched is not None and patched.status_code == 200 and patched.json().get("data", {}).get("outcome_status") == "on_hold"),
            ("learning list route", listed.status_code == 200 and listed.json().get("data", {}).get("total", 0) >= 1),
            ("learning safety no send", created_data.get("safety", {}).get("external_message_sent") is False),
            ("learning safety no quote status change", created_data.get("safety", {}).get("quote_status_changed") is False),
            ("learning safety no order status change", created_data.get("safety", {}).get("order_status_changed") is False),
            ("quote status unchanged", quote_after is not None and quote_after.status == status_before),
            ("quote detail exposes latest learning", detail.status_code == 200 and detail.json().get("data", {}).get("latest_learning")),
            ("learning promotion route", promoted is not None and promoted.status_code in {200, 201} and promoted_review),
            (
                "learning promotion safety",
                promoted_data.get("safety", {}).get("external_message_sent") is False
                and promoted_data.get("safety", {}).get("quote_status_changed") is False
                and promoted_data.get("safety", {}).get("order_status_changed") is False,
            ),
            (
                "business execution quote learning",
                dashboard.status_code == 200
                and any("learning" in item.get("learning_signal", "").lower() for item in dashboard.json().get("quotations", [])),
            ),
            (
                "business execution product signal",
                dashboard.status_code == 200
                and any(
                    item.get("partner_focus") == promoted_review.get("partner_focus")
                    and promoted_review.get("review_dimension") in item.get("dimensions", [])
                    for item in dashboard.json().get("products", [])
                ),
            ),
            ("status boundary", dashboard.json().get("summary", {}).get("status") == "READY_FOR_STAGING_HANDOFF"),
            ("no staging validated", dashboard.json().get("safety", {}).get("staging_validated") is False),
        ]
        for label, ok in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
