"""D8.12 release candidate readiness audit check."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8014").rstrip("/")


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


def _post_json(path: str, payload: dict[str, object], token: str | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{BACKEND_BASE_URL}{path}", data=data, headers=headers, method="POST")
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(path: str, token: str | None = None) -> dict[str, object]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{BACKEND_BASE_URL}{path}", headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _run_script(name: str) -> tuple[bool, str]:
    env = os.environ.copy()
    env.setdefault("BACKEND_BASE_URL", BACKEND_BASE_URL)
    result = subprocess.run(
        [sys.executable, f"scripts/{name}"],
        cwd=ROOT / "backend",
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )
    tail = "\n".join(result.stdout.strip().splitlines()[-4:])
    return result.returncode == 0, tail


def main() -> int:
    checks = [
        Check("8 primary navigation groups"),
        Check("core routes and redirects preserved"),
        Check("Chinese label mapping available"),
        Check("demo business loop markers"),
        Check("multi-partner scenario markers"),
        Check("customer-visible safety boundary"),
        Check("D8.5/D8.9/D8.10/D8.11 checks still pass"),
        Check("handoff-only state boundary"),
        Check("no forbidden artifact references in D8.12 scope"),
    ]

    layout = _read("frontend/src/layouts/MainLayout.vue")
    router = _read("frontend/src/router/index.ts")
    zh_copy = _read("frontend/src/copy/zhCN.ts")
    demo = _read("frontend/src/pages/demo/DemoWalkthroughPage.vue")
    portal = _read("frontend/src/pages/system/PortalOperationsPage.vue")
    market = _read("frontend/src/pages/market/MarketPage.vue")
    orders = _read("frontend/src/pages/orders/OrdersPage.vue")
    order_detail = _read("frontend/src/pages/orders/OrderDetailPage.vue")
    feedback = _read("frontend/src/pages/system/FeedbackTicketsPage.vue")
    partner = _read("frontend/src/pages/partners/PartnerOnboardingPage.vue")
    docs = "\n".join(
        [
            _read("docs/demo/partner_demo_script.md"),
            _read("docs/demo/hosun_jooboo_demo_narrative.md"),
            _read("docs/demo/service_portal_staging_handoff_checklist.md"),
        ]
    )

    expected_groups = ("工作台", "客户开发", "产品与报价", "订单交付", "客户 Portal", "市场响应", "Partner 管理", "演示与资料")
    group_count = sum(1 for label in expected_groups if f"label: '{label}'" in layout)
    checks[0].pass_(f"{group_count} group(s)") if group_count == 8 else checks[0].fail(f"{group_count} group(s)")

    route_markers = (
        "demo-walkthrough",
        "portal-operations",
        "portal-integration",
        "market-response",
        "market-intelligence",
        "orders/:orderId",
        "feedback-tickets",
        "quotes",
        "partner-onboarding",
        "system-health",
        "companies",
        "lead-intelligence",
        "quote-catalog",
        "pricing-preview",
        "knowledge-base",
    )
    ok, missing = _contains_all(router, route_markers)
    checks[1].pass_("core routes present") if ok else checks[1].fail(missing)

    label_markers = (
        "ORDER_STATUS_LABELS",
        "QUOTE_STATUS_LABELS",
        "FEEDBACK_STATUS_LABELS",
        "FEEDBACK_PRIORITY_LABELS",
        "SHIPMENT_STATUS_LABELS",
        "PRODUCTION_STATUS_LABELS",
        "PARTNER_ONBOARDING_STAGE_LABELS",
        "MARKET_SIGNAL_LABELS",
        "PORTAL_READINESS_LABELS",
    )
    ok, missing = _contains_all(zh_copy, label_markers)
    checks[2].pass_("central zhCN maps present") if ok else checks[2].fail(missing)

    loop_markers = ("客户开发", "产品适配", "报价", "订单", "partner 分单", "生产", "物流", "Portal", "反馈", "市场响应")
    ok, missing = _contains_all(demo, loop_markers)
    checks[3].pass_("demo loop covers source-to-response flow") if ok else checks[3].fail(missing)

    partner_markers = ("HOSUN", "JOOBOO", "lifting systems", "education furniture", "future", "多品牌")
    ok, missing = _contains_all("\n".join([demo, partner, docs]), partner_markers)
    checks[4].pass_("HOSUN/JOOBOO/future partner coverage") if ok else checks[4].fail(missing)

    try:
        login = _post_json("/api/auth/login", {"email": "admin@example.com", "password": "admin123"})
        token = str(login["access_token"])
        console = _get_json("/api/v1/portal/operations/console", token)
        audit = console["data"]["forbidden_field_audit"]  # type: ignore[index]
        safety_ok = (
            bool(audit["checked"])  # type: ignore[index]
            and not audit["hits"]  # type: ignore[index]
            and not audit["credential_value_exposed"]  # type: ignore[index]
            and not audit["server_file_path_exposed"]  # type: ignore[index]
            and not audit["cost_fields_exposed"]  # type: ignore[index]
        )
        checks[5].pass_("forbidden-field audit clear") if safety_ok else checks[5].fail("forbidden-field audit not clear")
    except (KeyError, TypeError, HTTPError, URLError, TimeoutError, ValueError) as exc:
        checks[5].fail(f"portal safety request failed: {exc.__class__.__name__}")

    subchecks = []
    for script in (
        "d8_5_demo_environment_check.py",
        "d8_9_partner_onboarding_check.py",
        "d8_10_navigation_localization_check.py",
        "d8_11_chinese_operating_language_check.py",
    ):
        ok, detail = _run_script(script)
        subchecks.append((script, ok, detail))
    failed_subchecks = [name for name, ok, _ in subchecks if not ok]
    checks[6].pass_("all required D8 predecessor checks pass") if not failed_subchecks else checks[6].fail(", ".join(failed_subchecks))

    boundary_text = "\n".join([layout, router, demo, portal, market, orders, order_detail, feedback, partner, docs])
    unsafe = "Status: STAGING_VALIDATED" in boundary_text or "D9 is ready" in boundary_text
    if "READY_FOR_STAGING_HANDOFF" in boundary_text and not unsafe:
        checks[7].pass_("READY_FOR_STAGING_HANDOFF only")
    else:
        checks[7].fail("handoff boundary missing or unsafe")

    forbidden_artifacts = ("IE Auto.pdf", "local_data/", "backend/storage/", "PORTAL_CUSTOMER_API_TOKEN=")
    found = [item for item in forbidden_artifacts if item in "\n".join([layout, router, demo, portal, market, orders, order_detail, feedback, partner])]
    checks[8].pass_("no forbidden artifact references in active UI scope") if not found else checks[8].fail(", ".join(found))

    print("D8.12 Release Candidate Readiness Check")
    print(f"BACKEND_BASE_URL={BACKEND_BASE_URL}")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
