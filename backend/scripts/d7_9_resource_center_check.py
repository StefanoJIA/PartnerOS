"""D7.9 resource center smoke check."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient

FORBIDDEN = (
    "storage_key",
    "backend/storage",
    "uploads/",
    "internal_cost",
    "margin",
    "pricing_breakdown",
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


def _configure() -> None:
    os.environ["PORTAL_CUSTOMER_API_ENABLED"] = "true"
    os.environ["PORTAL_CUSTOMER_API_REQUIRE_TOKEN"] = "true"
    os.environ["PORTAL_CUSTOMER_API_TOKEN"] = "test-portal-token"
    os.environ["PORTAL_CUSTOMER_ALLOWED_ORIGINS"] = "https://service.intelli-opus.com"
    from app.core.config import get_settings

    get_settings.cache_clear()


def _client() -> TestClient:
    _configure()
    from app.main import create_app

    return TestClient(create_app())


def _no_forbidden(*responses) -> tuple[bool, str]:
    blob = json.dumps([r.json() for r in responses if r.headers.get("content-type", "").startswith("application/json")], ensure_ascii=False).lower()
    for marker in FORBIDDEN:
        if marker in blob:
            return False, marker
    return True, "clean"


def main() -> int:
    print("D7.9 Resource Center Check")
    checks = [
        Check("login"),
        Check("find order"),
        Check("upload file"),
        Check("create draft resource"),
        Check("publish resource"),
        Check("internal resource list"),
        Check("portal resource list"),
        Check("signed download"),
        Check("unpublish hides from portal"),
        Check("no forbidden fields"),
    ]

    with _client() as c:
        login = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
        if login.status_code != 200:
            checks[0].fail(f"HTTP {login.status_code}")
            for check in checks:
                print(check.line())
            return 1
        checks[0].pass_("admin@example.com")
        auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
        portal_auth = {"X-Portal-Customer-Token": "test-portal-token"}

        orders = c.get("/api/v1/orders?limit=1", headers=auth)
        items = orders.json().get("data", {}).get("items", []) if orders.status_code == 200 else []
        if not items:
            checks[1].fail("no orders")
            for check in checks:
                print(check.line())
            return 1
        order_id = items[0]["id"]
        checks[1].pass_(items[0].get("order_number", order_id[:8]))

        upload = c.post(
            "/api/files/upload",
            headers=auth,
            files={"upload": ("TEST-d7-9-resource.txt", b"TEST D7.9 customer resource", "text/plain")},
        )
        if upload.status_code == 201:
            checks[2].pass_(upload.json().get("id", "uploaded"))
        else:
            checks[2].fail(upload.text[:160])
            for check in checks:
                print(check.line())
            return 1
        file_id = upload.json()["id"]

        created = c.post(
            f"/api/v1/orders/{order_id}/resources",
            headers=auth,
            json={
                "file_id": file_id,
                "title": "TEST D7.9 customer resource",
                "category": "packing_list",
                "description": "TEST resource for service portal UAT.",
                "customer_visible": False,
            },
        )
        if created.status_code == 201 and created.json().get("data", {}).get("customer_visible") is False:
            checks[3].pass_(created.json()["data"]["id"])
        else:
            checks[3].fail(created.text[:160])
            for check in checks:
                print(check.line())
            return 1
        resource_id = created.json()["data"]["id"]

        published = c.patch(
            f"/api/v1/orders/{order_id}/resources/{resource_id}",
            headers=auth,
            json={"status": "published", "customer_visible": True},
        )
        pdata = published.json().get("data", {}) if published.status_code == 200 else {}
        if published.status_code == 200 and pdata.get("status") == "published" and pdata.get("customer_visible") is True:
            checks[4].pass_("published")
        else:
            checks[4].fail(published.text[:160])

        internal = c.get(f"/api/v1/orders/{order_id}/resources", headers=auth)
        if internal.status_code == 200 and internal.json().get("data", {}).get("total", 0) >= 1:
            checks[5].pass_(f"{internal.json()['data']['total']} resource(s)")
        else:
            checks[5].fail(internal.text[:160])

        portal = c.get(f"/api/v1/portal/customer/orders/{order_id}/resources", headers=portal_auth)
        presources = portal.json().get("data", {}).get("items", []) if portal.status_code == 200 else []
        current = next((r for r in presources if r.get("id") == resource_id), None)
        if current and current.get("download_url") and current.get("safety", {}).get("file_location_exposed") is False:
            checks[6].pass_("download_url present")
        else:
            checks[6].fail(portal.text[:200])

        download = c.get(current["download_url"]) if current else None
        if download is not None and download.status_code == 200 and b"TEST D7.9" in download.content:
            checks[7].pass_("HTTP 200")
        else:
            checks[7].fail(f"HTTP {download.status_code if download is not None else 'none'}")

        hidden = c.patch(
            f"/api/v1/orders/{order_id}/resources/{resource_id}",
            headers=auth,
            json={"status": "draft", "customer_visible": False},
        )
        portal_after = c.get(f"/api/v1/portal/customer/orders/{order_id}/resources", headers=portal_auth)
        after_items = portal_after.json().get("data", {}).get("items", []) if portal_after.status_code == 200 else []
        if hidden.status_code == 200 and not any(r.get("id") == resource_id for r in after_items):
            checks[8].pass_("hidden")
        else:
            checks[8].fail(portal_after.text[:160])

        clean, marker = _no_forbidden(created, published, internal, portal, portal_after)
        checks[9].pass_(marker) if clean else checks[9].fail(marker)

    for check in checks:
        print(check.line())
    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
