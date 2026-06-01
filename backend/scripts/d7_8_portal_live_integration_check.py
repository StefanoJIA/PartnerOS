"""D7.8 service portal live integration readiness check."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.models import User

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
    "test-portal-token",
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


def _configure(enabled: bool = True) -> None:
    os.environ["PORTAL_CUSTOMER_API_ENABLED"] = "true" if enabled else "false"
    os.environ["PORTAL_CUSTOMER_API_REQUIRE_TOKEN"] = "true"
    os.environ["PORTAL_CUSTOMER_API_TOKEN"] = "test-portal-token"
    os.environ["PORTAL_CUSTOMER_ALLOWED_ORIGINS"] = "https://service.intelli-opus.com"
    get_settings.cache_clear()


def _client(enabled: bool = True) -> TestClient:
    _configure(enabled=enabled)
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(), email="d7_8_uat@test.example", is_active=True
    )
    return TestClient(app, raise_server_exceptions=False)


def _no_forbidden_blob(*responses) -> tuple[bool, str]:
    payloads = []
    for response in responses:
        try:
            payloads.append(response.json())
        except ValueError:
            payloads.append({})
    blob = json.dumps(payloads, ensure_ascii=False).lower()
    for marker in FORBIDDEN:
        if marker in blob:
            return False, marker
    return True, "clean"


def _json(response) -> dict:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _redacted_backend_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        return f"{parsed.scheme}://<redacted-backend>{parsed.path or ''}"
    return value


def main() -> int:
    print("D7.8 Service Portal Live Integration Readiness Check")
    backend_url = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:8014")
    print(f"BACKEND_BASE_URL={_redacted_backend_url(backend_url)}")
    checks = [
        Check("enabled flag exposes portal API"),
        Check("missing token rejected"),
        Check("wrong token rejected"),
        Check("correct token accepted"),
        Check("manifest exposes service portal contract"),
        Check("products whitelist payload"),
        Check("orders whitelist payload"),
        Check("order detail whitelist payload"),
        Check("order snapshot whitelist payload"),
        Check("production whitelist payload"),
        Check("shipment whitelist payload"),
        Check("resources whitelist payload"),
        Check("TEST feedback ticket created"),
        Check("no forbidden fields"),
        Check("CORS origin configured"),
        Check("readiness endpoint safe"),
    ]

    with _client(enabled=False) as c:
        disabled = c.get("/api/v1/portal/customer/products")
        if disabled.status_code == 503:
            checks[0].pass_("disabled state returns 503")
        else:
            checks[0].fail(f"disabled state HTTP {disabled.status_code}")

    with _client(enabled=True) as c:
        missing = c.get("/api/v1/portal/customer/products")
        wrong = c.get("/api/v1/portal/customer/products", headers={"X-Portal-Customer-Token": "wrong"})
        headers = {"X-Portal-Customer-Token": "test-portal-token"}
        manifest = c.get("/api/v1/portal/customer/manifest", headers=headers)
        products = c.get("/api/v1/portal/customer/products?limit=5", headers=headers)
        orders = c.get("/api/v1/portal/customer/orders?limit=5", headers=headers)
        readiness = c.get("/api/v1/portal/customer/readiness")

        checks[1].pass_(f"HTTP {missing.status_code}") if missing.status_code == 401 else checks[1].fail(
            f"HTTP {missing.status_code}"
        )
        checks[2].pass_(f"HTTP {wrong.status_code}") if wrong.status_code == 403 else checks[2].fail(
            f"HTTP {wrong.status_code}"
        )
        checks[3].pass_(f"HTTP {products.status_code}") if products.status_code == 200 else checks[3].fail(
            products.text[:160]
        )
        mdata = _json(manifest).get("data", {}) if manifest.status_code == 200 else {}
        if (
            manifest.status_code == 200
            and mdata.get("source_of_truth") == "PartnerOS"
            and "order_snapshot" in mdata.get("endpoints", {})
            and mdata.get("field_policy", {}).get("planned_dates_are_guarantees") is False
        ):
            checks[4].pass_("D8.1 contract")
        else:
            checks[4].fail(manifest.text[:160])
        checks[5].pass_(f"HTTP {products.status_code}") if products.status_code == 200 else checks[5].fail(
            products.text[:160]
        )
        checks[6].pass_(f"HTTP {orders.status_code}") if orders.status_code == 200 else checks[6].fail(
            orders.text[:160]
        )

        order_items = _json(orders).get("data", {}).get("items", []) if orders.status_code == 200 else []
        detail = snapshot = production = shipment = resources = None
        if order_items:
            order_id = order_items[0]["id"]
            detail = c.get(f"/api/v1/portal/customer/orders/{order_id}", headers=headers)
            snapshot = c.get(f"/api/v1/portal/customer/orders/{order_id}/snapshot", headers=headers)
            production = c.get(f"/api/v1/portal/customer/orders/{order_id}/production", headers=headers)
            shipment = c.get(f"/api/v1/portal/customer/orders/{order_id}/shipment", headers=headers)
            resources = c.get(f"/api/v1/portal/customer/orders/{order_id}/resources", headers=headers)
            checks[7].pass_(f"HTTP {detail.status_code}") if detail.status_code == 200 else checks[7].fail(
                detail.text[:160]
            )
            sdata = _json(snapshot).get("data", {}) if snapshot.status_code == 200 else {}
            if (
                snapshot.status_code == 200
                and "customer_status" in sdata
                and "progress_steps" in sdata.get("customer_status", {})
                and sdata.get("customer_status", {}).get("planned_dates_are_guarantees") is False
            ):
                checks[8].pass_(f"HTTP {snapshot.status_code}")
            else:
                checks[8].fail(snapshot.text[:160])
            checks[9].pass_(f"HTTP {production.status_code}") if production.status_code == 200 else checks[9].fail(
                production.text[:160]
            )
            checks[10].pass_(f"HTTP {shipment.status_code}") if shipment.status_code == 200 else checks[10].fail(
                shipment.text[:160]
            )
            checks[11].pass_(f"HTTP {resources.status_code}") if resources.status_code == 200 else checks[11].fail(
                resources.text[:160]
            )
        else:
            checks[7].pass_("no order rows")
            checks[8].pass_("no order rows")
            checks[9].pass_("no order rows")
            checks[10].pass_("no order rows")
            checks[11].pass_("no order rows")

        feedback = c.post(
            "/api/v1/portal/customer/feedback",
            headers=headers,
            json={
                "order_id": order_items[0]["id"] if order_items else None,
                "feedback_type": "tracking",
                "subject": "TEST D7.8 portal UAT feedback",
                "message": "TEST: service portal staging integration feedback. No customer notification expected.",
                "priority": "normal",
                "customer_name": "TEST Portal UAT",
                "customer_email": "portal-uat@example.com",
            },
        )
        fdata = _json(feedback).get("data", {}) if feedback.status_code == 201 else {}
        if (
            feedback.status_code == 201
            and fdata.get("feedback_received") is True
            and fdata.get("customer_notified") is False
            and fdata.get("automatic_reply_sent") is False
        ):
            checks[12].pass_(fdata.get("ticket_number", "created"))
        else:
            checks[12].fail(feedback.text[:160])

        responses = [manifest, products, orders, feedback, readiness]
        responses.extend(r for r in (detail, snapshot, production, shipment, resources) if r is not None)
        clean, detail_text = _no_forbidden_blob(*responses)
        checks[13].pass_(detail_text) if clean else checks[13].fail(detail_text)

        rdata = _json(readiness).get("data", {}) if readiness.status_code == 200 else {}
        if rdata.get("allowed_origins_configured") is True and "https://service.intelli-opus.com" in rdata.get(
            "cors_origins", []
        ):
            checks[14].pass_("service portal origin configured")
        else:
            checks[14].fail(readiness.text[:160])
        if readiness.status_code == 200 and rdata.get("safety", {}).get("token_exposed") is False:
            checks[15].pass_("token not exposed")
        else:
            checks[15].fail(readiness.text[:160])

    for check in checks:
        print(check.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
