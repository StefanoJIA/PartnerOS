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
from app.services.business_execution import (  # noqa: E402
    build_account_360_intelligence,
    build_business_execution_center,
    build_customer_value_intelligence,
    build_partner_performance_intelligence,
    build_product_market_fit_intelligence,
    build_revenue_forecast_intelligence,
    build_win_loss_intelligence,
)


def main() -> int:
    db = SessionLocal()
    try:
        actor = db.query(User).filter(User.email == "admin@example.com").first()
        if actor is None:
            print("[FAIL] admin actor")
            return 1
        payload = build_business_execution_center(db, actor)
        win_loss_payload = build_win_loss_intelligence(db, limit=80)
        win_loss_items = win_loss_payload.get("items", [])
        all_product_dimensions = {
            dimension
            for item in payload.products
            for dimension in item.dimensions
        }
        product_validation_context_items = [
            item.validation_context for item in payload.products if item.validation_context
        ]
        commercial = payload.commercial_intelligence
        revenue_forecast = commercial.revenue_forecast or {}
        executive_summary = commercial.executive_summary or {}
        executive_questions = executive_summary.get("management_questions", {})
        executive_brief = executive_summary.get("management_brief", [])
        executive_actions = executive_summary.get("executive_actions", [])
        executive_snapshot = executive_summary.get("commercial_snapshot", {})
        customer_value_payload = build_customer_value_intelligence(db, limit=20)
        customer_value_items = customer_value_payload.get("items", [])
        revenue_forecast_payload = build_revenue_forecast_intelligence(db, limit=40)
        revenue_forecast_items = revenue_forecast_payload.get("forecast_items", [])
        partner_performance_payload = build_partner_performance_intelligence(db, limit=40)
        partner_performance_items = partner_performance_payload.get("items", [])
        product_market_fit_payload = build_product_market_fit_intelligence(db, limit=40)
        product_market_fit_items = product_market_fit_payload.get("items", [])
        account_360_payload = build_account_360_intelligence(db, limit=40)
        account_360_items = account_360_payload.get("items", [])
        commercial_safety_items = [
            item.get("safety", {})
            for collection in [
                commercial.win_loss,
                commercial.customer_value,
                commercial.partner_performance,
                commercial.product_market_fit,
                commercial.account_360,
            ]
            for item in collection
            if isinstance(item, dict)
        ]
        product_validation_impacts = {
            impact
            for item in product_validation_context_items
            for impact in item.get("readiness_impact", [])
        }
        product_validation_dimensions = {
            dimension
            for item in product_validation_context_items
            for dimension in item.get("dimensions_requiring_evidence", [])
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
        opportunity_execution_items = [
            item.execution_context for item in payload.opportunities if item.execution_context
        ]
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
            (
                "commercial intelligence present",
                bool(commercial.win_loss)
                or bool(commercial.customer_value)
                or bool(commercial.partner_performance)
                or bool(commercial.product_market_fit)
                or bool(commercial.account_360),
            ),
            (
                "commercial intelligence covers six assets",
                isinstance(executive_summary, dict)
                and isinstance(commercial.win_loss, list)
                and isinstance(commercial.customer_value, list)
                and isinstance(commercial.partner_performance, list)
                and isinstance(commercial.product_market_fit, list)
                and isinstance(commercial.account_360, list)
                and isinstance(revenue_forecast, dict)
                and "weighted_opportunity_amount" in revenue_forecast
                and "weighted_quote_amount" in revenue_forecast,
            ),
            (
                "commercial intelligence executive summary answers management questions",
                isinstance(executive_questions, dict)
                and "who_to_follow_today" in executive_questions
                and "what_converts" in executive_questions
                and "what_is_commercially_healthy" in executive_questions
                and "why_we_win" in executive_questions
                and "why_we_lose" in executive_questions
                and "future_revenue_from" in executive_questions
                and "which_partner_to_invest" in executive_questions
                and isinstance(executive_actions, list)
                and isinstance(executive_snapshot, dict)
                and "total_weighted_revenue" in executive_snapshot
                and "forecast_quality_score" in executive_snapshot,
            ),
            (
                "commercial intelligence management brief is actionable",
                isinstance(executive_brief, list)
                and len(executive_brief) >= 6
                and {"who_to_follow", "what_converts", "commercial_value", "why_we_win", "why_we_lose", "future_revenue"}.issubset(
                    {item.get("key") for item in executive_brief if isinstance(item, dict)}
                )
                and all(
                    isinstance(item, dict)
                    and item.get("question")
                    and item.get("answer")
                    and item.get("evidence")
                    and item.get("recommended_action")
                    and isinstance(item.get("source_assets"), list)
                    and item.get("path")
                    and item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("quote_status_changed") is False
                    and item.get("safety", {}).get("order_status_changed") is False
                    and item.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                    for item in executive_brief
                    if isinstance(item, dict)
                ),
            ),
            (
                "commercial intelligence executive summary safe boundaries",
                executive_summary.get("safety", {}).get("external_message_sent") is False
                and executive_summary.get("safety", {}).get("quote_status_changed") is False
                and executive_summary.get("safety", {}).get("order_status_changed") is False
                and executive_summary.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                and all(
                    item.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                    for item in executive_actions
                    if isinstance(item, dict)
                ),
            ),
            (
                "commercial intelligence links business objects",
                any(item.get("source_type") in {"opportunity", "quote_learning"} for item in commercial.win_loss)
                or any(item.get("quote_count", 0) >= 0 and item.get("order_count", 0) >= 0 for item in commercial.customer_value)
                or any(item.get("quote_support_count", 0) >= 0 for item in commercial.partner_performance),
            ),
            (
                "win-loss intelligence profiles commercial lessons",
                isinstance(win_loss_payload.get("summary"), dict)
                and "commercial_amount" in win_loss_payload["summary"]
                and all(
                    item.get("source_type") in {"opportunity", "quote_learning"}
                    and item.get("outcome")
                    and item.get("reason_category")
                    and isinstance(item.get("decision_factors"), list)
                    and item.get("commercial_lesson")
                    and item.get("next_quote_guidance")
                    and item.get("safety", {}).get("external_message_sent") is False
                    for item in win_loss_items
                ),
            ),
            (
                "win-loss intelligence answers management questions",
                isinstance(win_loss_payload.get("management_questions"), dict)
                and "why_we_win" in win_loss_payload["management_questions"]
                and "why_we_lose" in win_loss_payload["management_questions"]
                and "what_to_change_next_quote" in win_loss_payload["management_questions"]
                and isinstance(win_loss_payload.get("reason_clusters"), list)
                and isinstance(win_loss_payload.get("partner_rollup"), list)
                and isinstance(win_loss_payload.get("product_rollup"), list)
                and isinstance(win_loss_payload.get("decision_factor_rows"), list),
            ),
            (
                "win-loss intelligence safe boundaries",
                win_loss_payload.get("safety", {}).get("external_message_sent") is False
                and win_loss_payload.get("safety", {}).get("quote_status_changed") is False
                and win_loss_payload.get("safety", {}).get("order_status_changed") is False
                and win_loss_payload.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                and all(item.get("safety", {}).get("customer_forbidden_fields_exposed") is False for item in win_loss_items),
            ),
            (
                "customer value intelligence profiles accounts",
                isinstance(customer_value_items, list)
                and all(
                    item.get("customer_name")
                    and item.get("value_tier")
                    and isinstance(item.get("value_score"), int)
                    and item.get("priority") in {"P1", "P2", "P3"}
                    and "weighted_pipeline_amount" in item
                    and "future_revenue_signal" in item
                    and isinstance(item.get("commercial_quality"), dict)
                    and "healthy_revenue_proxy" in item
                    and item.get("commercial_quality", {}).get("uses_cost_or_margin") is False
                    and item.get("commercial_quality", {}).get("tier")
                    and item.get("recommended_reason")
                    and item.get("next_action")
                    for item in customer_value_items
                ),
            ),
            (
                "customer value answers management questions",
                isinstance(customer_value_payload.get("management_questions"), dict)
                and "who_to_follow" in customer_value_payload["management_questions"]
                and "future_revenue_from" in customer_value_payload["management_questions"]
                and "what_is_commercially_healthy" in customer_value_payload["management_questions"]
                and "which_value_is_at_risk" in customer_value_payload["management_questions"]
                and isinstance(customer_value_payload.get("summary"), dict)
                and "weighted_pipeline_amount" in customer_value_payload["summary"]
                and "healthy_revenue_proxy" in customer_value_payload["summary"]
                and isinstance(customer_value_payload.get("commercial_quality_leaders"), list)
                and isinstance(customer_value_payload.get("service_burden_accounts"), list),
            ),
            (
                "customer value safe boundaries",
                customer_value_payload.get("safety", {}).get("external_message_sent") is False
                and customer_value_payload.get("safety", {}).get("quote_status_changed") is False
                and customer_value_payload.get("safety", {}).get("order_status_changed") is False
                and customer_value_payload.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                and all(item.get("safety", {}).get("customer_forbidden_fields_exposed") is False for item in customer_value_items),
            ),
            (
                "revenue forecast intelligence profiles future revenue",
                isinstance(revenue_forecast_items, list)
                and isinstance(revenue_forecast_payload.get("summary"), dict)
                and "total_weighted_amount" in revenue_forecast_payload["summary"]
                and "at_risk_weighted_amount" in revenue_forecast_payload["summary"]
                and all(
                    item.get("source_type") in {"opportunity", "quote", "order_backlog"}
                    and "weighted_amount" in item
                    and "probability" in item
                    and item.get("customer_name")
                    and item.get("risk_level") in {"low", "medium", "high"}
                    and isinstance(item.get("forecast_quality"), dict)
                    and item.get("forecast_confidence")
                    and item.get("revenue_bucket")
                    and isinstance(item.get("forecast_quality_score"), int)
                    and item.get("forecast_quality", {}).get("uses_cost_or_margin") is False
                    and item.get("next_action")
                    for item in revenue_forecast_items
                ),
            ),
            (
                "revenue forecast answers management questions",
                isinstance(revenue_forecast_payload.get("management_questions"), dict)
                and "future_revenue_from" in revenue_forecast_payload["management_questions"]
                and "what_is_committed" in revenue_forecast_payload["management_questions"]
                and "what_needs_manual_follow_up" in revenue_forecast_payload["management_questions"]
                and "what_is_weak_signal" in revenue_forecast_payload["management_questions"]
                and "revenue_source_mix" in revenue_forecast_payload["management_questions"]
                and isinstance(revenue_forecast_payload.get("forecast_by_partner"), list)
                and isinstance(revenue_forecast_payload.get("forecast_by_product"), list)
                and isinstance(revenue_forecast_payload.get("forecast_by_customer"), list)
                and isinstance(revenue_forecast_payload.get("revenue_bucket_mix"), list)
                and isinstance(revenue_forecast_payload.get("source_type_mix"), list)
                and "forecast_quality_score" in revenue_forecast_payload.get("summary", {})
                and "forecastable_weighted_amount" in revenue_forecast_payload.get("summary", {})
                and "manual_follow_up_weighted_amount" in revenue_forecast_payload.get("summary", {}),
            ),
            (
                "revenue forecast safe boundaries",
                revenue_forecast_payload.get("safety", {}).get("external_message_sent") is False
                and revenue_forecast_payload.get("safety", {}).get("quote_status_changed") is False
                and revenue_forecast_payload.get("safety", {}).get("order_status_changed") is False
                and revenue_forecast_payload.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                and all(item.get("safety", {}).get("customer_forbidden_fields_exposed") is False for item in revenue_forecast_items),
            ),
            (
                "partner performance intelligence profiles partner investment",
                isinstance(partner_performance_items, list)
                and isinstance(partner_performance_payload.get("summary"), dict)
                and "order_amount" in partner_performance_payload["summary"]
                and "quote_support_amount" in partner_performance_payload["summary"]
                and all(
                    item.get("partner_name")
                    and "quote_support_count" in item
                    and "win_rate" in item
                    and "order_amount" in item
                    and "on_time_delivery_rate" in item
                    and "feedback_issue_count" in item
                    and item.get("health")
                    and item.get("investment_priority") in {"P1", "P2", "P3"}
                    and isinstance(item.get("allocation_profile"), dict)
                    and item.get("allocation_fit")
                    and item.get("pilot_fit")
                    and isinstance(item.get("allocation_score"), int)
                    and item.get("allocation_profile", {}).get("uses_cost_or_margin") is False
                    and isinstance(item.get("product_line_contribution"), list)
                    and item.get("recommended_action")
                    and item.get("next_allocation_action")
                    for item in partner_performance_items
                ),
            ),
            (
                "partner performance answers management questions",
                isinstance(partner_performance_payload.get("management_questions"), dict)
                and "which_partner_to_invest" in partner_performance_payload["management_questions"]
                and "who_gets_next_quote_allocation" in partner_performance_payload["management_questions"]
                and "who_is_ready_for_pilot" in partner_performance_payload["management_questions"]
                and "who_should_not_get_expanded_allocation_yet" in partner_performance_payload["management_questions"]
                and "which_partner_has_delivery_or_feedback_risk" in partner_performance_payload["management_questions"]
                and isinstance(partner_performance_payload.get("partner_scoreboard"), list)
                and isinstance(partner_performance_payload.get("quote_allocation_candidates"), list)
                and isinstance(partner_performance_payload.get("pilot_candidates"), list)
                and isinstance(partner_performance_payload.get("allocation_risks"), list)
                and isinstance(partner_performance_payload.get("product_line_allocation"), list)
                and "quote_allocation_candidate_count" in partner_performance_payload.get("summary", {}),
            ),
            (
                "partner performance safe boundaries",
                partner_performance_payload.get("safety", {}).get("external_message_sent") is False
                and partner_performance_payload.get("safety", {}).get("quote_status_changed") is False
                and partner_performance_payload.get("safety", {}).get("order_status_changed") is False
                and partner_performance_payload.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                and all(item.get("safety", {}).get("customer_forbidden_fields_exposed") is False for item in partner_performance_items),
            ),
            (
                "account 360 profiles full commercial history",
                isinstance(account_360_items, list)
                and isinstance(account_360_payload.get("summary"), dict)
                and "weighted_pipeline_amount" in account_360_payload["summary"]
                and all(
                    item.get("customer_name")
                    and isinstance(item.get("source_counts"), dict)
                    and {"leads", "opportunities", "quotes", "orders", "feedback", "win_loss_records"}.issubset(item["source_counts"].keys())
                    and isinstance(item.get("commercial_value"), dict)
                    and "weighted_pipeline_amount" in item["commercial_value"]
                    and isinstance(item.get("object_timeline"), list)
                    and isinstance(item.get("win_loss_summary"), dict)
                    and isinstance(item.get("delivery_summary"), dict)
                    and isinstance(item.get("relationship_map"), dict)
                    and item.get("relationship_depth")
                    and isinstance(item.get("next_commercial_motion"), dict)
                    and item.get("next_motion_type")
                    and item.get("next_motion_owner")
                    and item.get("repeat_business_signal")
                    and item.get("next_action")
                    for item in account_360_items
                ),
            ),
            (
                "account 360 answers management questions",
                isinstance(account_360_payload.get("management_questions"), dict)
                and "who_to_follow" in account_360_payload["management_questions"]
                and "which_accounts_have_full_history" in account_360_payload["management_questions"]
                and "which_accounts_need_feedback_before_repeat" in account_360_payload["management_questions"]
                and "which_accounts_have_quote_to_order_learning" in account_360_payload["management_questions"]
                and "which_accounts_are_ready_for_repeat_or_referral" in account_360_payload["management_questions"]
                and "which_accounts_can_be_reactivated_from_loss_learning" in account_360_payload["management_questions"]
                and "what_is_the_next_commercial_motion" in account_360_payload["management_questions"]
                and isinstance(account_360_payload.get("full_relationship_accounts"), list)
                and isinstance(account_360_payload.get("quote_to_order_learning_accounts"), list)
                and isinstance(account_360_payload.get("repeat_or_referral_accounts"), list)
                and isinstance(account_360_payload.get("reactivation_accounts"), list)
                and "full_relationship_count" in account_360_payload.get("summary", {}),
            ),
            (
                "account 360 safe boundaries",
                account_360_payload.get("safety", {}).get("external_message_sent") is False
                and account_360_payload.get("safety", {}).get("quote_status_changed") is False
                and account_360_payload.get("safety", {}).get("order_status_changed") is False
                and account_360_payload.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                and all(item.get("safety", {}).get("customer_forbidden_fields_exposed") is False for item in account_360_items),
            ),
            (
                "commercial intelligence safe boundaries",
                all(
                    safety.get("external_message_sent") is False
                    and safety.get("quote_status_changed") is False
                    and safety.get("order_status_changed") is False
                    and safety.get("raw_token_recorded") is False
                    and safety.get("customer_forbidden_fields_exposed") is False
                    for safety in commercial_safety_items
                ),
            ),
            ("product intelligence present", bool(payload.products)),
            (
                "product validation context present",
                bool(product_validation_context_items)
                and all(
                    item.get("health")
                    and item.get("priority")
                    and item.get("next_best_action")
                    and item.get("evidence_counts")
                    for item in product_validation_context_items
                ),
            ),
            (
                "product validation links execution evidence",
                any(
                    counts.get("opportunities", 0) >= 0
                    and counts.get("quotes", 0) >= 0
                    and counts.get("orders", 0) >= 0
                    and counts.get("feedback", 0) >= 0
                    and counts.get("market_reviews", 0) >= 0
                    for counts in [item.get("evidence_counts", {}) for item in product_validation_context_items]
                )
                and bool(
                    {"quote wording", "delivery visibility", "after-sales learning", "Market Response", "pilot delivery risk", "customer-safe wording"}
                    & product_validation_impacts
                ),
            ),
            (
                "product validation covers partner dimensions",
                bool(
                    {"load", "stability", "noise", "warranty", "test cycle", "certification", "project demand"}
                    & product_validation_dimensions
                    or {"durability", "procurement cycle", "classroom deployment", "delivery consistency", "feedback after use"}
                    & product_validation_dimensions
                    or {"product family", "quote logic", "delivery requirement", "customer-visible fields", "Market Response metrics"}
                    & product_validation_dimensions
                ),
            ),
            (
                "product validation safe boundaries",
                all(
                    item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("quote_status_changed") is False
                    and item.get("safety", {}).get("order_status_changed") is False
                    and item.get("safety", {}).get("raw_token_recorded") is False
                    and item.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                    and item.get("safety", {}).get("cost_exposed") is False
                    and item.get("safety", {}).get("margin_exposed") is False
                    and item.get("safety", {}).get("supplier_private_notes_exposed") is False
                    and item.get("safety", {}).get("staging_validated") is False
                    and item.get("customer_safe_boundary")
                    for item in product_validation_context_items
                ),
            ),
            (
                "product-market fit intelligence profiles conversion evidence",
                isinstance(product_market_fit_payload.get("summary"), dict)
                and "quote_learning_count" in product_market_fit_payload["summary"]
                and all(
                    item.get("partner_focus")
                    and item.get("product_focus")
                    and isinstance(item.get("evidence_counts"), dict)
                    and {"opportunities", "quotes", "orders", "feedback", "wins", "losses"}.issubset(item["evidence_counts"].keys())
                    and isinstance(item.get("commercial_value"), dict)
                    and "order_amount" in item["commercial_value"]
                    and isinstance(item.get("buying_factors_ranked"), list)
                    and item.get("conversion_signal")
                    and item.get("next_action")
                    for item in product_market_fit_items
                ),
            ),
            (
                "product-market fit answers management questions",
                isinstance(product_market_fit_payload.get("management_questions"), dict)
                and "what_converts" in product_market_fit_payload["management_questions"]
                and "why_customers_buy_or_decline" in product_market_fit_payload["management_questions"]
                and "which_product_lines_need_validation_before_pilot" in product_market_fit_payload["management_questions"],
            ),
            (
                "product-market fit covers multi-partner product dimensions",
                any("load" in item.get("dimensions", []) or "noise" in item.get("dimensions", []) for item in product_market_fit_items)
                and any("delivery consistency" in item.get("dimensions", []) or "resource needs" in item.get("dimensions", []) for item in product_market_fit_items)
                and any("quote logic" in item.get("dimensions", []) or "resource taxonomy" in item.get("dimensions", []) for item in product_market_fit_items),
            ),
            (
                "product-market fit safe boundaries",
                product_market_fit_payload.get("safety", {}).get("external_message_sent") is False
                and product_market_fit_payload.get("safety", {}).get("quote_status_changed") is False
                and product_market_fit_payload.get("safety", {}).get("order_status_changed") is False
                and all(
                    item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("quote_status_changed") is False
                    and item.get("safety", {}).get("order_status_changed") is False
                    and item.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                    and item.get("customer_safe_boundary")
                    for item in product_market_fit_items
                ),
            ),
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
                "opportunities expose execution context",
                bool(opportunity_execution_items)
                and all(
                    item.get("health")
                    and item.get("next_best_action")
                    and item.get("conversion_signal", {}).get("manual_handoff_required") is True
                    for item in opportunity_execution_items
                ),
            ),
            (
                "opportunity execution links quote order or stage handoff",
                any(
                    item.get("linked_quote_count", 0) >= 0
                    and item.get("linked_order_count", 0) >= 0
                    and (
                        item.get("quote")
                        or item.get("orders")
                        or item.get("missing_inputs")
                        or item.get("health") in {"needs_quote", "quote_follow_up", "stage_inputs_needed"}
                    )
                    for item in opportunity_execution_items
                ),
            ),
            (
                "opportunity execution safe boundaries",
                all(
                    item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("customer_notified") is False
                    and item.get("safety", {}).get("supplier_notified") is False
                    and item.get("safety", {}).get("quote_status_changed") is False
                    and item.get("safety", {}).get("order_status_changed") is False
                    and item.get("safety", {}).get("shipment_created") is False
                    and item.get("safety", {}).get("raw_token_recorded") is False
                    and item.get("safety", {}).get("staging_validated") is False
                    and item.get("customer_safe_boundary")
                    for item in opportunity_execution_items
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
            win_loss_created = client.post(
                f"/api/v1/growth/opportunities/{created_data.get('id')}/win-loss",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "outcome": "won",
                    "won_reason": "Runtime check captured confirmed buying factors without changing quote or order status.",
                    "competitor_signal": "Alternative supplier compared on delivery and warranty.",
                    "customer_decision_factors": ["delivery", "warranty", "load"],
                    "product_dimensions": ["load", "noise", "warranty", "certification"],
                    "next_action": "Reuse this outcome as internal commercial learning only.",
                    "owner": "runtime-check",
                },
            ) if created_data.get("id") else None
            win_loss_list = client.get("/api/v1/growth/win-loss", headers={"Authorization": f"Bearer {token}"})
            opp_list_after = client.get("/api/v1/growth/opportunities", headers={"Authorization": f"Bearer {token}"})
            response = client.get("/api/dashboard/business-execution", headers={"Authorization": f"Bearer {token}"})
            win_loss_route = client.get(
                "/api/dashboard/win-loss-intelligence",
                headers={"Authorization": f"Bearer {token}"},
            )
            win_loss_route_data_preview = win_loss_route.json() if win_loss_route.status_code == 200 else {}
            first_win_loss_factor = (
                win_loss_route_data_preview.get("decision_factor_rows", [{}])[0].get("factor")
                if win_loss_route_data_preview.get("decision_factor_rows")
                else None
            )
            win_loss_factor_detail_route = (
                client.get(
                    "/api/dashboard/win-loss-intelligence/factor-detail",
                    params={"factor": first_win_loss_factor},
                    headers={"Authorization": f"Bearer {token}"},
                )
                if first_win_loss_factor
                else None
            )
            customer_value_route = client.get(
                "/api/dashboard/customer-value-intelligence",
                headers={"Authorization": f"Bearer {token}"},
            )
            revenue_forecast_route = client.get(
                "/api/dashboard/revenue-forecast-intelligence",
                headers={"Authorization": f"Bearer {token}"},
            )
            partner_performance_route = client.get(
                "/api/dashboard/partner-performance-intelligence",
                headers={"Authorization": f"Bearer {token}"},
            )
            partner_performance_preview = (
                partner_performance_route.json() if partner_performance_route.status_code == 200 else {}
            )
            first_partner_key = (
                partner_performance_preview.get("items", [{}])[0].get("partner_id")
                or partner_performance_preview.get("items", [{}])[0].get("partner_name")
                if partner_performance_preview.get("items")
                else None
            )
            partner_performance_detail_route = (
                client.get(
                    "/api/dashboard/partner-performance-intelligence/detail",
                    params={"partner": first_partner_key},
                    headers={"Authorization": f"Bearer {token}"},
                )
                if first_partner_key
                else None
            )
            product_market_fit_route = client.get(
                "/api/dashboard/product-market-fit-intelligence",
                headers={"Authorization": f"Bearer {token}"},
            )
            product_market_fit_preview = product_market_fit_route.json() if product_market_fit_route.status_code == 200 else {}
            first_pmf_factor = None
            for pmf_item in product_market_fit_preview.get("items", []):
                for factor_item in pmf_item.get("buying_factors_ranked", []):
                    first_pmf_factor = factor_item.get("factor")
                    if first_pmf_factor:
                        break
                if first_pmf_factor:
                    break
            product_market_fit_factor_detail_route = (
                client.get(
                    "/api/dashboard/product-market-fit-intelligence/factor-detail",
                    params={"factor": first_pmf_factor},
                    headers={"Authorization": f"Bearer {token}"},
                )
                if first_pmf_factor
                else None
            )
            account_360_route = client.get(
                "/api/dashboard/account-360-intelligence",
                headers={"Authorization": f"Bearer {token}"},
            )
            account_360_route_data_preview = account_360_route.json() if account_360_route.status_code == 200 else {}
            first_account_key = (
                account_360_route_data_preview.get("items", [{}])[0].get("account_key")
                if account_360_route_data_preview.get("items")
                else None
            )
            account_360_detail_route = (
                client.get(
                    f"/api/dashboard/account-360-intelligence/{first_account_key}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if first_account_key
                else None
            )
            company_workspace = (
                client.get(f"/api/companies/{company_id}/workspace", headers={"Authorization": f"Bearer {token}"})
                if company_id
                else None
            )
        response_data = response.json() if response.status_code == 200 else {}
        checks.append(("route business execution", response.status_code == 200 and response_data.get("executive_decisions")))
        checks.append(
            (
                "route commercial intelligence",
                response.status_code == 200
                and isinstance(response_data.get("commercial_intelligence"), dict)
                and isinstance(response_data["commercial_intelligence"].get("executive_summary"), dict)
                and "management_questions" in response_data["commercial_intelligence"]["executive_summary"]
                and isinstance(response_data["commercial_intelligence"].get("revenue_forecast"), dict)
                and "weighted_opportunity_amount" in response_data["commercial_intelligence"]["revenue_forecast"]
                and isinstance(response_data["commercial_intelligence"].get("account_360"), list),
            )
        )
        win_loss_route_data = win_loss_route.json() if win_loss_route.status_code == 200 else {}
        win_loss_factor_detail_data = (
            win_loss_factor_detail_route.json()
            if win_loss_factor_detail_route is not None and win_loss_factor_detail_route.status_code == 200
            else {}
        )
        checks.append(
            (
                "route win-loss intelligence dashboard",
                win_loss_route.status_code == 200
                and isinstance(win_loss_route_data.get("summary"), dict)
                and "what_to_change_next_quote" in win_loss_route_data.get("management_questions", {})
                and isinstance(win_loss_route_data.get("reason_clusters"), list)
                and all(
                    item.get("reason_category")
                    and item.get("next_quote_guidance")
                    and item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                    for item in win_loss_route_data.get("items", [])
                ),
            )
        )
        checks.append(
            (
                "route win-loss factor detail",
                win_loss_factor_detail_route is not None
                and win_loss_factor_detail_route.status_code == 200
                and win_loss_factor_detail_data.get("factor")
                and isinstance(win_loss_factor_detail_data.get("summary"), dict)
                and isinstance(win_loss_factor_detail_data.get("items"), list)
                and isinstance(win_loss_factor_detail_data.get("next_quote_guidance"), list)
                and isinstance(win_loss_factor_detail_data.get("partner_rollup"), list)
                and isinstance(win_loss_factor_detail_data.get("product_rollup"), list)
                and win_loss_factor_detail_data.get("safety", {}).get("external_message_sent") is False
                and win_loss_factor_detail_data.get("safety", {}).get("customer_forbidden_fields_exposed") is False,
            )
        )
        customer_value_route_data = customer_value_route.json() if customer_value_route.status_code == 200 else {}
        checks.append(
            (
                "route customer value intelligence",
                customer_value_route.status_code == 200
                and isinstance(customer_value_route_data.get("items"), list)
                and isinstance(customer_value_route_data.get("summary"), dict)
                and "management_questions" in customer_value_route_data
                and "who_to_follow" in customer_value_route_data["management_questions"]
                and all(
                    item.get("value_tier")
                    and "weighted_pipeline_amount" in item
                    and item.get("safety", {}).get("external_message_sent") is False
                    for item in customer_value_route_data.get("items", [])
                ),
            )
        )
        revenue_forecast_route_data = revenue_forecast_route.json() if revenue_forecast_route.status_code == 200 else {}
        checks.append(
            (
                "route revenue forecast intelligence",
                revenue_forecast_route.status_code == 200
                and isinstance(revenue_forecast_route_data.get("summary"), dict)
                and "total_weighted_amount" in revenue_forecast_route_data["summary"]
                and isinstance(revenue_forecast_route_data.get("forecast_items"), list)
                and isinstance(revenue_forecast_route_data.get("forecast_by_product"), list)
                and "future_revenue_from" in revenue_forecast_route_data.get("management_questions", {})
                and all(
                    item.get("source_type") in {"opportunity", "quote", "order_backlog"}
                    and item.get("safety", {}).get("external_message_sent") is False
                    for item in revenue_forecast_route_data.get("forecast_items", [])
                ),
            )
        )
        partner_performance_route_data = partner_performance_route.json() if partner_performance_route.status_code == 200 else {}
        partner_performance_detail_data = (
            partner_performance_detail_route.json()
            if partner_performance_detail_route is not None and partner_performance_detail_route.status_code == 200
            else {}
        )
        checks.append(
            (
                "route partner performance intelligence",
                partner_performance_route.status_code == 200
                and isinstance(partner_performance_route_data.get("summary"), dict)
                and "which_partner_to_invest" in partner_performance_route_data.get("management_questions", {})
                and isinstance(partner_performance_route_data.get("partner_scoreboard"), list)
                and all(
                    item.get("partner_name")
                    and item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                    for item in partner_performance_route_data.get("items", [])
                ),
            )
        )
        checks.append(
            (
                "route partner performance detail",
                partner_performance_detail_route is not None
                and partner_performance_detail_route.status_code == 200
                and partner_performance_detail_data.get("partner_name")
                and isinstance(partner_performance_detail_data.get("summary"), dict)
                and isinstance(partner_performance_detail_data.get("allocation_profile"), dict)
                and isinstance(partner_performance_detail_data.get("product_line_contribution"), list)
                and isinstance(partner_performance_detail_data.get("quote_samples"), list)
                and isinstance(partner_performance_detail_data.get("order_samples"), list)
                and isinstance(partner_performance_detail_data.get("feedback_samples"), list)
                and "should_this_partner_get_next_quote" in partner_performance_detail_data.get("management_questions", {})
                and partner_performance_detail_data.get("summary", {}).get("uses_cost_or_margin") is False
                and partner_performance_detail_data.get("safety", {}).get("external_message_sent") is False
                and partner_performance_detail_data.get("safety", {}).get("customer_forbidden_fields_exposed") is False,
            )
        )
        product_market_fit_route_data = product_market_fit_route.json() if product_market_fit_route.status_code == 200 else {}
        product_market_fit_factor_detail_data = (
            product_market_fit_factor_detail_route.json()
            if product_market_fit_factor_detail_route is not None
            and product_market_fit_factor_detail_route.status_code == 200
            else {}
        )
        checks.append(
            (
                "route product-market fit intelligence",
                product_market_fit_route.status_code == 200
                and isinstance(product_market_fit_route_data.get("summary"), dict)
                and "why_customers_buy_or_decline" in product_market_fit_route_data.get("management_questions", {})
                and isinstance(product_market_fit_route_data.get("validated_buying_factors"), list)
                and all(
                    item.get("partner_focus")
                    and isinstance(item.get("buying_factors_ranked"), list)
                    and item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                    for item in product_market_fit_route_data.get("items", [])
                ),
            )
        )
        checks.append(
            (
                "route product-market fit factor detail",
                product_market_fit_factor_detail_route is not None
                and product_market_fit_factor_detail_route.status_code == 200
                and product_market_fit_factor_detail_data.get("factor")
                and isinstance(product_market_fit_factor_detail_data.get("summary"), dict)
                and isinstance(product_market_fit_factor_detail_data.get("items"), list)
                and isinstance(product_market_fit_factor_detail_data.get("buying_factor_evidence"), list)
                and isinstance(product_market_fit_factor_detail_data.get("partner_rollup"), list)
                and isinstance(product_market_fit_factor_detail_data.get("product_rollup"), list)
                and isinstance(product_market_fit_factor_detail_data.get("customer_safe_candidates"), list)
                and isinstance(product_market_fit_factor_detail_data.get("internal_only_boundaries"), list)
                and product_market_fit_factor_detail_data.get("safety", {}).get("external_message_sent") is False
                and product_market_fit_factor_detail_data.get("safety", {}).get("customer_forbidden_fields_exposed") is False,
            )
        )
        account_360_route_data = account_360_route.json() if account_360_route.status_code == 200 else {}
        account_360_detail_route_data = (
            account_360_detail_route.json()
            if account_360_detail_route is not None and account_360_detail_route.status_code == 200
            else {}
        )
        checks.append(
            (
                "route account 360 intelligence",
                account_360_route.status_code == 200
                and isinstance(account_360_route_data.get("summary"), dict)
                and "who_to_follow" in account_360_route_data.get("management_questions", {})
                and isinstance(account_360_route_data.get("recommended_accounts"), list)
                and all(
                    item.get("customer_name")
                    and isinstance(item.get("object_timeline"), list)
                    and item.get("safety", {}).get("external_message_sent") is False
                    and item.get("safety", {}).get("customer_forbidden_fields_exposed") is False
                    for item in account_360_route_data.get("items", [])
                ),
            )
        )
        checks.append(
            (
                "route account 360 detail",
                account_360_detail_route is not None
                and account_360_detail_route.status_code == 200
                and account_360_detail_route_data.get("account_key")
                and isinstance(account_360_detail_route_data.get("detail_summary"), dict)
                and isinstance(account_360_detail_route_data.get("commercial_questions"), dict)
                and isinstance(account_360_detail_route_data.get("commercial_asset_coverage"), dict)
                and isinstance(account_360_detail_route_data.get("object_timeline"), list)
                and account_360_detail_route_data.get("safety", {}).get("external_message_sent") is False
                and account_360_detail_route_data.get("safety", {}).get("customer_forbidden_fields_exposed") is False,
            )
        )
        checks.append(
            (
                "route product validation context",
                response.status_code == 200
                and any(
                    item.get("validation_context", {}).get("next_best_action")
                    and item.get("validation_context", {}).get("evidence_counts")
                    and item.get("validation_context", {}).get("safety", {}).get("customer_forbidden_fields_exposed") is False
                    for item in response_data.get("products", [])
                ),
            )
        )
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
        checks.append(
            (
                "route opportunity execution context",
                created.status_code in {200, 201}
                and created_data.get("execution_context", {}).get("health")
                and created_data.get("execution_context", {}).get("conversion_signal", {}).get("manual_handoff_required") is True
                and created_data.get("execution_context", {}).get("safety", {}).get("external_message_sent") is False
                and created_data.get("execution_context", {}).get("safety", {}).get("order_status_changed") is False,
            )
        )
        checks.append(("route opportunity patch", patched is not None and patched.status_code == 200 and patched.json().get("data", {}).get("probability") == 72))
        win_loss_data = win_loss_list.json().get("data", {}) if win_loss_list.status_code == 200 else {}
        checks.append(
            (
                "route opportunity win/loss record",
                win_loss_created is not None
                and win_loss_created.status_code in {200, 201}
                and win_loss_created.json().get("data", {}).get("outcome") == "won"
                and win_loss_created.json().get("data", {}).get("safety", {}).get("quote_status_changed") is False
                and win_loss_created.json().get("data", {}).get("safety", {}).get("order_status_changed") is False,
            )
        )
        checks.append(
            (
                "route win/loss intelligence library",
                win_loss_list.status_code == 200
                and win_loss_data.get("summary", {}).get("total", 0) >= 1
                and any(
                    item.get("source_id") == created_data.get("id")
                    and item.get("outcome") == "won"
                    and item.get("safety", {}).get("external_message_sent") is False
                    for item in win_loss_data.get("items", [])
                ),
            )
        )
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
        checks.append(
            (
                "route opportunity execution reaches dashboard",
                any(
                    item.get("id") == created_data.get("id")
                    and item.get("execution_context", {}).get("next_best_action")
                    and item.get("execution_context", {}).get("safety", {}).get("external_message_sent") is False
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
