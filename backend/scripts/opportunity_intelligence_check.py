"""Runtime check for opportunity recommendations from quote and market learning.

This check verifies that PartnerOS can convert Quote Learning and Market
Response Review records into Sales Opportunity recommendations without
automatically changing opportunity, quote, or order status.
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


def _print(label: str, ok: bool) -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")


def main() -> int:
    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.is_archived.is_(False)).order_by(Quote.updated_at.desc()).first()
        if quote is None:
            _print("quote fixture present", False)
            return 1
        quote_id = str(quote.id)
        quote_status_before = quote.status

        app = create_app()
        with TestClient(app) as client:
            login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            learning_payload = {
                "outcome_status": "revision_requested",
                "customer_feedback": "Opportunity check: lifting systems buyer needs clearer project fit.",
                "customer_objection": "Load, stability, noise, warranty, certification, and delivery wording need validation.",
                "delivery_feedback": "Delivery window must stay planned until approved.",
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
                "next_action": "Review HOSUN lifting wording before moving this opportunity forward.",
                "owner": "opportunity-intelligence-check",
                "affects_product_intelligence": True,
                "affects_market_response": True,
                "affects_opportunity": True,
                "internal_only": True,
            }
            learning = client.post(f"/api/v1/quotes/{quote_id}/learning", headers=headers, json=learning_payload)
            learning_data = learning.json().get("data", {}) if learning.status_code in {200, 201} else {}
            promoted = (
                client.post(
                    f"/api/v1/quotes/{quote_id}/learning/{learning_data.get('id')}/market-response-review",
                    headers=headers,
                )
                if learning_data.get("id")
                else None
            )

            probability_before = 67
            opportunity_payload = {
                "opportunity_name": "Runtime opportunity intelligence - HOSUN lifting systems",
                "quote_id": quote_id,
                "partner_focus": "HOSUN",
                "product_focus": [
                    "lifting systems",
                    "desk frames",
                    "desk legs",
                    "lifting columns",
                    "heavy-duty supply",
                ],
                "customer_segment": "project buyer",
                "project_size": "pilot sample project",
                "decision_stage": "quotation",
                "competition": "Alternative supplier under review; no real competitor quote is claimed.",
                "risk": "Customer-safe wording needs business owner review.",
                "probability": probability_before,
                "priority": "P1",
                "owner": "operator",
                "next_action": "Review recommendation manually before saving any change.",
                "status": "open",
            }
            created = client.post("/api/v1/growth/opportunities", headers=headers, json=opportunity_payload)
            created_data = created.json().get("data", {}) if created.status_code in {200, 201} else {}
            listed = client.get("/api/v1/growth/opportunities", headers=headers)
            list_data = listed.json().get("data", {}) if listed.status_code == 200 else {}
            listed_row = next(
                (row for row in list_data.get("opportunities", []) if row.get("id") == created_data.get("id")),
                {},
            )

        db.expire_all()
        quote_after = db.get(Quote, quote.id)
        recommendations = listed_row.get("recommendations") or created_data.get("recommendations") or []
        safety = list_data.get("safety", {})
        recommendation_safety = recommendations[0].get("safety", {}) if recommendations else {}
        checks = [
            ("learning create route", learning.status_code in {200, 201} and learning_data.get("affects_opportunity") is True),
            (
                "market response promotion route",
                promoted is not None and promoted.status_code in {200, 201} and promoted.json().get("data", {}).get("review"),
            ),
            ("opportunity create route", created.status_code in {200, 201} and created_data.get("probability") == probability_before),
            ("opportunity list route", listed.status_code == 200 and listed_row.get("id") == created_data.get("id")),
            (
                "opportunity recommendations present",
                bool(recommendations)
                and any(item.get("source_type") in {"quote_learning", "market_response"} for item in recommendations),
            ),
            (
                "recommendation is manual apply only",
                bool(recommendations) and all(item.get("manual_apply_required") is True for item in recommendations),
            ),
            (
                "opportunity probability not auto-overwritten",
                listed_row.get("probability") == probability_before and created_data.get("probability") == probability_before,
            ),
            ("quote status unchanged", quote_after is not None and quote_after.status == quote_status_before),
            ("growth route no external send", safety.get("email_sent") is False and safety.get("external_crm_connected") is False),
            (
                "recommendation safety no status mutation",
                recommendation_safety.get("opportunity_auto_updated") is False
                and recommendation_safety.get("quote_status_changed") is False
                and recommendation_safety.get("order_status_changed") is False,
            ),
            ("no staging validated", recommendation_safety.get("staging_validated") is False),
        ]
        for label, ok in checks:
            _print(label, ok)
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
