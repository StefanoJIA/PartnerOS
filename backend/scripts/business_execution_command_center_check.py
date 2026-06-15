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
        lifecycle_stages = {item.lifecycle_stage for item in payload.lifecycle}
        lifecycle_sources = {item.source_type for item in payload.lifecycle}
        lifecycle_impacts = {impact for item in payload.lifecycle for impact in item.readiness_impact}
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
                "lifecycle covers opportunity and quotation objects",
                {"Opportunity", "Quotation"} & lifecycle_stages
                and {"opportunity", "quote"} & lifecycle_sources,
            ),
            (
                "lifecycle includes feedback or repeat-business signal",
                bool({"feedback", "order"} & lifecycle_sources)
                and bool({"after-sales", "repeat business", "market response"} & lifecycle_impacts),
            ),
            (
                "lifecycle has action metadata",
                all(item.source_type and item.source_id and item.stage_order > 0 and item.priority for item in payload.lifecycle),
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
            opp_list_before = client.get("/api/v1/growth/opportunities", headers={"Authorization": f"Bearer {token}"})
            opp_payload = {
                "opportunity_name": "Runtime pipeline check - lifting systems project",
                "partner_focus": "HOSUN",
                "product_focus": ["lifting systems", "desk frames", "desk legs", "lifting columns", "heavy-duty solutions"],
                "customer_segment": "project buyer",
                "project_size": "mid-size project",
                "estimated_value": "25000.00",
                "decision_stage": "quotation",
                "competition": "Alternative supplier under review; record real competitor only after business input.",
                "risk": "Needs validation for load, noise, warranty, certification, delivery, and installation wording.",
                "probability": 67,
                "priority": "P1",
                "owner": "runtime-check",
                "next_action": "Confirm quote inputs and customer-safe technical wording.",
                "status": "open",
            }
            created = client.post("/api/v1/growth/opportunities", headers={"Authorization": f"Bearer {token}"}, json=opp_payload)
            created_data = created.json().get("data", {}) if created.status_code in {200, 201} else {}
            patched = client.patch(
                f"/api/v1/growth/opportunities/{created_data.get('id')}",
                headers={"Authorization": f"Bearer {token}"},
                json={"decision_stage": "negotiation", "probability": 72},
            ) if created_data.get("id") else None
            opp_list_after = client.get("/api/v1/growth/opportunities", headers={"Authorization": f"Bearer {token}"})
            response = client.get("/api/dashboard/business-execution", headers={"Authorization": f"Bearer {token}"})
        response_data = response.json() if response.status_code == 200 else {}
        checks.append(("route business execution", response.status_code == 200 and response_data.get("executive_decisions")))
        checks.append(("route safety flags", response_data.get("safety", {}).get("staging_validated") is False))
        checks.append(("route no external send", response_data.get("safety", {}).get("external_message_sent") is False))
        checks.append(("route opportunity list", opp_list_before.status_code == 200 and "opportunities" in opp_list_before.json().get("data", {})))
        checks.append(("route opportunity create", created.status_code in {200, 201} and created_data.get("probability") == 67))
        checks.append(("route opportunity patch", patched is not None and patched.status_code == 200 and patched.json().get("data", {}).get("probability") == 72))
        checks.append(("route opportunity safety", opp_list_after.json().get("data", {}).get("safety", {}).get("email_sent") is False))
        checks.append(
            (
                "business execution uses opportunity records",
                any(item.get("id") == created_data.get("id") for item in response_data.get("opportunities", [])),
            )
        )

        for label, ok in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
