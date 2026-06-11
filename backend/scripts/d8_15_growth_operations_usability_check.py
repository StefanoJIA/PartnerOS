"""D8.15 Growth Operations usability and Chinese login check."""

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


def main() -> int:
    checks = [
        Check("login page Chinese labels and proxy hint"),
        Check("Growth Operations Chinese usability copy"),
        Check("D8.15 demo documentation"),
        Check("runtime Growth Operations API safety"),
        Check("frontend dev shell pages reachable"),
        Check("no forbidden automation or staging claim"),
    ]

    login_page = _read("frontend/src/pages/auth/LoginPage.vue")
    growth_page = _read("frontend/src/pages/growth/GrowthOperationsPage.vue")
    docs = _read("docs/demo/d8_15_growth_operations_usability_check.md")

    ok, missing = _contains_all(
        login_page,
        (
            "邮箱",
            "密码",
            "登录",
            "本地默认账号",
            "VITE_API_PROXY_TARGET=http://127.0.0.1:8014",
            "登录失败。请确认 backend 8014 已启动",
        ),
    )
    checks[0].pass_("login defaults are Chinese-first") if ok else checks[0].fail(missing)

    ok, missing = _contains_all(
        growth_page,
        (
            "Campaign / 营销活动",
            "规划活动 → 选择分群 → 创建外联任务 → 更新状态 →",
            "保存 Campaign",
            "HOSUN",
            "JOOBOO",
            "HOSUN / JOOBOO 平级运营",
            "不自动发送",
            "当前 Campaign / 营销活动暂无可记录的线索",
        ),
    )
    checks[1].pass_("growth copy explains the Chinese operating flow") if ok else checks[1].fail(missing)

    ok, missing = _contains_all(
        docs,
        (
            "D8.15",
            "READY_FOR_STAGING_HANDOFF",
            "WAITING_FOR_REAL_STAGING_EVIDENCE",
            "VITE_API_PROXY_TARGET=\"http://127.0.0.1:8014\"",
            "Campaign / 营销活动",
            "规划活动 → 选择分群 → 创建外联任务 → 更新状态 → 查看报价/订单/反馈/市场响应",
        ),
    )
    checks[2].pass_("D8.15 local runtime and usability notes present") if ok else checks[2].fail(missing)

    try:
        login = _request_json("/api/auth/login", "POST", {"email": "admin@example.com", "password": "admin123"})
        token = str(login["access_token"])
        console = _request_json("/api/v1/growth/operations-console", token=token)
        campaigns = _request_json("/api/v1/growth/campaigns", token=token)
        console_data = console["data"]  # type: ignore[index]
        campaign_data = campaigns["data"]  # type: ignore[index]
        runtime_ok = (
            console.get("ok") is True
            and campaigns.get("ok") is True
            and console_data["safety"]["staging_validated"] is False  # type: ignore[index]
            and campaign_data["safety"]["email_sent"] is False  # type: ignore[index]
            and campaign_data["safety"]["customer_notified"] is False  # type: ignore[index]
            and campaign_data["safety"]["order_status_changed"] is False  # type: ignore[index]
        )
        checks[3].pass_("Growth APIs reachable and safety flags are false") if runtime_ok else checks[3].fail("runtime safety flags incomplete")
    except (HTTPError, URLError, TimeoutError, KeyError, TypeError, ValueError) as exc:
        checks[3].fail(f"runtime API failed: {exc.__class__.__name__}")

    try:
        login_shell = _request_text(f"{FRONTEND_BASE_URL}/login")
        growth_shell = _request_text(f"{FRONTEND_BASE_URL}/growth-operations")
        frontend_ok = 'id="app"' in login_shell and 'id="app"' in growth_shell
        checks[4].pass_("login and growth routes serve the Vue app") if frontend_ok else checks[4].fail("Vue app shell missing")
    except (HTTPError, URLError, TimeoutError) as exc:
        checks[4].fail(f"frontend dev shell failed: {exc.__class__.__name__}")

    boundary_text = "\n".join([login_page, growth_page, docs])
    unsafe_markers = (
        "Status: " + "STAGING_VALIDATED",
        "D9 is ready",
        "email_sent\": True",
        "customer_notified\": True",
        "supplier_notified\": True",
        "quote_status_changed\": True",
        "order_status_changed\": True",
    )
    found = [marker for marker in unsafe_markers if marker in boundary_text]
    checks[5].pass_("READY_FOR_STAGING_HANDOFF only; no forbidden automation") if not found else checks[5].fail(", ".join(found))

    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.15 Growth Operations usability check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1
    print("\nD8.15 Growth Operations usability check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
