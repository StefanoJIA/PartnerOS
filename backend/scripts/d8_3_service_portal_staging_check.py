"""D8.3 HTTP contract check for service.intelli-opus.com staging integration."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import httpx

FORBIDDEN = (
    "internal_cost",
    "margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "supplier_private",
    "supplier_reference",
    "backend_path",
    "storage_key",
    "backend/storage",
    "local_data",
    "portal_customer_api_token",
    "secret_key",
    "password_hash",
)
UNSAFE_TOKENS = {
    "",
    "<portal-server-token>",
    "test-portal-token",
    "dev-portal-token",
    "change-me",
    "d8-integration-hardening-local-token",
}
MIN_TOKEN_LENGTH = 24


class Check:
    def __init__(self, label: str) -> None:
        self.label = label
        self.ok = False
        self.detail = ""

    def pass_(self, detail: str = "") -> None:
        self.ok = True
        self.detail = detail

    def fail(self, detail: str) -> None:
        self.ok = False
        self.detail = detail

    def line(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{status}] {self.label}{suffix}"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _base_url() -> str:
    return os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8014").rstrip("/")


def _portal_token() -> str:
    return (
        os.getenv("SERVICE_PORTAL_PARTNEROS_TOKEN")
        or os.getenv("PORTAL_CUSTOMER_API_TOKEN")
        or "test-portal-token"
    ).strip()


def _origin() -> str:
    return os.getenv("SERVICE_PORTAL_ORIGIN", "https://service.intelli-opus.com").strip()


def _is_placeholder(value: str) -> bool:
    stripped = value.strip()
    return stripped.startswith("<") and stripped.endswith(">") or "<" in stripped or ">" in stripped


def _is_localhost_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "http" and (parsed.hostname or "").lower() in {"localhost", "127.0.0.1", "::1"}


def _redacted_url(value: str) -> str:
    if _is_placeholder(value):
        return "https://<redacted-backend>" if value.startswith("https://") else "<placeholder>"
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.hostname and not _is_localhost_url(value):
        return f"{parsed.scheme}://<redacted-backend>{parsed.path or ''}"
    return value


def _input_issue(base: str, token: str, origin: str) -> str:
    if _is_placeholder(base):
        return "placeholder BACKEND_BASE_URL"
    if not (urlparse(base).scheme == "https" or _is_localhost_url(base)):
        return "BACKEND_BASE_URL must be HTTPS or local rehearsal HTTP"
    if not token or token in UNSAFE_TOKENS or _is_placeholder(token) or len(token) < MIN_TOKEN_LENGTH:
        return "SERVICE_PORTAL_PARTNEROS_TOKEN must be non-default and private"
    if _is_placeholder(origin) or urlparse(origin).scheme != "https":
        return "SERVICE_PORTAL_ORIGIN must be a real HTTPS origin"
    return ""


def _json(response: httpx.Response | None) -> Any:
    if response is None:
        return {}
    try:
        return response.json()
    except ValueError:
        return {}


def _finish(*, checks: list[Check], base: str, origin: str, create_feedback: bool) -> int:
    print("D8.3 Service Portal Staging Contract Check")
    print(f"BACKEND_BASE_URL={_redacted_url(base)}")
    print(f"SERVICE_PORTAL_ORIGIN={origin}")
    print(f"create_test_feedback={create_feedback}")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def no_forbidden_blob(*responses: httpx.Response | dict[str, Any] | None, token: str = "") -> tuple[bool, str]:
    payloads: list[Any] = []
    for response in responses:
        if response is None:
            continue
        payloads.append(_json(response) if isinstance(response, httpx.Response) else response)
    blob = json.dumps(payloads, ensure_ascii=False).lower()
    for marker in FORBIDDEN:
        if marker in blob:
            return False, marker
    if token and token.lower() in blob:
        return False, "portal token leaked"
    return True, "clean"


def _get(client: httpx.Client, path: str, headers: dict[str, str] | None = None) -> httpx.Response | None:
    try:
        return client.get(f"{_base_url()}/api/v1/portal/customer{path}", headers=headers)
    except httpx.HTTPError:
        return None


def main() -> int:
    base = _base_url()
    token = _portal_token()
    origin = _origin()
    create_feedback = _truthy(os.getenv("D8_3_CREATE_TEST_FEEDBACK"))
    headers = {"X-Portal-Customer-Token": token}

    checks = [
        Check("backend reachable"),
        Check("missing token rejected"),
        Check("wrong token rejected"),
        Check("CORS preflight allows service portal origin"),
        Check("manifest endpoint"),
        Check("products endpoint"),
        Check("orders endpoint"),
        Check("order detail endpoint"),
        Check("order snapshot endpoint"),
        Check("production endpoint"),
        Check("shipment endpoint"),
        Check("resources endpoint"),
        Check("optional TEST feedback"),
        Check("no forbidden fields or token leakage"),
    ]

    input_issue = _input_issue(base, token, origin)
    if input_issue:
        checks[0].fail(input_issue)
        for check in checks[1:]:
            check.fail("not attempted; staging inputs unsafe")
        return _finish(checks=checks, base=base, origin=origin, create_feedback=create_feedback)

    responses: list[httpx.Response | None] = []
    order_items: list[dict[str, Any]] = []
    with httpx.Client(timeout=15.0) as client:
        try:
            health = client.get(f"{base}/health")
        except httpx.HTTPError as exc:
            checks[0].fail(str(exc)[:120])
            for check in checks[1:]:
                check.fail("not attempted; backend unreachable")
            return _finish(checks=checks, base=base, origin=origin, create_feedback=create_feedback)
        checks[0].pass_(f"HTTP {health.status_code}") if health.status_code == 200 else checks[0].fail(
            f"HTTP {health.status_code}"
        )

        missing = _get(client, "/products?limit=1")
        wrong = _get(client, "/products?limit=1", headers={"X-Portal-Customer-Token": "wrong"})
        responses.extend([missing, wrong])
        checks[1].pass_(f"HTTP {missing.status_code}") if missing and missing.status_code == 401 else checks[1].fail(
            f"HTTP {missing.status_code if missing else 'unreachable'}"
        )
        checks[2].pass_(f"HTTP {wrong.status_code}") if wrong and wrong.status_code == 403 else checks[2].fail(
            f"HTTP {wrong.status_code if wrong else 'unreachable'}"
        )

        try:
            preflight = client.options(
                f"{base}/api/v1/portal/customer/products",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "x-portal-customer-token",
                },
            )
        except httpx.HTTPError as exc:
            preflight = None
            checks[3].fail(str(exc)[:120])
        else:
            allowed_origin = preflight.headers.get("access-control-allow-origin", "")
            if preflight.status_code in {200, 204} and allowed_origin == origin:
                checks[3].pass_(origin)
            else:
                checks[3].fail(f"HTTP {preflight.status_code} allow-origin={allowed_origin or 'missing'}")
        responses.append(preflight)

        manifest = _get(client, "/manifest", headers=headers)
        products = _get(client, "/products?limit=5", headers=headers)
        orders = _get(client, "/orders?limit=5", headers=headers)
        responses.extend([manifest, products, orders])
        manifest_data = (_json(manifest).get("data") or {}) if manifest and manifest.status_code == 200 else {}
        if (
            manifest
            and manifest.status_code == 200
            and manifest_data.get("source_of_truth") == "PartnerOS"
            and "order_snapshot" in manifest_data.get("endpoints", {})
            and manifest_data.get("field_policy", {}).get("planned_dates_are_guarantees") is False
        ):
            checks[4].pass_("D8.1 contract")
        else:
            checks[4].fail(f"HTTP {manifest.status_code if manifest else 'unreachable'}")
        checks[5].pass_(f"HTTP {products.status_code}") if products and products.status_code == 200 else checks[
            5
        ].fail(f"HTTP {products.status_code if products else 'unreachable'}")
        checks[6].pass_(f"HTTP {orders.status_code}") if orders and orders.status_code == 200 else checks[6].fail(
            f"HTTP {orders.status_code if orders else 'unreachable'}"
        )

        if orders and orders.status_code == 200:
            order_items = ((_json(orders).get("data") or {}).get("items") or [])[:1]
        if order_items:
            order_id = order_items[0]["id"]
            detail = _get(client, f"/orders/{order_id}", headers=headers)
            snapshot = _get(client, f"/orders/{order_id}/snapshot", headers=headers)
            production = _get(client, f"/orders/{order_id}/production", headers=headers)
            shipment = _get(client, f"/orders/{order_id}/shipment", headers=headers)
            resources = _get(client, f"/orders/{order_id}/resources", headers=headers)
            responses.extend([detail, snapshot, production, shipment, resources])
            if detail and detail.status_code == 200:
                checks[7].pass_(f"HTTP {detail.status_code}")
            else:
                checks[7].fail(f"HTTP {detail.status_code if detail else 'unreachable'}")
            snapshot_data = (_json(snapshot).get("data") or {}) if snapshot and snapshot.status_code == 200 else {}
            if (
                snapshot
                and snapshot.status_code == 200
                and "customer_status" in snapshot_data
                and "progress_steps" in snapshot_data.get("customer_status", {})
                and bool(snapshot_data.get("customer_status", {}).get("next_action_label"))
                and "tracking_summary" in snapshot_data
                and snapshot_data.get("customer_status", {}).get("planned_dates_are_guarantees") is False
                and snapshot_data.get("tracking_summary", {}).get("planned_dates_are_guarantees") is False
            ):
                checks[8].pass_(f"HTTP {snapshot.status_code}")
            else:
                checks[8].fail(f"HTTP {snapshot.status_code if snapshot else 'unreachable'}")
            for idx, response in ((9, production), (10, shipment), (11, resources)):
                if response and response.status_code == 200:
                    checks[idx].pass_(f"HTTP {response.status_code}")
                else:
                    checks[idx].fail(f"HTTP {response.status_code if response else 'unreachable'}")
        else:
            for idx in (7, 8, 9, 10, 11):
                checks[idx].pass_("no order rows")

        if create_feedback:
            feedback = client.post(
                f"{base}/api/v1/portal/customer/feedback",
                headers=headers,
                json={
                    "order_id": order_items[0]["id"] if order_items else None,
                    "feedback_type": "tracking",
                    "subject": "TEST D8.3 service portal staging feedback",
                    "message": "TEST: D8.3 staging contract runner. No customer notification expected.",
                    "priority": "normal",
                    "customer_name": "TEST Service Portal",
                    "customer_email": "portal-staging@example.com",
                },
            )
            responses.append(feedback)
            data = (_json(feedback).get("data") or {}) if feedback.status_code == 201 else {}
            if (
                feedback.status_code == 201
                and data.get("feedback_received") is True
                and data.get("customer_notified") is False
            ):
                checks[12].pass_(data.get("ticket_number", "created"))
            else:
                checks[12].fail(f"HTTP {feedback.status_code}")
        else:
            checks[12].pass_("skipped; set D8_3_CREATE_TEST_FEEDBACK=true")

    clean, detail = no_forbidden_blob(*responses, token=token)
    checks[13].pass_(detail) if clean else checks[13].fail(detail)

    return _finish(checks=checks, base=base, origin=origin, create_feedback=create_feedback)


if __name__ == "__main__":
    raise SystemExit(main())
