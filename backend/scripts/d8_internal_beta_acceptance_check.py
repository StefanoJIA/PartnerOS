"""Internal beta acceptance check for PartnerOS D8 handoff usability.

This is a local readiness check. It does not call real staging, does not send
external messages, and does not create proof records.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Check:
    label: str
    ok: bool = False
    detail: str = ""

    def pass_(self, detail: str = "") -> None:
        self.ok = True
        self.detail = detail

    def fail(self, detail: str) -> None:
        self.ok = False
        self.detail = detail

    def line(self) -> str:
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{'PASS' if self.ok else 'FAIL'}] {self.label}{suffix}"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    missing = [marker for marker in markers if marker not in text]
    return not missing, ", ".join(missing)


def main() -> int:
    checks = [
        Check("Internal beta files and routes"),
        Check("Workbench entry points"),
        Check("External execution tracker fields"),
        Check("Manual-only execution guardrails"),
        Check("Staging readiness boundary"),
        Check("HOSUN/JOOBOO/future partner operating coverage"),
        Check("Core internal beta routes remain linked"),
        Check("No unsafe completion claims"),
    ]

    required_files = (
        "backend/alembic/versions/0019_external_execution.py",
        "backend/alembic/versions/0021_daily_queue_handling.py",
        "backend/app/models/daily_queue.py",
        "backend/app/models/external_execution.py",
        "backend/app/models/market_response.py",
        "backend/app/schemas/external_execution.py",
        "backend/app/schemas/market_response_reviews.py",
        "backend/app/services/external_execution.py",
        "backend/app/services/daily_decision_queue.py",
        "backend/app/services/market_response_reviews.py",
        "backend/app/services/partner_onboarding.py",
        "backend/app/api/v1/routes/external_execution.py",
        "backend/app/api/v1/routes/market_response.py",
        "backend/app/api/v1/routes/partner_onboarding.py",
        "frontend/src/api/externalExecution.ts",
        "frontend/src/api/marketResponse.ts",
        "frontend/src/api/partnerOnboarding.ts",
        "frontend/src/pages/execution/ExternalExecutionPage.vue",
        "frontend/src/components/dashboard/OperationalTracePanel.vue",
        "frontend/src/pages/market/MarketPage.vue",
        "frontend/src/pages/partners/PartnerOnboardingPage.vue",
        "frontend/src/pages/orders/OrdersPage.vue",
        "frontend/src/pages/system/FeedbackTicketsPage.vue",
        "frontend/src/router/index.ts",
        "frontend/src/layouts/MainLayout.vue",
        "frontend/src/pages/dashboard/DashboardPage.vue",
        "frontend/src/pages/demo/DemoWalkthroughPage.vue",
    )
    missing_files = [path for path in required_files if not (ROOT / path).exists()]
    if missing_files:
        checks[0].fail(", ".join(missing_files))
        for check in checks:
            print(check.line())
        return 1

    external_page = read("frontend/src/pages/execution/ExternalExecutionPage.vue")
    external_api = read("frontend/src/api/externalExecution.ts")
    backend_route = read("backend/app/api/v1/routes/external_execution.py")
    market_route = read("backend/app/api/v1/routes/market_response.py")
    partner_route = read("backend/app/api/v1/routes/partner_onboarding.py")
    daily_queue_model = read("backend/app/models/daily_queue.py")
    backend_service = read("backend/app/services/external_execution.py")
    daily_queue_service = read("backend/app/services/daily_decision_queue.py")
    dashboard_route = read("backend/app/api/routes/dashboard.py")
    dashboard_schema = read("backend/app/schemas/dashboard_actions.py")
    dashboard_api = read("frontend/src/api/dashboard.ts")
    trace_panel = read("frontend/src/components/dashboard/OperationalTracePanel.vue")
    market_review_service = read("backend/app/services/market_response_reviews.py")
    partner_onboarding_service = read("backend/app/services/partner_onboarding.py")
    migration = read("backend/alembic/versions/0019_external_execution.py")
    market_migration = read("backend/alembic/versions/0020_market_response_reviews.py")
    daily_queue_migration = read("backend/alembic/versions/0021_daily_queue_handling.py")
    router = read("frontend/src/router/index.ts")
    nav = read("frontend/src/layouts/MainLayout.vue")
    dashboard = read("frontend/src/pages/dashboard/DashboardPage.vue")
    demo = read("frontend/src/pages/demo/DemoWalkthroughPage.vue")
    market_page = read("frontend/src/pages/market/MarketPage.vue")
    market_api = read("frontend/src/api/marketResponse.ts")
    partner_page = read("frontend/src/pages/partners/PartnerOnboardingPage.vue")
    partner_api = read("frontend/src/api/partnerOnboarding.ts")
    orders_page = read("frontend/src/pages/orders/OrdersPage.vue")
    feedback_page = read("frontend/src/pages/system/FeedbackTicketsPage.vue")
    combined = "\n".join(
        [
            external_page,
            external_api,
            daily_queue_model,
            backend_route,
            backend_service,
            daily_queue_service,
            dashboard_route,
            dashboard_schema,
            dashboard_api,
            trace_panel,
            migration,
            daily_queue_migration,
            market_route,
            partner_route,
            market_review_service,
            partner_onboarding_service,
            market_migration,
            market_page,
            market_api,
            partner_page,
            partner_api,
            orders_page,
            feedback_page,
            router,
            nav,
            dashboard,
            demo,
        ]
    )

    ok, missing = contains_all(
        router,
        (
            "external-execution",
            "staging-readiness",
            "@/pages/execution/ExternalExecutionPage.vue",
        ),
    )
    checks[0].pass_("external execution page and staging-readiness alias are registered") if ok else checks[0].fail(missing)

    ok, missing = contains_all(
        dashboard + "\n" + nav + "\n" + demo,
        (
            "外部执行 / Staging",
            "Market Response 待审查",
            "外部执行与 Staging Gate",
            "本地 dry-run 不能替代真实 staging evidence",
            "/external-execution",
            "/external-execution?status=blocked",
            "/staging-readiness",
            "external-execution",
        ),
    )
    checks[1].pass_("dashboard, nav, and demo walkthrough expose response review and external execution gates") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "action_type",
            "owner",
            "due_date",
            "dependency",
            "next_step",
            "status",
            "notes",
            "draft",
            "ready to send",
            "sent manually",
            "response received",
            "blocked",
            "complete",
            "fetchExternalExecutionConsole",
            "createExternalExecutionAction",
            "updateExternalExecutionAction",
            "/v1/external-execution/console",
            "/v1/external-execution/actions",
            "external_execution_actions",
            "market_response_reviews",
            "response-reviews",
            "Market Response 运营审查队列",
            "fetchMarketResponseReviews",
            "fetchExternalExecutionConsole",
            "filteredActions",
            "applyExternalFilters",
            "syncFiltersFromRoute",
            "activeExternalFilterLabel",
            "应用筛选链接",
            "URL 可分享",
            "action_type",
            "owner",
            "keyword",
            "队列筛选",
            "只看阻塞",
            "状态来自人工记录",
            "真实回复安全录入",
            "回复录入",
            "标记 response received 前必须录入真实回复摘要",
            "PROVIDED_VIA_SECURE_CHANNEL",
            "linked_action_statuses",
            "next_action",
            "readiness_gap_intelligence",
            "Readiness Gap Intelligence",
            "readinessGaps",
            "readinessGapSummary",
            "affects_d9",
            "affects_pilot",
            "needs_business_signoff",
            "needs_security_signoff",
            "needs_partner_feedback",
            "needs_staging_credentials",
            "evidence_required",
            "customer_safe_boundary",
            "lifting_partner.lifting_systems_claims",
            "jooboo.project_furniture_path",
            "future_partner.onboarding_decision_model",
            "updateMarketResponseReview",
            "market-response-reviews",
            "needs%20review",
            "applyReviewFilters",
            "syncReviewFiltersFromRoute",
            "activeReviewFilterLabel",
            "URL 可分享",
            "只看待审查",
            "Pilot blocker",
            "clearReviewFilters",
            "partner_focus",
            "focus_category",
            "visibility_class",
            "status",
            "createPartnerOnboardingMarketResponseReviews",
            "生成市场审查项",
            "daily-decision-queue",
            "DailyDecisionQueueItem",
            "DailyDecisionQueueOut",
            "build_daily_decision_queue",
            "fetchDailyDecisionQueue",
            "今日运营决策队列",
            "depends_on_external_input",
            "readiness_gap_intelligence",
            "market_response_review",
            "partner_onboarding",
            "feedback_ticket",
            "order delivery",
            "daily_queue_handling_records",
            "DailyQueueHandlingRecord",
            "DailyQueueHandlingUpdate",
            "DailyQueueHandlingRecordOut",
            "updateDailyQueueHandling",
            "update_daily_queue_handling",
            "handling_status",
            "handling_events",
            "acknowledged",
            "in_progress",
            "deferred",
            "waiting_external",
            "decision_recorded",
            "处理今日运营决策项",
            "知晓",
            "接手",
            "延期/备注",
            "处理备注",
            "fetchDailyQueueHandling",
            "OperationalTracePanel",
            "Daily Queue 处理回流",
            "Daily Queue / Market Response 回流",
            "Daily Queue / Partner Onboarding 回流",
            "Daily Queue / 订单交付回流",
            "Daily Queue / Feedback 回流",
            "source_type",
            "source_id",
            "partner_focus",
            "category",
            "进入源对象",
            "internal handling layer",
        ),
    )
    checks[2].pass_("tracker includes required fields, statuses, API persistence, and migration") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "不自动发送邮件、短信、LinkedIn 或客户通知",
            "没有真实回复不能标记 response received",
            "没有真实签字不能 approved",
            "不能记录 raw token",
            "PROVIDED_VIA_SECURE_CHANNEL",
            "API cost $0",
        ),
    )
    checks[3].pass_("manual-only guardrails are visible") if ok else checks[3].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "backend HTTPS origin",
            "Portal origin",
            "PORTAL_CUSTOMER_API_TOKEN",
            "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
            "PUBLIC_BASE_URL",
            "security signoff",
            "business signoff",
            "real staging smoke test",
            "D9 gate blocked",
        ),
    )
    checks[4].pass_("staging readiness and D9 boundary are visible") if ok else checks[4].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "HOSUN",
            "lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty supply",
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
            "customer-safe candidate",
            "needs validation",
            "internal-only",
            "pilot blocker",
            "JOOBOO",
            "education furniture",
            "school desks/chairs",
            "project furniture",
            "future partner",
            "onboarding data",
            "quote logic",
            "Market Response metrics",
        ),
    )
    checks[5].pass_("multi-partner and HOSUN review dimensions are covered") if ok else checks[5].fail(missing)

    ok, missing = contains_all(
        combined,
        (
            "/",
            "/growth-operations",
            "/orders",
            "/feedback-tickets",
            "/market-response",
            "/partner-onboarding",
            "/portal-operations",
            "/demo-walkthrough",
            "/system-health",
            "/external-execution",
        ),
    )
    checks[6].pass_("required beta routes remain present or linked") if ok else checks[6].fail(missing)

    unsafe_positive_claims = (
        "Status: STAGING_VALIDATED",
        "External staging state: STAGING_VALIDATED",
        "D9 已开始",
        "message sent automatically",
        "自动发送客户通知",
        "raw token:",
        "real staging evidence recorded",
    )
    found = [marker for marker in unsafe_positive_claims if marker in combined]
    checks[7].pass_("no staging validation, D9 entry, raw-token, or automatic-send claim") if not found else checks[7].fail(", ".join(found))

    for check in checks:
        print(check.line())
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
