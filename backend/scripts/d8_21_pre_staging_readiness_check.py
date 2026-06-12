"""D8.21 pre-staging readiness drill and handoff request pack check."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8014").rstrip("/")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:5173").rstrip("/")
ADMIN_EMAIL = os.getenv("DEMO_LOGIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("DEMO_LOGIN_PASSWORD", "admin123")

FORBIDDEN_PAYLOAD_MARKERS = (
    "internal_cost",
    "margin",
    "pricing_breakdown",
    "pricing_breakdown_json",
    "cost_snapshot",
    "cost_snapshot_json",
    "supplier_private",
    "supplier_private_notes",
    "backend_path",
    "backend file path",
    "storage_key",
    "portal_customer_api_token",
    "internal_only_comments",
    "private_partner_notes",
    "password_hash",
    "backend/storage",
    "local_data",
)


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


def _contains_groups(text: str, groups: tuple[tuple[str, ...], ...]) -> tuple[bool, str]:
    missing = []
    lowered = text.lower()
    for group in groups:
        if not any(item.lower() in lowered for item in group):
            missing.append(" / ".join(group))
    return not missing, ", ".join(missing)


def _request_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    request = Request(url, data=data, headers=request_headers, method=method)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _api_login_token() -> str:
    data = _request_json(
        f"{BACKEND_BASE_URL}/api/auth/login",
        "POST",
        {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    return str(data["access_token"])


def _first_order_id(token: str) -> str | None:
    data = _request_json(
        f"{BACKEND_BASE_URL}/api/v1/orders?limit=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    items = data.get("data", {}).get("items", [])
    if items:
        return str(items[0]["id"])
    return None


def _run_browser_drill(order_id: str | None) -> tuple[bool, str]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        return False, f"playwright unavailable: {exc}"

    route_groups: list[tuple[str, tuple[tuple[str, ...], ...]]] = [
        (
            "/",
            (
                ("每日操作地图", "Workbench", "工作台"),
                ("业务开发", "Customer Development"),
                ("运营交付", "Delivery"),
                ("管理决策", "Management"),
            ),
        ),
        (
            "/growth-operations",
            (
                ("Campaign", "营销活动"),
                ("HOSUN",),
                ("JOOBOO",),
                ("人工外联", "Manual Outreach"),
                ("不自动", "does not automatically", "manual"),
            ),
        ),
        ("/quotes", (("报价", "Quotes"),)),
        ("/orders", (("订单", "Orders"),)),
        (
            "/portal-operations",
            (
                ("Portal",),
                ("客户", "customer"),
                ("READY_FOR_STAGING_HANDOFF", "handoff", "交付"),
            ),
        ),
        (
            "/feedback-tickets",
            (
                ("Feedback", "反馈"),
                ("内部", "internal"),
                ("不通知", "does not notify", "不自动", "不会", "仅记录", "internal"),
            ),
        ),
        (
            "/market-response",
            (
                ("HOSUN lifting systems",),
                ("desk frames",),
                ("desk legs",),
                ("lifting columns",),
                ("heavy-duty supply",),
                ("JOOBOO education furniture", "education furniture"),
                ("project furniture",),
            ),
        ),
        (
            "/partner-onboarding",
            (
                ("HOSUN",),
                ("JOOBOO",),
                ("future", "未来", "Chongqing Huiju", "重庆汇聚"),
                ("readiness", "准备", "就绪"),
            ),
        ),
        (
            "/demo-walkthrough",
            (
                ("客户开发", "Customer Development"),
                ("Campaign", "营销活动"),
                ("人工外联", "Manual Outreach"),
                ("报价", "Quote"),
                ("订单", "Order"),
                ("生产", "Production"),
                ("物流", "Shipment"),
                ("Portal",),
                ("Feedback", "反馈"),
                ("Market Response", "市场响应"),
                ("Partner",),
            ),
        ),
        ("/system-health", (("系统", "System"), ("health", "健康"),)),
    ]
    if order_id:
        route_groups.insert(
            4,
            (
                f"/orders/{order_id}",
                (
                    ("客户可见", "customer-visible"),
                    ("Partner",),
                    ("生产", "Production"),
                    ("物流", "Shipment"),
                    ("反馈", "Feedback"),
                ),
            ),
        )

    console_errors: list[str] = []
    page_errors: list[str] = []
    network_errors: list[str] = []
    failures: list[str] = []

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="msedge", headless=True)
            except PlaywrightError:
                browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on(
                "console",
                lambda msg: console_errors.append(msg.text)
                if msg.type == "error"
                and "favicon" not in msg.text.lower()
                and "failed to load resource" not in msg.text.lower()
                else None,
            )
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.on(
                "response",
                lambda response: network_errors.append(f"{response.status} {response.url}")
                if response.status >= 500
                else None,
            )

            page.goto(f"{FRONTEND_BASE_URL}/login", wait_until="networkidle", timeout=30000)
            page.fill('input[type="email"]', ADMIN_EMAIL)
            page.fill('input[type="password"]', ADMIN_PASSWORD)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1500)
            if "/login" in page.url:
                button = page.locator("button").first
                if button.count():
                    button.click()
                    page.wait_for_timeout(2500)
            if "/login" in page.url:
                failures.append("login did not leave /login")

            for path, marker_groups in route_groups:
                page.goto(f"{FRONTEND_BASE_URL}{path}", wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(500)
                body_text = page.locator("body").inner_text(timeout=10000)
                if not body_text.strip():
                    failures.append(f"{path}: blank body")
                    continue
                ok, missing = _contains_groups(body_text, marker_groups)
                if not ok:
                    failures.append(f"{path}: missing {missing}")

            browser.close()
    except (PlaywrightError, PlaywrightTimeoutError) as exc:
        return False, f"browser drill failed: {exc}"

    fatal = [item for item in console_errors + page_errors + network_errors if item.strip()]
    if failures or fatal:
        detail = "; ".join(failures + [f"fatal browser issue: {item}" for item in fatal[:5]])
        return False, detail[:900]
    return True, f"{len(route_groups)} route(s) checked through UI login"


def _no_forbidden_blob(*payloads: Any) -> tuple[bool, str]:
    blob = json.dumps(payloads, ensure_ascii=False).lower()
    for marker in FORBIDDEN_PAYLOAD_MARKERS:
        if marker in blob:
            return False, marker
    return True, "clean"


def _portal_dry_run() -> tuple[bool, str]:
    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.core.deps import get_current_user
    from app.models import User

    def configure(enabled: bool) -> TestClient:
        os.environ["PORTAL_CUSTOMER_API_ENABLED"] = "true" if enabled else "false"
        os.environ["PORTAL_CUSTOMER_API_REQUIRE_TOKEN"] = "true"
        os.environ["PORTAL_CUSTOMER_API_TOKEN"] = "d8-21-local-dry-run-token"
        os.environ["PORTAL_CUSTOMER_ALLOWED_ORIGINS"] = "https://service.intelli-opus.com"
        os.environ["PUBLIC_BASE_URL"] = "https://partneros-staging.example.invalid"
        get_settings.cache_clear()

        from app.main import create_app

        app = create_app()
        app.dependency_overrides[get_current_user] = lambda: User(
            id=uuid4(),
            email="d8_21_pre_staging@test.example",
            is_active=True,
        )
        return TestClient(app, raise_server_exceptions=False)

    with configure(enabled=False) as client:
        disabled = client.get("/api/v1/portal/customer/products")
        if disabled.status_code != 503:
            return False, f"disabled state expected 503, got {disabled.status_code}"

    with configure(enabled=True) as client:
        missing = client.get("/api/v1/portal/customer/products")
        wrong = client.get(
            "/api/v1/portal/customer/products",
            headers={"X-Portal-Customer-Token": "wrong"},
        )
        disallowed = client.options(
            "/api/v1/portal/customer/products",
            headers={
                "Origin": "https://evil.example.invalid",
                "Access-Control-Request-Method": "GET",
            },
        )
        headers = {"X-Portal-Customer-Token": "d8-21-local-dry-run-token"}
        readiness = client.get("/api/v1/portal/customer/readiness")
        manifest = client.get("/api/v1/portal/customer/manifest", headers=headers)
        products = client.get("/api/v1/portal/customer/products?limit=5", headers=headers)
        orders = client.get("/api/v1/portal/customer/orders?limit=5", headers=headers)
        if missing.status_code != 401:
            return False, f"missing token expected 401, got {missing.status_code}"
        if wrong.status_code != 403:
            return False, f"wrong token expected 403, got {wrong.status_code}"
        if disallowed.headers.get("access-control-allow-origin") == "https://evil.example.invalid":
            return False, "disallowed origin received access-control-allow-origin"
        if readiness.status_code != 200 or manifest.status_code != 200:
            return False, "readiness/manifest unavailable"
        readiness_blob = json.dumps(readiness.json(), ensure_ascii=False).lower()
        if "staging_validated" in readiness_blob or "production ready" in readiness_blob:
            return False, "readiness claims external staging or production readiness"
        if products.status_code != 200 or orders.status_code != 200:
            return False, f"products/orders HTTP {products.status_code}/{orders.status_code}"

        order_items = orders.json().get("data", {}).get("items", [])
        detail = production = shipment = resources = None
        before_status = after_status = None
        if order_items:
            order_id = order_items[0]["id"]
            detail = client.get(f"/api/v1/portal/customer/orders/{order_id}", headers=headers)
            production = client.get(f"/api/v1/portal/customer/orders/{order_id}/production", headers=headers)
            shipment = client.get(f"/api/v1/portal/customer/orders/{order_id}/shipment", headers=headers)
            resources = client.get(f"/api/v1/portal/customer/orders/{order_id}/resources", headers=headers)
            if any(r.status_code != 200 for r in (detail, production, shipment, resources)):
                return False, "order detail/production/shipment/resources dry-run failed"
            before_status = detail.json().get("data", {}).get("status")

        feedback = client.post(
            "/api/v1/portal/customer/feedback",
            headers=headers,
            json={
                "order_id": order_items[0]["id"] if order_items else None,
                "feedback_type": "tracking",
                "subject": "D8.21 pre-staging dry-run feedback",
                "message": "Dry-run only. No automatic customer notification expected.",
                "priority": "normal",
                "customer_name": "D8.21 Dry Run",
                "customer_email": "d8-21-dry-run@example.com",
            },
        )
        if feedback.status_code != 201:
            return False, f"feedback dry-run HTTP {feedback.status_code}"
        feedback_data = feedback.json().get("data", {})
        if feedback_data.get("customer_notified") is not False or feedback_data.get("automatic_reply_sent") is not False:
            return False, "feedback safety flags are not false"
        if order_items:
            order_id = order_items[0]["id"]
            after = client.get(f"/api/v1/portal/customer/orders/{order_id}", headers=headers)
            after_status = after.json().get("data", {}).get("status")
            if before_status != after_status:
                return False, f"portal feedback changed order status {before_status} -> {after_status}"

        payloads = [manifest.json(), products.json(), orders.json(), feedback.json()]
        for response in (detail, production, shipment, resources):
            if response is not None:
                payloads.append(response.json())
        clean, marker = _no_forbidden_blob(*payloads)
        if not clean:
            return False, f"forbidden marker in customer-facing payload: {marker}"
    return True, "disabled/missing/wrong token, origin boundary, payload whitelist, feedback safety OK"


def _document_checks() -> tuple[bool, str]:
    files = {
        "drill": "docs/phase3/d8_21_pre_staging_readiness_drill.md",
        "staging": "docs/phase3/d8_21_staging_request_pack.md",
        "security": "docs/phase3/d8_21_security_review_request.md",
        "uat": "docs/phase3/d8_21_business_uat_request.md",
        "invite": "docs/demo/d8_21_partner_rehearsal_invite.md",
    }
    missing_files = [path for path in files.values() if not (ROOT / path).exists()]
    if missing_files:
        return False, "missing files: " + ", ".join(missing_files)

    drill = _read(files["drill"])
    staging = _read(files["staging"])
    security = _read(files["security"])
    uat = _read(files["uat"])
    invite = _read(files["invite"])
    combined = "\n".join([drill, staging, security, uat, invite])

    required = (
        "READY_FOR_STAGING_HANDOFF",
        "WAITING_FOR_REAL_STAGING_EVIDENCE",
        "backend HTTPS origin",
        "PORTAL_CUSTOMER_API_ENABLED",
        "PORTAL_CUSTOMER_API_TOKEN",
        "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
        "PUBLIC_BASE_URL",
        "service.intelli-opus.com",
        "Token Handling",
        "CORS",
        "Forbidden Fields",
        "Business Owner Decisions Needed",
        "HOSUN",
        "JOOBOO",
        "Chongqing Huiju",
        "future partner",
        "lifting systems",
        "desk frames",
        "desk legs",
        "lifting columns",
        "heavy-duty supply",
        "education furniture",
        "project furniture",
        "Do not automatically",
        "cost",
        "margin",
        "pricing breakdown",
        "supplier private notes",
        "backend file paths",
        "storage keys",
        "token values",
        "internal-only comments",
        "private partner notes",
        "unsafe raw database IDs",
    )
    ok, missing = _contains_all(combined, required)
    if not ok:
        return False, missing

    forbidden_positive_claims = (
        "Current state: STAGING_VALIDATED",
        "External staging state: STAGING_VALIDATED",
        "Status: STAGING_VALIDATED",
        "D9 entered",
        "proof record created",
        "production ready",
    )
    found = [marker for marker in forbidden_positive_claims if marker in combined]
    if found:
        return False, "forbidden positive claim: " + ", ".join(found)
    return True, "5 D8.21 docs complete"


def main() -> int:
    checks = [
        Check("backend/frontend local services"),
        Check("real browser pre-staging drill"),
        Check("Portal bridge customer-safe dry-run"),
        Check("D8.21 request pack documents"),
        Check("D8.20 contract alignment"),
        Check("D8.19 roadmap alignment"),
    ]

    try:
        health = _request_json(f"{BACKEND_BASE_URL}/health")
        front = urlopen(Request(f"{FRONTEND_BASE_URL}/login", method="GET"), timeout=20)
        if health.get("status") == "ok" and front.status == 200:
            checks[0].pass_("backend 8014 and frontend 5173 reachable")
        else:
            checks[0].fail("unexpected health/login response")
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        checks[0].fail(f"local services unavailable: {exc.__class__.__name__}")

    order_id = None
    if checks[0].ok:
        try:
            token = _api_login_token()
            order_id = _first_order_id(token)
        except (HTTPError, URLError, TimeoutError, KeyError, ValueError) as exc:
            checks[1].fail(f"cannot get order id before browser drill: {exc.__class__.__name__}")

    if checks[0].ok and not checks[1].detail:
        ok, detail = _run_browser_drill(order_id)
        checks[1].pass_(detail) if ok else checks[1].fail(detail)

    try:
        ok, detail = _portal_dry_run()
        checks[2].pass_(detail) if ok else checks[2].fail(detail)
    except Exception as exc:  # noqa: BLE001 - smoke script should report any dry-run failure.
        checks[2].fail(f"{exc.__class__.__name__}: {exc}")

    ok, detail = _document_checks()
    checks[3].pass_(detail) if ok else checks[3].fail(detail)

    try:
        d820 = _read("docs/phase3/d8_20_staging_handoff_contract.md")
        ok, missing = _contains_all(
            d820,
            (
                "READY_FOR_STAGING_HANDOFF",
                "WAITING_FOR_REAL_STAGING_EVIDENCE",
                "PORTAL_CUSTOMER_API_TOKEN",
                "Forbidden fields absent",
                "No quote/order status auto-change",
                "HOSUN Lifting Systems Field Preparation",
                "Multi-Partner Expansion Preparation",
            ),
        )
        checks[4].pass_("D8.20 handoff contract remains aligned") if ok else checks[4].fail(missing)
    except FileNotFoundError:
        checks[4].fail("D8.20 contract missing")

    try:
        d819 = _read("docs/phase3/d8_19_feature_gap_and_roadmap.md")
        ok, missing = _contains_all(
            d819,
            (
                "Real service Portal staging validation",
                "RBAC / role permissions",
                "Audit log / operation audit",
                "HOSUN Lifting Systems Gap Analysis",
                "Multi-Partner Expansion Analysis",
            ),
        )
        checks[5].pass_("D8.19 P0 roadmap remains aligned") if ok else checks[5].fail(missing)
    except FileNotFoundError:
        checks[5].fail("D8.19 roadmap missing")

    for check in checks:
        print(check.line())

    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"\nD8.21 pre-staging readiness check failed: {len(failed)} issue(s).", file=sys.stderr)
        return 1

    print("\nD8.21 pre-staging readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
