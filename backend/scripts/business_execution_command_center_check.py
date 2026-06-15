"""Runtime check for the Business Execution Command Center.

This local check proves that PartnerOS can derive a business execution
main chain from current internal data. It does not call real staging,
send external messages, record tokens, or mutate quote/order status.
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
from app.models import User  # noqa: E402
from app.services.business_execution import build_business_execution_center  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        actor = db.query(User).filter(User.email == "admin@example.com").first()
        if actor is None:
            print("[FAIL] admin actor")
            return 1
        payload = build_business_execution_center(db, actor)
        all_product_dimensions = {
            dimension
            for item in payload.products
            for dimension in item.dimensions
        }
        all_partner_names = {item.partner_name for item in payload.partners}
        all_partner_focus = {
            item.partner_focus
            for item in payload.opportunities
            if item.partner_focus
        } | {
            item.partner_focus
            for item in payload.products
            if item.partner_focus
        }
        checks = [
            ("status boundary", payload.summary.status == "READY_FOR_STAGING_HANDOFF"),
            ("external staging boundary", payload.summary.external_staging_state == "WAITING_FOR_REAL_STAGING_EVIDENCE"),
            ("customer lifecycle present", bool(payload.lifecycle)),
            ("opportunity pipeline present", bool(payload.opportunities)),
            ("quotation intelligence present", bool(payload.quotations)),
            ("product intelligence present", bool(payload.products)),
            ("partner intelligence present", bool(payload.partners)),
            ("delivery visibility present", bool(payload.delivery)),
            ("executive decisions present", bool(payload.executive_decisions)),
            (
                "lifecycle covers sales-to-delivery stages",
                any(item.lifecycle_stage in {"Lead", "Qualified", "Opportunity", "Quotation"} for item in payload.lifecycle)
                and any(item.lifecycle_stage in {"Order", "Production", "Delivery", "After-Sales"} for item in payload.lifecycle),
            ),
            (
                "opportunities rank probability",
                all(0 <= item.probability <= 100 for item in payload.opportunities),
            ),
            (
                "quote learning captures feedback gap",
                any("feedback" in item.learning_signal.lower() or "won" in item.outcome_signal.lower() for item in payload.quotations),
            ),
            (
                "lifting system dimensions represented",
                {"load", "stability", "noise", "warranty", "test cycle", "certification"}.issubset(all_product_dimensions),
            ),
            (
                "education furniture dimensions represented",
                bool({"durability", "procurement cycle", "delivery consistency"} & all_product_dimensions)
                or any("JOOBOO" in name for name in all_partner_names | all_partner_focus),
            ),
            (
                "future partner path represented",
                any("future partner" in (item.partner_focus or "").lower() for item in payload.opportunities)
                or any("future" in item.answer.lower() for item in payload.executive_decisions)
                or bool(payload.partners),
            ),
            (
                "manual-only safety",
                payload.safety.get("external_message_sent") is False
                and payload.safety.get("quote_status_changed") is False
                and payload.safety.get("order_status_changed") is False
                and payload.safety.get("raw_token_recorded") is False
                and payload.safety.get("staging_validated") is False
                and payload.safety.get("customer_forbidden_fields_exposed") is False,
            ),
        ]

        app = create_app()
        with TestClient(app) as client:
            login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
            token = login.json()["access_token"]
            response = client.get("/api/dashboard/business-execution", headers={"Authorization": f"Bearer {token}"})
        response_data = response.json() if response.status_code == 200 else {}
        checks.append(("route business execution", response.status_code == 200 and response_data.get("executive_decisions")))
        checks.append(("route safety flags", response_data.get("safety", {}).get("staging_validated") is False))
        checks.append(("route no external send", response_data.get("safety", {}).get("external_message_sent") is False))

        for label, ok in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
