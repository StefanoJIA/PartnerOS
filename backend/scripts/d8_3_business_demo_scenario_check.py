"""D8.3 business demo scenario readiness check.

Read-only HTTP check for the PartnerOS business walkthrough:
product interest -> quote -> order -> partner split -> production -> shipment -> feedback -> market response.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx


BASE = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8014").rstrip("/")
ADMIN_EMAIL = os.getenv("DEMO_LOGIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("DEMO_LOGIN_PASSWORD", "admin123")


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


def _data(resp: httpx.Response) -> Any:
    resp.raise_for_status()
    body = resp.json()
    return body.get("data", body)


def _contains_partner(rows: list[dict[str, Any]], markers: tuple[str, ...]) -> bool:
    for row in rows:
        name = str(row.get("partner_name") or "").upper()
        if any(marker in name for marker in markers):
            return True
    return False


def main() -> int:
    checks = [
        Check("login"),
        Check("business loop counts"),
        Check("HOSUN partner direction"),
        Check("second partner direction"),
        Check("Portal operations demo data"),
        Check("Market signal explanations"),
        Check("customer-visible safety boundary"),
        Check("state boundary remains handoff-only"),
    ]

    with httpx.Client(timeout=30.0) as client:
        try:
            login = client.post(f"{BASE}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
            token = login.json().get("access_token") if login.status_code == 200 else None
            if not token:
                checks[0].fail(f"HTTP {login.status_code}")
                for check in checks:
                    print(check.line())
                return 1
            headers = {"Authorization": f"Bearer {token}"}
            checks[0].pass_("token received; value not printed")

            portal = _data(client.get(f"{BASE}/api/v1/portal/operations/console", headers=headers))
            market = _data(client.get(f"{BASE}/api/v1/market/response-intelligence", headers=headers))
            orders = _data(client.get(f"{BASE}/api/v1/orders", headers=headers, params={"limit": 5}))
            quotes = _data(client.get(f"{BASE}/api/v1/quotes", headers=headers, params={"limit": 5}))
            feedback = _data(client.get(f"{BASE}/api/v1/feedback-tickets", headers=headers, params={"limit": 5}))
        except Exception as exc:  # noqa: BLE001
            checks[1].fail(str(exc)[:160])
            for check in checks:
                print(check.line())
            return 1

    order_count = int(market["summary"]["order_count"])
    quote_count = int(market["summary"]["quote_count"])
    feedback_count = int(market["summary"]["feedback_ticket_count"])
    preview_count = int(portal["market_signal_preview"]["total"])
    if orders["total"] and quotes["total"] and feedback["total"] and order_count and quote_count and feedback_count:
        checks[1].pass_(f"orders={order_count}; quotes={quote_count}; feedback={feedback_count}; previews={preview_count}")
    else:
        checks[1].fail("missing order, quote, or feedback data for walkthrough")

    partner_rows = list(portal["multi_partner_flow_readiness"]["items"])
    if _contains_partner(partner_rows, ("HOSUN",)):
        checks[2].pass_("HOSUN present as peer partner")
    else:
        checks[2].fail("HOSUN partner direction missing")

    if _contains_partner(partner_rows, ("JOOBOO", "HUIJU", "EDUCATION")) or len(partner_rows) >= 2:
        checks[3].pass_("second partner/future partner direction present")
    else:
        checks[3].fail("second partner direction missing")

    portal_recent_orders = int(portal["recent_customer_visible_orders"]["total"])
    shipment_total = int(portal["shipment_readiness"]["total_count"])
    open_feedback = int(portal["feedback_operations"]["open_count"])
    if portal_recent_orders and shipment_total and open_feedback >= 0 and preview_count:
        checks[4].pass_(f"recent_orders={portal_recent_orders}; shipments={shipment_total}; open_feedback={open_feedback}")
    else:
        checks[4].fail("Portal Operations lacks recent orders, shipments, feedback, or market preview")

    focus_keys = {row["key"] for row in portal["market_signal_preview"]["items"]}
    required_focus = {"adjustable_desk_frames", "desk_legs", "lifting_columns", "education_furniture"}
    recommendations = market.get("recommendations") or []
    if required_focus.issubset(focus_keys) and recommendations:
        checks[5].pass_(f"focus={','.join(sorted(required_focus))}; recommendations={len(recommendations)}")
    else:
        checks[5].fail("missing HOSUN/JOOBOO focus rows or market recommendations")

    safety = portal["safety"]
    portal_contract_safety = portal["portal_contract"]["safety"]
    forbidden = portal["forbidden_field_audit"]
    unsafe = (
        safety["customer_notified"]
        or safety["supplier_notified"]
        or safety["automatic_reply_sent"]
        or safety["carrier_api_called"]
        or safety["order_status_mutated"]
        or portal_contract_safety["token_value_exposed"]
        or bool(forbidden["hits"])
    )
    if not unsafe:
        checks[6].pass_("no customer/supplier notification, carrier call, token leak, or forbidden-field hit")
    else:
        checks[6].fail("unsafe customer-visible boundary flag detected")

    launch_safety = portal["portal_launch_readiness"]["safety"]
    checklist_safety = portal["staging_integration_checklist"]["safety"]
    if not launch_safety["staging_validated"] and not checklist_safety["proof_record_created"]:
        checks[7].pass_("READY_FOR_STAGING_HANDOFF only; no staging validation/proof record")
    else:
        checks[7].fail("staging/proof boundary violated")

    print("D8.3 Business Demo Scenario Check")
    print(f"BACKEND_BASE_URL={BASE}")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
