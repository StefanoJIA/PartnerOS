"""D8.11 Chinese operating language and workflow alignment check."""

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


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _contains_all(text: str, markers: tuple[str, ...]) -> tuple[bool, str]:
    missing = [marker for marker in markers if marker not in text]
    return not missing, ", ".join(missing)


def main() -> int:
    checks = [
        Check("central Chinese label maps"),
        Check("dashboard operating copy"),
        Check("core pages Chinese-first"),
        Check("business status displays use Chinese labels"),
        Check("portal operations workflow copy"),
        Check("handoff-only boundary"),
        Check("no forbidden local artifacts referenced"),
    ]

    zh_copy = _read("frontend/src/copy/zhCN.ts")
    daily_ops = _read("frontend/src/components/dashboard/DailyOperationsPanel.vue")
    activity = _read("frontend/src/components/dashboard/RecentActivityList.vue")
    eod = _read("frontend/src/components/dashboard/EndOfDaySummaryPanel.vue")
    product = _read("frontend/src/components/dashboard/ProductOpportunitySummary.vue")
    daily_ops_constants = _read("frontend/src/constants/dailyOps.ts")
    eod_constants = _read("frontend/src/constants/dailyWorkSummary.ts")
    demo = _read("frontend/src/pages/demo/DemoWalkthroughPage.vue")
    portal = _read("frontend/src/pages/system/PortalOperationsPage.vue")
    market = _read("frontend/src/pages/market/MarketPage.vue")
    orders = _read("frontend/src/pages/orders/OrdersPage.vue")
    order_detail = _read("frontend/src/pages/orders/OrderDetailPage.vue")
    feedback = _read("frontend/src/pages/system/FeedbackTicketsPage.vue")
    partner = _read("frontend/src/pages/partners/PartnerOnboardingPage.vue")
    system = _read("frontend/src/pages/system/SystemHealthPage.vue")

    map_markers = (
        "ORDER_STATUS_LABELS",
        "QUOTE_STATUS_LABELS",
        "FEEDBACK_STATUS_LABELS",
        "FEEDBACK_PRIORITY_LABELS",
        "SHIPMENT_STATUS_LABELS",
        "PRODUCTION_STATUS_LABELS",
        "PARTNER_ONBOARDING_STAGE_LABELS",
        "MARKET_SIGNAL_LABELS",
        "PORTAL_READINESS_LABELS",
        "zhLabel",
    )
    ok, missing = _contains_all(zh_copy, map_markers)
    checks[0].pass_("shared display maps exist") if ok else checks[0].fail(missing)

    dashboard_markers = (
        "每日运营指挥台",
        "今日重点",
        "近期人工触达",
        "产品机会摘要",
        "日终运营总结",
        "已人工发送",
        "打开线索",
    )
    ok, missing = _contains_all("\n".join([daily_ops, activity, eod, product, daily_ops_constants, eod_constants, zh_copy]), dashboard_markers)
    checks[1].pass_("dashboard cards and actions localized") if ok else checks[1].fail(missing)

    core_markers = (
        "业务演示流程",
        "Portal 运营",
        "市场响应智能",
        "客户订单",
        "客户可见运营摘要",
        "客户反馈工单",
        "Partner 接入管理",
        "系统健康",
    )
    ok, missing = _contains_all("\n".join([demo, portal, market, orders, order_detail, feedback, partner, system]), core_markers)
    checks[2].pass_("core business pages have Chinese entry copy") if ok else checks[2].fail(missing)

    status_markers = (
        "zhLabel(ORDER_STATUS_LABELS",
        "zhLabel(FEEDBACK_STATUS_LABELS",
        "zhLabel(FEEDBACK_PRIORITY_LABELS",
        "zhLabel(SHIPMENT_STATUS_LABELS",
        "zhLabel(PRODUCTION_STATUS_LABELS",
        "zhLabel(RESOURCE_STATUS_LABELS",
        "zhLabel(MARKET_SIGNAL_LABELS",
    )
    ok, missing = _contains_all("\n".join([orders, order_detail, feedback, portal]), status_markers)
    checks[3].pass_("status and signal fields render via Chinese maps") if ok else checks[3].fail(missing)

    portal_markers = (
        "近期客户可见订单",
        "物流状态",
        "反馈状态",
        "多 Partner 运营闭环准备度",
        "客户可见快照",
        "资料中心准备度",
        "市场响应信号",
        "近期反馈工单",
    )
    ok, missing = _contains_all(portal, portal_markers)
    checks[4].pass_("portal operations explains workflow in Chinese") if ok else checks[4].fail(missing)

    combined_boundary = "\n".join([zh_copy, demo, portal, market, orders, order_detail, feedback, partner, system])
    unsafe = "Status: STAGING_VALIDATED" in combined_boundary or "D9 is ready" in combined_boundary
    if "READY_FOR_STAGING_HANDOFF" in combined_boundary and not unsafe:
        checks[5].pass_("READY_FOR_STAGING_HANDOFF remains the external status")
    else:
        checks[5].fail("staging boundary unclear")

    forbidden = ("IE Auto.pdf", "local_data/", "backend/storage/", "PORTAL_CUSTOMER_API_TOKEN=")
    found = [item for item in forbidden if item in combined_boundary]
    checks[6].pass_("no local artifact or token value references") if not found else checks[6].fail(", ".join(found))

    print("D8.11 Chinese Operating Language Check")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
