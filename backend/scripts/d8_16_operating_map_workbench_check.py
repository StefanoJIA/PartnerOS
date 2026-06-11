"""D8.16 daily workbench and operating map check."""

from __future__ import annotations

import json
import os
import sys
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


def _request_json(path: str, method: str = "GET", payload: dict[str, object] | None = None, token: str | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{BACKEND_BASE_URL}{path}", data=data, headers=headers, method=method)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _request_text(url: str) -> str:
    request = Request(url, method="GET")
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def _nav_group_count(layout_text: str) -> int:
    return layout_text.count("key:")


def main() -> int:
    checks = [
        Check("daily workbench operating map UI"),
        Check("core workflow links are present"),
        Check("operating map document"),
        Check("8 primary navigation groups remain stable"),
        Check("runtime workbench APIs are available"),
        Check("frontend dashboard shell is reachable"),
        Check("no D9, proof records, staging claim, or automation"),
    ]

    dashboard = _read("frontend/src/pages/dashboard/DashboardPage.vue")
    layout = _read("frontend/src/layouts/MainLayout.vue")
    docs = _read("docs/phase3/d8_16_operating_map.md")

    ok, missing = _contains_all(
        dashboard,
        (
            "每日操作地图",
            "业务开发",
            "运营交付",
            "管理决策",
            "Campaign / 营销活动",
            "待处理报价 / RFQ",
            "订单交付与物流风险",
            "客户 Feedback 处理",
            "Market Response 推荐",
            "Partner Onboarding 缺口",
            "READY_FOR_STAGING_HANDOFF",
        ),
    )
    checks[0].pass_("dashboard is a Chinese daily operating entry") if ok else checks[0].fail(missing)

    ok, missing = _contains_all(
        dashboard,
        (
            "/growth-operations",
            "/lead-intelligence",
            "/quotes",
            "/rfqs",
            "/orders",
            "/partner-operations",
            "/feedback-tickets",
            "/market-response",
            "/partner-onboarding",
            "/demo-walkthrough",
        ),
    )
    checks[1].pass_("Campaign, Quote, Order, Feedback, Market, Partner links present") if ok else checks[1].fail(missing)

    ok, missing = _contains_all(
        docs,
        (
            "D8.16",
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "业务开发",
            "运营交付",
            "管理决策",
            "Campaign / 营销活动",
            "Quote",
            "Order",
            "Feedback",
            "Market Response",
            "HOSUN",
            "JOOBOO",
            "不进入 D9",
        ),
    )
    checks[2].pass_("Chinese operating map document present") if ok else checks[2].fail(missing)

    group_count = _nav_group_count(layout)
    expected_groups = ("工作台", "客户开发", "产品与报价", "订单交付", "客户 Portal", "市场响应", "Partner 管理", "演示与资料")
    nav_ok = group_count == 8 and all(group in layout for group in expected_groups)
    checks[3].pass_("8 group(s)") if nav_ok else checks[3].fail(f"{group_count} group(s)")

    try:
        login = _request_json("/api/auth/login", "POST", {"email": "admin@example.com", "password": "admin123"})
        token = str(login["access_token"])
        daily = _request_json("/api/dashboard/actions", token=token)
        growth = _request_json("/api/v1/growth/operations-console", token=token)
        feedback = _request_json("/api/v1/feedback-tickets?operation_filter=needs_internal_review&limit=1", token=token)
        market = _request_json("/api/v1/market/response-intelligence", token=token)
        partner = _request_json("/api/v1/partner-onboarding", token=token)
        runtime_ok = (
            isinstance(daily.get("recommended_actions"), list)
            and growth["data"]["safety"]["email_sent"] is False  # type: ignore[index]
            and feedback["data"]["items"] is not None  # type: ignore[index]
            and market["data"]["safety"]["email_sent"] is False  # type: ignore[index]
            and partner["data"]["status"] == "READY_FOR_STAGING_HANDOFF"  # type: ignore[index]
        )
        checks[4].pass_("dashboard, growth, feedback, market, partner APIs OK") if runtime_ok else checks[4].fail("runtime response shape or safety failed")
    except (HTTPError, URLError, TimeoutError, KeyError, TypeError, ValueError) as exc:
        checks[4].fail(f"runtime API failed: {exc.__class__.__name__}")

    try:
        shell = _request_text(f"{FRONTEND_BASE_URL}/")
        checks[5].pass_("Vue app shell served") if 'id="app"' in shell else checks[5].fail("Vue app shell missing")
    except (HTTPError, URLError, TimeoutError) as exc:
        checks[5].fail(f"frontend shell failed: {exc.__class__.__name__}")

    boundary_text = "\n".join([dashboard, docs])
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
    checks[6].pass_("D8 handoff boundary and manual-only safety intact") if not found else checks[6].fail(", ".join(found))

    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.16 operating map workbench check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1
    print("\nD8.16 operating map workbench check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
