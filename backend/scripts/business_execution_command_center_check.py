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
from app.models import Company, Lead, User  # noqa: E402
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
        account_sources = {source for item in payload.account_lifecycle for source in item.source_counts}
        account_impacts = {impact for item in payload.account_lifecycle for impact in item.readiness_impact}
        account_health_items = [item.commercial_health for item in payload.account_lifecycle if item.commercial_health]
        account_stage_progression_items = [
            item.stage_progression for item in payload.account_lifecycle if item.stage_progression
        ]
        quote_commercial_items = [item.commercial_intelligence for item in payload.quotations if item.commercial_intelligence]
        quote_partner_readiness_items = [item.partner_readiness for item in payload.quotations if item.partner_readiness]
        quote_commercial_dimensions = {
            dimension
            for item in quote_commercial_items
            for dimension in item.get("dimension_review_needs", [])
        }
        fulfillment_items = [item.fulfillment_intelligence for item in payload.delivery if item.fulfillment_intelligence]
        partner_execution_items = [
            item.get("partner_execution_readiness")
            for item in fulfillment_items
            if item.get("partner_execution_readiness")
        ]
        fulfillment_impacts = {
            impact
            for item in fulfillment_items
            for impact in item.get("readiness_impact", [])
        }
        partner_capability_items = [item.capability_intelligence for item in payload.partners if item.capability_intelligence]
        partner_capability_impacts = {
            impact
            for item in partner_capability_items
            for impact in item.get("readiness_impact", [])
        }
        opportunity_partner_fit_items = [item.partner_fit for item in payload.opportunities if item.partner_fit]
        stage_gate_items = [item.stage_gate for item in payload.opportunities if item.stage_gate]
        all_stage_gate_dimensions = {
            dimension
            for gate in stage_gate_items
            for dimension in gate.get("dimension_review_needs", [])
        }
        checks = [
            ("status boundary", payload.summary.status == "READY_FOR_STAGING_HANDOFF"),
            ("external staging boundary", payload.summary.external_staging_state == "WAITING_FOR_REAL_STAGING_EVIDENCE"),
            ("customer lifecycle present", bool(payload.lifecycle)),
            ("account lifecycle present", bool(payload.account_lifecycle)),
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
                "account lifecycle aggregates source objects",
                bool({"lead", "opportunity", "quote", "order", "feedback"} & account_sources)
                and all(item.current_stage and item.next_action and item.active_paths for item in payload.account_lifecycle),
            ),
            (
                "account lifecycle carries business impact",
                bool(account_impacts)
                and all(item.decision_reason and item.priority for item in payload.account_lifecycle),
            ),
            (
                "account lifecycle exposes commercial health",
                bool(account_health_items)
                and all(
                    health.get("health")
                    and health.get("business_focus")
                    and health.get("next_best_action")
                    and isinstance(health.get("score"), int)
                    for health in account_health_items
                ),
            ),
            (
                "account commercial health links conversion delivery or repeat signals",
                any(
                    health.get("conversion_signal")
                    and health.get("delivery_signal")
                    and health.get("repeat_business_signal")
                    for health in account_health_items
                ),
            ),
            (
                "account stage progression present",
                bool(account_stage_progression_items)
                and all(
                    item.get("health")
                    and item.get("current_stage")
                    and item.get("recommended_action")
                    and item.get("handoff_object")
                    and item.get("recommended_entry_path")
                    for item in account_stage_progression_items
                ),
            ),
            (
                "account stage progression drives next lifecycle move",
                any(
                    item.get("next_stage")
                    or item.get("handoff_object") in {"repeat_business", "feedback_to_market_response"}
                    for item in account_stage_progression_items
                )
                and any(
                    item.get("missing_inputs") or item.get("health") in {"ready_to_advance", "repeat_business_ready"}
                    for item in account_stage_progression_items
                ),
            ),
            (
                "account stage progression safe boundaries",
                all(
                    item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("quote_status_changed") is False
                    and item.get("safety", {}).get("order_status_changed") is False
                    and item.get("safety", {}).get("raw_token_recorded") is False
                    and item.get("safety", {}).get("staging_validated") is False
                    for item in account_stage_progression_items
                ),
            ),
            (
                "opportunities rank probability",
                all(0 <= item.probability <= 100 for item in payload.opportunities),
            ),
            (
                "opportunities expose stage gates",
                bool(stage_gate_items)
                and all(gate.get("health") and gate.get("next_best_action") for gate in stage_gate_items)
                and any(gate.get("missing_inputs") or gate.get("health") == "ready_to_advance" for gate in stage_gate_items),
            ),
            (
                "opportunities expose partner-fit routing",
                bool(opportunity_partner_fit_items)
                and all(
                    item.get("partner_name")
                    and isinstance(item.get("fit_score"), int)
                    and item.get("next_best_action")
                    for item in opportunity_partner_fit_items
                ),
            ),
            (
                "opportunity stage gates cover product dimensions",
                bool(
                    {"load", "stability", "noise", "warranty", "test cycle", "certification"} & all_stage_gate_dimensions
                    or {"durability", "school procurement timing", "delivery consistency"} & all_stage_gate_dimensions
                    or {"product family", "quote logic", "delivery requirement"} & all_stage_gate_dimensions
                ),
            ),
            (
                "quote learning captures feedback gap",
                any("feedback" in item.learning_signal.lower() or "won" in item.outcome_signal.lower() for item in payload.quotations),
            ),
            (
                "quote commercial intelligence present",
                bool(quote_commercial_items)
                and all(
                    item.get("health")
                    and item.get("business_focus")
                    and item.get("next_best_action")
                    and isinstance(item.get("score"), int)
                    for item in quote_commercial_items
                ),
            ),
            (
                "quote commercial intelligence has safe boundaries",
                all(
                    item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("quote_status_changed") is False
                    and item.get("safety", {}).get("order_status_changed") is False
                    and item.get("customer_safe_boundary")
                    for item in quote_commercial_items
                ),
            ),
            (
                "quote commercial intelligence covers product dimensions",
                bool(
                    {"load", "stability", "noise", "warranty", "test cycle", "certification"} & quote_commercial_dimensions
                    or {"durability", "school procurement timing", "delivery consistency"} & quote_commercial_dimensions
                    or {"product family", "quote logic", "delivery requirement"} & quote_commercial_dimensions
                ),
            ),
            (
                "quote partner readiness present",
                bool(quote_partner_readiness_items)
                and all(
                    item.get("health")
                    and item.get("next_best_action")
                    and item.get("partners")
                    for item in quote_partner_readiness_items
                ),
            ),
            (
                "quote partner readiness safe boundaries",
                all(
                    item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("quote_status_changed") is False
                    and item.get("safety", {}).get("order_status_changed") is False
                    and item.get("customer_safe_boundary")
                    for item in quote_partner_readiness_items
                ),
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
                "delivery fulfillment intelligence present",
                bool(fulfillment_items)
                and all(
                    item.get("health")
                    and item.get("business_focus")
                    and item.get("next_best_action")
                    and item.get("source_quote")
                    for item in fulfillment_items
                ),
            ),
            (
                "delivery fulfillment intelligence links quote and feedback loop",
                bool({"delivery visibility risk", "repeat business risk", "commercial learning loop", "Market Response review"} & fulfillment_impacts)
                or any(item.get("quote_dimension_gaps") or item.get("quote_missing_inputs") for item in fulfillment_items),
            ),
            (
                "delivery partner execution readiness present",
                bool(partner_execution_items)
                and all(
                    item.get("health")
                    and item.get("priority")
                    and item.get("next_best_action")
                    and item.get("partners")
                    for item in partner_execution_items
                ),
            ),
            (
                "delivery partner execution readiness links order handoff",
                any(
                    partner.get("handoff_stage")
                    and (
                        partner.get("missing_execution_inputs")
                        or partner.get("risk_signals")
                        or partner.get("split_created") is True
                    )
                    for item in partner_execution_items
                    for partner in item.get("partners", [])
                ),
            ),
            (
                "delivery partner execution readiness safe boundaries",
                all(
                    item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("supplier_notified") is False
                    and item.get("safety", {}).get("customer_notified") is False
                    and item.get("safety", {}).get("order_status_changed") is False
                    and item.get("safety", {}).get("shipment_created") is False
                    and item.get("customer_safe_boundary")
                    for item in partner_execution_items
                ),
            ),
            (
                "delivery fulfillment intelligence safe boundaries",
                all(
                    item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("order_status_changed") is False
                    and item.get("safety", {}).get("shipment_created") is False
                    and item.get("customer_safe_boundary")
                    for item in fulfillment_items
                ),
            ),
            (
                "partner capability intelligence present",
                bool(partner_capability_items)
                and all(
                    item.get("health")
                    and item.get("business_focus")
                    and item.get("next_best_action")
                    and isinstance(item.get("score"), int)
                    for item in partner_capability_items
                ),
            ),
            (
                "partner capability intelligence drives investment decision",
                any(item.get("investment_priority") in {"P1", "P2", "P3"} for item in partner_capability_items)
                and bool(
                    {"quote readiness", "customer-visible resources", "delivery visibility", "pilot partner selection", "Market Response metrics"}
                    & partner_capability_impacts
                    or any(item.get("missing_inputs") or item.get("risk_signals") for item in partner_capability_items)
                ),
            ),
            (
                "partner capability intelligence safe boundaries",
                all(
                    item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("partner_notified") is False
                    and item.get("safety", {}).get("raw_token_recorded") is False
                    and item.get("customer_safe_boundary")
                    for item in partner_capability_items
                ),
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
            lead_company = db.query(Lead.company_id).filter(Lead.company_id.isnot(None), Lead.is_active.is_(True)).first()
            fallback_company = db.query(Company.id).first()
            company_id = str(lead_company[0] if lead_company else fallback_company[0]) if (lead_company or fallback_company) else None
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
            company_workspace = (
                client.get(f"/api/companies/{company_id}/workspace", headers={"Authorization": f"Bearer {token}"})
                if company_id
                else None
            )
        response_data = response.json() if response.status_code == 200 else {}
        checks.append(("route business execution", response.status_code == 200 and response_data.get("executive_decisions")))
        checks.append(("route account lifecycle", response.status_code == 200 and response_data.get("account_lifecycle")))
        checks.append(
            (
                "route account stage progression",
                response.status_code == 200
                and any(
                    item.get("stage_progression", {}).get("recommended_action")
                    for item in response_data.get("account_lifecycle", [])
                ),
            )
        )
        checks.append(
            (
                "route quote commercial intelligence",
                response.status_code == 200
                and any(
                    item.get("commercial_intelligence", {}).get("next_best_action")
                    for item in response_data.get("quotations", [])
                ),
            )
        )
        checks.append(
            (
                "route quote partner readiness",
                response.status_code == 200
                and any(
                    item.get("partner_readiness", {}).get("next_best_action")
                    and item.get("partner_readiness", {}).get("partners")
                    for item in response_data.get("quotations", [])
                ),
            )
        )
        checks.append(
            (
                "route delivery fulfillment intelligence",
                response.status_code == 200
                and any(
                    item.get("fulfillment_intelligence", {}).get("next_best_action")
                    for item in response_data.get("delivery", [])
                ),
            )
        )
        checks.append(
            (
                "route delivery partner execution readiness",
                response.status_code == 200
                and any(
                    item.get("fulfillment_intelligence", {})
                    .get("partner_execution_readiness", {})
                    .get("partners")
                    for item in response_data.get("delivery", [])
                ),
            )
        )
        checks.append(
            (
                "route partner capability intelligence",
                response.status_code == 200
                and any(
                    item.get("capability_intelligence", {}).get("next_best_action")
                    for item in response_data.get("partners", [])
                ),
            )
        )
        checks.append(("route safety flags", response_data.get("safety", {}).get("staging_validated") is False))
        checks.append(("route no external send", response_data.get("safety", {}).get("external_message_sent") is False))
        checks.append(("route opportunity list", opp_list_before.status_code == 200 and "opportunities" in opp_list_before.json().get("data", {})))
        checks.append(("route opportunity create", created.status_code in {200, 201} and created_data.get("probability") == 67))
        checks.append(
            (
                "route opportunity stage gate",
                created.status_code in {200, 201}
                and created_data.get("stage_gate", {}).get("health") in {"needs_input", "ready_to_advance", "blocked"}
                and "load" in created_data.get("stage_gate", {}).get("dimension_review_needs", []),
            )
        )
        checks.append(
            (
                "route opportunity partner-fit recommendation",
                created.status_code in {200, 201}
                and created_data.get("partner_fit", {}).get("partner_name")
                and any(
                    item.get("source_type") == "partner_fit"
                    and item.get("partner_fit", {}).get("fit_score") is not None
                    and item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("opportunity_auto_updated") is False
                    for item in created_data.get("recommendations", [])
                ),
            )
        )
        checks.append(("route opportunity patch", patched is not None and patched.status_code == 200 and patched.json().get("data", {}).get("probability") == 72))
        checks.append(("route opportunity safety", opp_list_after.json().get("data", {}).get("safety", {}).get("email_sent") is False))
        checks.append(
            (
                "business execution uses opportunity records",
                any(item.get("id") == created_data.get("id") for item in response_data.get("opportunities", [])),
            )
        )
        checks.append(
            (
                "route opportunity partner-fit reaches dashboard",
                any(
                    item.get("id") == created_data.get("id")
                    and item.get("partner_fit", {}).get("partner_name")
                    for item in response_data.get("opportunities", [])
                ),
            )
        )
        company_workspace_data = company_workspace.json() if company_workspace is not None and company_workspace.status_code == 200 else {}
        company_execution = company_workspace_data.get("business_execution", {})
        checks.append(
            (
                "company workspace execution context",
                company_workspace is not None
                and company_workspace.status_code == 200
                and bool(company_execution.get("account"))
                and bool(company_execution.get("lifecycle")),
            )
        )
        checks.append(
            (
                "company workspace commercial health",
                bool(company_execution.get("account", {}).get("commercial_health", {}).get("next_best_action")),
            )
        )
        checks.append(
            (
                "company workspace safety flags",
                company_execution.get("safety", {}).get("external_message_sent") is False
                and company_execution.get("safety", {}).get("staging_validated") is False,
            )
        )

        for label, ok in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
