"""D8.17 full-chain manual acceptance check."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8014").rstrip("/")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:5173").rstrip("/")


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


def _request_text(url: str) -> str:
    request = Request(url, method="GET")
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def _request_json(
    path: str,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    token: str | None = None,
) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{BACKEND_BASE_URL}{path}", data=data, headers=headers, method=method)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _login() -> str:
    response = _request_json("/api/auth/login", "POST", {"email": "admin@example.com", "password": "admin123"})
    return str(response["access_token"])


def _create_campaign(token: str, partner: str, product_focus: list[str], segment: str, goal: str) -> dict[str, object]:
    suffix = str(int(time.time()))
    return _request_json(
        "/api/v1/growth/campaigns",
        "POST",
        {
            "name": f"TEST D8.17 {partner} full-chain check {suffix}",
            "partner_focus": partner,
            "product_focus": product_focus,
            "target_segment": segment,
            "goal": goal,
            "status": "planned",
            "owner": "D8.17 acceptance check",
            "next_action": "Create manual outreach task, update status, and review quote/order/feedback/market response.",
            "notes": "Local D8.17 acceptance data only. No external send.",
        },
        token,
    )


def main() -> int:
    checks = [
        Check("full-chain UI markers"),
        Check("manual acceptance document"),
        Check("runtime campaign and outreach loop"),
        Check("runtime order feedback market partner APIs"),
        Check("frontend routes reachable"),
        Check("handoff boundary and no external automation"),
    ]

    dashboard = _read("frontend/src/pages/dashboard/DashboardPage.vue")
    growth = _read("frontend/src/pages/growth/GrowthOperationsPage.vue")
    market = _read("frontend/src/pages/market/MarketPage.vue")
    demo = _read("frontend/src/pages/demo/DemoWalkthroughPage.vue")
    partner = _read("frontend/src/pages/partners/PartnerOnboardingPage.vue")
    feedback = _read("frontend/src/pages/system/FeedbackTicketsPage.vue")
    feedback_api = _read("frontend/src/api/feedbackTickets.ts")
    growth_service = _read("backend/app/services/growth_operations.py")
    growth_schema = _read("backend/app/schemas/growth.py")
    docs = _read("docs/demo/d8_17_full_chain_manual_acceptance.md")

    ok, missing = _contains_all(
        "\n".join([dashboard, growth, market, demo, partner, feedback, feedback_api, growth_service, growth_schema]),
        (
            "每日操作地图",
            "Campaign / 营销活动",
            "人工外联",
            "已请求报价",
            "客户可见",
            "反馈处理仅记录内部操作",
            "HOSUN lifting systems",
            "desk frames",
            "desk legs",
            "lifting columns",
            "heavy-duty supply",
            "JOOBOO education furniture",
            "project furniture",
            "HOSUN 和 JOOBOO",
        ),
    )
    checks[0].pass_("dashboard, growth, market, feedback, partner, demo markers present") if ok else checks[0].fail(missing)

    ok, missing = _contains_all(
        docs,
        (
            "D8.17",
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "WorkBench".replace("WorkBench", "Workbench"),
            "TEST D8.17 HOSUN Campaign",
            "TEST D8.17 JOOBOO Campaign",
            "客户开发 → Campaign / 营销活动 → 人工外联 → 报价 → 订单 → 生产 → 物流 → Portal → Feedback → Market Response → Partner 接入",
            "does not auto-send",
            "No blocking issue found",
        ),
    )
    checks[1].pass_("D8.17 manual acceptance record present") if ok else checks[1].fail(missing)

    try:
        token = _login()
        hosun = _create_campaign(
            token,
            "HOSUN",
            ["lifting systems", "desk frames", "desk legs", "lifting columns", "heavy-duty supply"],
            "升降办公和项目制采购客户",
            "Validate HOSUN full-chain growth acceptance from campaign to quote/order/feedback/market response.",
        )
        jooboo = _create_campaign(
            token,
            "JOOBOO",
            ["education furniture", "project furniture", "classroom furniture"],
            "教育家具和学校项目采购客户",
            "Validate JOOBOO full-chain growth acceptance from campaign to quote/order/feedback/market response.",
        )
        jooboo_data = jooboo["data"]  # type: ignore[index]
        jooboo_campaign_id = jooboo_data["campaign"]["id"]  # type: ignore[index]
        task_detail = _request_json(
            f"/api/v1/growth/campaigns/{jooboo_campaign_id}/tasks",
            "POST",
            {"task_type": "manual_outreach", "language": "zh", "notes": "D8.17 full-chain manual outreach check"},
            token,
        )
        task = task_detail["data"]["tasks"][0]  # type: ignore[index]
        interested = _request_json(f"/api/v1/growth/tasks/{task['id']}", "PATCH", {"status": "interested"}, token)
        quote_requested = _request_json(f"/api/v1/growth/tasks/{task['id']}", "PATCH", {"status": "quote_requested"}, token)
        campaign_ok = (
            hosun["data"]["campaign"]["partner_focus"] == "HOSUN"  # type: ignore[index]
            and jooboo_data["campaign"]["partner_focus"] == "JOOBOO"  # type: ignore[index]
            and task["draft_subject"]
            and interested["data"]["tasks"][0]["status"] == "interested"  # type: ignore[index]
            and quote_requested["data"]["tasks"][0]["status"] == "quote_requested"  # type: ignore[index]
            and quote_requested["data"]["safety"]["email_sent"] is False  # type: ignore[index]
            and quote_requested["data"]["safety"]["customer_notified"] is False  # type: ignore[index]
        )
        checks[2].pass_("HOSUN/JOOBOO campaigns and manual outreach status loop OK") if campaign_ok else checks[2].fail("campaign/task runtime loop incomplete")

        orders = _request_json("/api/v1/orders?limit=1", token=token)
        tickets = _request_json("/api/v1/feedback-tickets?limit=1", token=token)
        market_response = _request_json("/api/v1/market/response-intelligence", token=token)
        onboarding = _request_json("/api/v1/partner-onboarding", token=token)
        runtime_ok = (
            orders["data"]["items"] is not None  # type: ignore[index]
            and tickets["data"]["items"] is not None  # type: ignore[index]
            and market_response["data"]["safety"]["email_sent"] is False  # type: ignore[index]
            and market_response["data"]["safety"]["order_status_changed"] is False  # type: ignore[index]
            and onboarding["data"]["status"] == "READY_FOR_STAGING_HANDOFF"  # type: ignore[index]
        )
        checks[3].pass_("order, feedback, market, partner runtime APIs OK") if runtime_ok else checks[3].fail("runtime chain response incomplete")
    except (HTTPError, URLError, TimeoutError, KeyError, TypeError, ValueError) as exc:
        checks[2].fail(f"runtime campaign/task failed: {exc.__class__.__name__}")
        checks[3].fail("skipped because runtime setup failed")

    try:
        route_paths = (
            "/",
            "/growth-operations",
            "/quotes",
            "/orders",
            "/feedback-tickets",
            "/market-response",
            "/partner-onboarding",
            "/demo-walkthrough",
        )
        shells = [_request_text(f"{FRONTEND_BASE_URL}{path}") for path in route_paths]
        frontend_ok = all('id="app"' in shell for shell in shells)
        checks[4].pass_("all full-chain routes serve Vue app") if frontend_ok else checks[4].fail("Vue app shell missing")
    except (HTTPError, URLError, TimeoutError) as exc:
        checks[4].fail(f"frontend shell failed: {exc.__class__.__name__}")

    boundary_text = "\n".join([dashboard, growth, market, demo, partner, feedback, docs])
    unsafe_markers = (
        "Status: " + "STAGING_VALIDATED",
        "D9 is ready",
        "proof record created",
        "email_sent\": True",
        "customer_notified\": True",
        "supplier_notified\": True",
        "webhook_sent\": True",
        "order_status_changed\": True",
    )
    found = [marker for marker in unsafe_markers if marker in boundary_text]
    checks[5].pass_("READY_FOR_STAGING_HANDOFF only; no forbidden automation") if not found else checks[5].fail(", ".join(found))

    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.17 full-chain acceptance check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1
    print("\nD8.17 full-chain acceptance check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
