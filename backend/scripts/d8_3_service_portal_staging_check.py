"""D8.3 HTTP contract check for service.intelli-opus.com staging integration."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

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
    "storage_key",
    "backend/storage",
    "portal_customer_api_token",
    "secret_key",
    "password_hash",
)


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


def _json(response: httpx.Response | None) -> Any:
    if response is None:
        return {}
    try:
        return response.json()
    except ValueError:
        return {}


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
        Check("products endpoint"),
        Check("orders endpoint"),
        Check("order detail endpoint"),
        Check("production endpoint"),
        Check("shipment endpoint"),
        Check("resources endpoint"),
        Check("optional TEST feedback"),
        Check("no forbidden fields or token leakage"),
    ]

    responses: list[httpx.Response | None] = []
    order_items: list[dict[str, Any]] = []
    with httpx.Client(timeout=15.0) as client:
        try:
            health = client.get(f"{base}/health")
        except httpx.HTTPError as exc:
            checks[0].fail(str(exc)[:120])
            for check in checks:
                print(check.line())
            print("Result: FAIL")
            return 1
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

        preflight = client.options(
            f"{base}/api/v1/portal/customer/products",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "x-portal-customer-token",
            },
        )
        allowed_origin = preflight.headers.get("access-control-allow-origin", "")
        if preflight.status_code in {200, 204} and allowed_origin == origin:
            checks[3].pass_(origin)
        else:
            checks[3].fail(f"HTTP {preflight.status_code} allow-origin={allowed_origin or 'missing'}")

        products = _get(client, "/products?limit=5", headers=headers)
        orders = _get(client, "/orders?limit=5", headers=headers)
        responses.extend([products, orders])
        checks[4].pass_(f"HTTP {products.status_code}") if products and products.status_code == 200 else checks[
            4
        ].fail(f"HTTP {products.status_code if products else 'unreachable'}")
        checks[5].pass_(f"HTTP {orders.status_code}") if orders and orders.status_code == 200 else checks[5].fail(
            f"HTTP {orders.status_code if orders else 'unreachable'}"
        )

        if orders and orders.status_code == 200:
            order_items = ((_json(orders).get("data") or {}).get("items") or [])[:1]
        if order_items:
            order_id = order_items[0]["id"]
            detail = _get(client, f"/orders/{order_id}", headers=headers)
            production = _get(client, f"/orders/{order_id}/production", headers=headers)
            shipment = _get(client, f"/orders/{order_id}/shipment", headers=headers)
            resources = _get(client, f"/orders/{order_id}/resources", headers=headers)
            responses.extend([detail, production, shipment, resources])
            for idx, response in ((6, detail), (7, production), (8, shipment), (9, resources)):
                if response and response.status_code == 200:
                    checks[idx].pass_(f"HTTP {response.status_code}")
                else:
                    checks[idx].fail(f"HTTP {response.status_code if response else 'unreachable'}")
        else:
            for idx in (6, 7, 8, 9):
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
                checks[10].pass_(data.get("ticket_number", "created"))
            else:
                checks[10].fail(f"HTTP {feedback.status_code}")
        else:
            checks[10].pass_("skipped; set D8_3_CREATE_TEST_FEEDBACK=true")

    clean, detail = no_forbidden_blob(*responses, token=token)
    checks[11].pass_(detail) if clean else checks[11].fail(detail)

    print("D8.3 Service Portal Staging Contract Check")
    print(f"BACKEND_BASE_URL={base}")
    print(f"SERVICE_PORTAL_ORIGIN={origin}")
    print(f"create_test_feedback={create_feedback}")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
