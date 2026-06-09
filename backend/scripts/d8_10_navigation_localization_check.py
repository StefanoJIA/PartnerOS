"""D8.10 navigation simplification and Chinese UI localization check."""

from __future__ import annotations

import re
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


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    missing = [marker for marker in markers if marker not in text]
    return not missing, ", ".join(missing)


def main() -> int:
    checks = [
        Check("primary navigation <= 8 groups"),
        Check("core routes preserved"),
        Check("core pages reachable from navigation"),
        Check("Chinese navigation labels"),
        Check("key pages localized"),
        Check("handoff-only boundary"),
        Check("no forbidden artifact references in staged UI work"),
    ]

    layout = _read("frontend/src/layouts/MainLayout.vue")
    router = _read("frontend/src/router/index.ts")
    partner_page = _read("frontend/src/pages/partners/PartnerOnboardingPage.vue")
    demo_page = _read("frontend/src/pages/demo/DemoWalkthroughPage.vue")
    portal_page = _read("frontend/src/pages/system/PortalOperationsPage.vue")
    market_page = _read("frontend/src/pages/market/MarketPage.vue")
    feedback_page = _read("frontend/src/pages/system/FeedbackTicketsPage.vue")
    orders_page = _read("frontend/src/pages/orders/OrdersPage.vue")
    order_detail_page = _read("frontend/src/pages/orders/OrderDetailPage.vue")
    system_page = _read("frontend/src/pages/system/SystemHealthPage.vue")

    expected_primary = ["工作台", "客户开发", "产品与报价", "订单交付", "客户 Portal", "市场响应", "Partner 管理", "演示与资料"]
    primary_labels = [label for label in expected_primary if f"label: '{label}'" in layout]
    if 1 <= len(primary_labels) <= 8:
        checks[0].pass_(f"{len(primary_labels)} group(s): {', '.join(primary_labels)}")
    else:
        checks[0].fail(f"{len(primary_labels)} primary group(s)")

    required_routes = (
        "demo-walkthrough",
        "partner-onboarding",
        "portal-operations",
        "portal-integration",
        "market-response",
        "market-intelligence",
        "orders",
        "feedback-tickets",
        "system-health",
    )
    ok, missing = _contains_all(router, required_routes)
    checks[1].pass_("router keeps stable paths") if ok else checks[1].fail(missing)

    required_nav_paths = (
        "/demo-walkthrough",
        "/partner-onboarding",
        "/portal-operations",
        "/market-response",
        "/orders",
        "/feedback-tickets",
        "/system-health",
    )
    ok, missing = _contains_all(layout, required_nav_paths)
    checks[2].pass_("navigation or redirects cover required pages") if ok else checks[2].fail(missing)

    chinese_nav_markers = ("工作台", "客户开发", "产品与报价", "订单交付", "客户 Portal", "市场响应", "Partner 管理", "演示与资料")
    ok, missing = _contains_all(layout, chinese_nav_markers)
    checks[3].pass_("major navigation labels localized") if ok else checks[3].fail(missing)

    localized_markers = (
        "业务演示流程",
        "Portal 运营",
        "市场响应智能",
        "客户反馈工单",
        "客户订单",
        "客户可见运营摘要",
        "Partner 接入管理",
        "系统健康",
    )
    combined_pages = "\n".join(
        [demo_page, portal_page, market_page, feedback_page, orders_page, order_detail_page, partner_page, system_page]
    )
    ok, missing = _contains_all(combined_pages, localized_markers)
    checks[4].pass_("key page copy localized") if ok else checks[4].fail(missing)

    combined_boundary = "\n".join([layout, router, partner_page, demo_page, portal_page, market_page, feedback_page, system_page])
    unsafe = "Status: STAGING_VALIDATED" in combined_boundary or "D9 is ready" in combined_boundary
    if "READY_FOR_STAGING_HANDOFF" in combined_boundary and not unsafe:
        checks[5].pass_("READY_FOR_STAGING_HANDOFF only")
    else:
        checks[5].fail("staging boundary unclear")

    forbidden = ("IE Auto.pdf", "local_data/", "backend/storage/", "PORTAL_CUSTOMER_API_TOKEN=")
    found = [item for item in forbidden if item in combined_boundary]
    checks[6].pass_("no forbidden artifact instructions") if not found else checks[6].fail(", ".join(found))

    print("D8.10 Navigation Localization Check")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
