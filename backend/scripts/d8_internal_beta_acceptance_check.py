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
        "frontend/src/pages/execution/ExternalExecutionPage.vue",
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
    router = read("frontend/src/router/index.ts")
    nav = read("frontend/src/layouts/MainLayout.vue")
    dashboard = read("frontend/src/pages/dashboard/DashboardPage.vue")
    demo = read("frontend/src/pages/demo/DemoWalkthroughPage.vue")
    combined = "\n".join([external_page, router, nav, dashboard, demo])

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
            "/external-execution",
            "external-execution",
        ),
    )
    checks[1].pass_("dashboard, nav, and demo walkthrough expose external execution") if ok else checks[1].fail(missing)

    ok, missing = contains_all(
        external_page,
        (
            "actionType",
            "owner",
            "dueDate",
            "dependency",
            "nextStep",
            "status",
            "notes",
            "draft",
            "ready to send",
            "sent manually",
            "response received",
            "blocked",
            "complete",
            "localStorage",
        ),
    )
    checks[2].pass_("tracker includes required fields, statuses, and local persistence") if ok else checks[2].fail(missing)

    ok, missing = contains_all(
        external_page,
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
        external_page,
        (
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "backend HTTPS origin",
            "service.intelli-opus.com real origin",
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
        external_page,
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
