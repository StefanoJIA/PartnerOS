"""D8.5 demo environment hardening check.

Ensures the repeatable business walkthrough has stable demo data, live API
coverage, customer-visible order detail, feedback operations, and frontend route
availability. The seed step is idempotent demo data only.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(BACKEND_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT / "scripts"))

from d8_3_business_demo_seed import ORDER_NUMBER, main as seed_demo  # noqa: E402


BASE = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8014").rstrip("/")
FRONTEND_BASE = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:5173").rstrip("/")
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


def _partner_present(rows: list[dict[str, Any]], *markers: str) -> bool:
    for row in rows:
        name = str(row.get("partner_name") or "").upper()
        if any(marker.upper() in name for marker in markers):
            return True
    return False


def _frontend_ok(client: httpx.Client, path: str) -> tuple[bool, str]:
    resp = client.get(f"{FRONTEND_BASE}{path}")
    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}"
    text = resp.text
    if '<div id="app"></div>' not in text:
        return False, "missing Vue app shell"
    return True, f"HTTP {resp.status_code}"


def main() -> int:
    checks = [
        Check("idempotent demo seed"),
        Check("backend health"),
        Check("login"),
        Check("frontend routes"),
        Check("HOSUN and JOOBOO stable scenarios"),
        Check("Portal Operations demo readiness"),
        Check("Market Response explanations"),
        Check("Order Detail customer-visible summary"),
        Check("Feedback Tickets list/detail/update"),
        Check("customer-visible safety boundary"),
        Check("state boundary remains handoff-only"),
    ]

    try:
        seed_rc = seed_demo()
        checks[0].pass_("D8.3 demo seed ensured") if seed_rc == 0 else checks[0].fail(f"seed rc={seed_rc}")
    except Exception as exc:  # noqa: BLE001
        checks[0].fail(str(exc)[:180])

    headers: dict[str, str] = {}
    portal: dict[str, Any] = {}
    market: dict[str, Any] = {}
    order_detail: dict[str, Any] = {}
    feedback_list: dict[str, Any] = {}
    feedback_detail: dict[str, Any] = {}
    feedback_update: dict[str, Any] = {}

    with httpx.Client(timeout=30.0) as client:
        try:
            health = client.get(f"{BASE}/health")
            health_data = health.json()
            if health.status_code == 200 and health_data.get("status") == "ok" and not health_data.get("migration_pending"):
                checks[1].pass_(f"db={health_data.get('database_status')}; rev={health_data.get('alembic_current_revision')}")
            else:
                checks[1].fail(f"HTTP {health.status_code}: {health.text[:120]}")
        except Exception as exc:  # noqa: BLE001
            checks[1].fail(str(exc)[:160])

        try:
            login = client.post(f"{BASE}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
            token = login.json().get("access_token") if login.status_code == 200 else None
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                checks[2].pass_("token received; value not printed")
            else:
                checks[2].fail(f"HTTP {login.status_code}")
        except Exception as exc:  # noqa: BLE001
            checks[2].fail(str(exc)[:160])

        frontend_paths = [
            "/",
            "/demo-walkthrough",
            "/portal-operations",
            "/market-response",
            "/orders",
            "/feedback-tickets",
            "/quotes",
            "/system-health",
        ]
        frontend_failures: list[str] = []
        for path in frontend_paths:
            try:
                ok, detail = _frontend_ok(client, path)
                if not ok:
                    frontend_failures.append(f"{path}:{detail}")
            except Exception as exc:  # noqa: BLE001
                frontend_failures.append(f"{path}:{str(exc)[:80]}")
        checks[3].pass_(f"{len(frontend_paths)} route(s)") if not frontend_failures else checks[3].fail("; ".join(frontend_failures[:4]))

        if headers:
            try:
                portal = _data(client.get(f"{BASE}/api/v1/portal/operations/console", headers=headers))
                market = _data(client.get(f"{BASE}/api/v1/market/response-intelligence", headers=headers))
                feedback_list = _data(client.get(f"{BASE}/api/v1/feedback-tickets", headers=headers, params={"limit": 20}))
            except Exception as exc:  # noqa: BLE001
                checks[5].fail(str(exc)[:160])

    partner_rows = list((portal.get("multi_partner_flow_readiness") or {}).get("items") or [])
    if _partner_present(partner_rows, "HOSUN") and _partner_present(partner_rows, "JOOBOO", "EDUCATION"):
        checks[4].pass_("HOSUN + JOOBOO present")
    else:
        checks[4].fail("missing HOSUN or JOOBOO partner row")

    portal_ready = portal.get("portal_launch_readiness") or {}
    recent = portal.get("recent_customer_visible_orders") or {}
    shipments = portal.get("shipment_readiness") or {}
    feedback_ops = portal.get("feedback_operations") or {}
    market_preview = portal.get("market_signal_preview") or {}
    if (
        recent.get("total", 0) > 0
        and shipments.get("total_count", 0) > 0
        and feedback_ops.get("open_count", -1) >= 0
        and market_preview.get("total", 0) > 0
        and portal_ready.get("safety", {}).get("read_only") is True
    ):
        checks[5].pass_(
            f"orders={recent.get('total')}; shipments={shipments.get('total_count')}; "
            f"feedback={feedback_ops.get('open_count')}; signals={market_preview.get('total')}"
        )
    elif not checks[5].detail:
        checks[5].fail("missing portal status, orders, shipments, feedback, or market signal")

    focus_keys = {row.get("key") for row in market_preview.get("items") or []}
    recommendations = market.get("recommendations") or []
    focus_required = {"adjustable_desk_frames", "desk_legs", "lifting_columns", "education_furniture"}
    if focus_required.issubset(focus_keys) and recommendations:
        checks[6].pass_(f"focus={','.join(sorted(focus_required))}; recommendations={len(recommendations)}")
    else:
        checks[6].fail("missing focus explanations or recommendations")

    demo_order = next((row for row in recent.get("items") or [] if row.get("order_number") == ORDER_NUMBER), None)
    demo_order = demo_order or next(iter(recent.get("items") or []), None)
    if headers and demo_order:
        with httpx.Client(timeout=30.0) as client:
            try:
                order_detail = _data(client.get(f"{BASE}/api/v1/orders/{demo_order['id']}", headers=headers))
            except Exception as exc:  # noqa: BLE001
                checks[7].fail(str(exc)[:160])

    production = order_detail.get("production_summary") or {}
    shipment = order_detail.get("shipment_summary") or {}
    if production.get("total_milestones", 0) > 0 and shipment.get("total_plans", 0) > 0:
        checks[7].pass_(
            f"order={order_detail.get('order_number')}; production={production.get('completed_milestones')}/{production.get('total_milestones')}; "
            f"shipments={shipment.get('active_plans')}/{shipment.get('total_plans')}"
        )
    elif not checks[7].detail:
        checks[7].fail("missing production or shipment summary")

    ticket = next((row for row in feedback_list.get("items") or [] if row.get("ticket_number") in {"FB-D83-HOSUN", "FB-D83-JOOBOO"}), None)
    ticket = ticket or next(iter(feedback_list.get("items") or []), None)
    if headers and ticket:
        with httpx.Client(timeout=30.0) as client:
            try:
                feedback_detail = _data(client.get(f"{BASE}/api/v1/feedback-tickets/{ticket['id']}", headers=headers))
                feedback_update = _data(
                    client.patch(
                        f"{BASE}/api/v1/feedback-tickets/{ticket['id']}",
                        headers=headers,
                        json={
                            "status": feedback_detail.get("status") or "in_review",
                            "priority": feedback_detail.get("priority") or "normal",
                            "internal_owner": feedback_detail.get("internal_owner") or "D8.5 demo operator",
                            "response_summary": feedback_detail.get("response_summary")
                            or "D8.5 demo check verified internal handling flow.",
                        },
                    )
                )
            except Exception as exc:  # noqa: BLE001
                checks[8].fail(str(exc)[:160])

    update_safety = feedback_update.get("safety") or {}
    update_operation = feedback_update.get("operation") or {}
    if (
        feedback_list.get("total", 0) > 0
        and feedback_detail.get("id")
        and feedback_update.get("id")
        and update_operation.get("internal_handling_only") is True
        and not update_safety.get("customer_notified")
        and not update_safety.get("automatic_reply_sent")
    ):
        checks[8].pass_(f"ticket={feedback_update.get('ticket_number')}; internal update ok")
    elif not checks[8].detail:
        checks[8].fail("feedback list/detail/update not demo-ready")

    safety = portal.get("safety") or {}
    contract_safety = (portal.get("portal_contract") or {}).get("safety") or {}
    forbidden = portal.get("forbidden_field_audit") or {}
    unsafe = (
        safety.get("customer_notified")
        or safety.get("supplier_notified")
        or safety.get("automatic_reply_sent")
        or safety.get("carrier_api_called")
        or safety.get("order_status_mutated")
        or contract_safety.get("token_value_exposed")
        or bool(forbidden.get("hits"))
    )
    if not unsafe:
        checks[9].pass_("no notification, carrier, token, forbidden-field, or status-mutation hit")
    else:
        checks[9].fail("unsafe customer-visible boundary flag detected")

    launch_safety = portal_ready.get("safety") or {}
    checklist_safety = (portal.get("staging_integration_checklist") or {}).get("safety") or {}
    if not launch_safety.get("staging_validated") and not checklist_safety.get("proof_record_created"):
        checks[10].pass_("READY_FOR_STAGING_HANDOFF only; no staging validation/proof record")
    else:
        checks[10].fail("staging/proof boundary violated")

    print("D8.5 Demo Environment Check")
    print(f"BACKEND_BASE_URL={BASE}")
    print(f"FRONTEND_BASE_URL={FRONTEND_BASE}")
    for check in checks:
        print(check.line())
    failed = [check for check in checks if not check.ok]
    print("Result: " + ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

