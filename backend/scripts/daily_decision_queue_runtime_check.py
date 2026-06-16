"""Runtime check for the Daily Operating Decision Queue.

This is a local internal-beta check. It does not call real staging, send
external messages, record tokens, or claim staging validation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_database_url() -> None:
    if os.getenv("DATABASE_URL"):
        return
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "DATABASE_URL":
            os.environ["DATABASE_URL"] = value.strip().strip('"').strip("'")
            return


_load_database_url()

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import User  # noqa: E402
from app.schemas.dashboard_actions import DailyQueueHandlingUpdate  # noqa: E402
from app.services.daily_decision_queue import build_daily_decision_queue, update_daily_queue_handling  # noqa: E402


def _has_category(items: list, category: str) -> bool:
    return any(item.category == category for item in items)


def main() -> int:
    db = SessionLocal()
    try:
        actor = db.query(User).filter(User.email == "admin@example.com").first()
        if actor is None:
            print("[FAIL] admin actor")
            return 1

        payload = build_daily_decision_queue(db, actor)
        items = payload.items
        safety = payload.safety
        target = items[0]
        handling = update_daily_queue_handling(
            db,
            actor,
            DailyQueueHandlingUpdate(
                queue_item_id=target.id,
                source_type=target.source_type,
                source_id=target.source_id,
                source_path=target.source_path,
                title=target.title,
                category=target.category,
                priority=target.priority,
                partner_focus=target.partner_focus,
                product_focus=target.product_focus,
                customer_or_account=target.customer_or_account,
                action="assign",
                owner=actor.email,
                internal_note="Runtime check: internal handling record only; no external evidence or source status mutation.",
            ),
        )
        refreshed = build_daily_decision_queue(db, actor)
        refreshed_target = next((item for item in refreshed.items if item.id == target.id), None)
        category_targets = {}
        for item in items:
            category_targets.setdefault(item.category, item)
        for category, item in category_targets.items():
            if category == target.category:
                continue
            update_daily_queue_handling(
                db,
                actor,
                DailyQueueHandlingUpdate(
                    queue_item_id=item.id,
                    source_type=item.source_type,
                    source_id=item.source_id,
                    source_path=item.source_path,
                    title=item.title,
                    category=item.category,
                    priority=item.priority,
                    partner_focus=item.partner_focus,
                    product_focus=item.product_focus,
                    customer_or_account=item.customer_or_account,
                    action="acknowledge",
                    owner=actor.email,
                    internal_note=f"Runtime traceability check for {category}.",
                ),
            )
        unsafe_rejected = False
        try:
            update_daily_queue_handling(
                db,
                actor,
                DailyQueueHandlingUpdate(
                    queue_item_id=target.id,
                    source_type=target.source_type,
                    source_id=target.source_id,
                    source_path=target.source_path,
                    title=target.title,
                    category=target.category,
                    priority=target.priority,
                    partner_focus=target.partner_focus,
                    product_focus=target.product_focus,
                    customer_or_account=target.customer_or_account,
                    action="record_decision",
                    handling_status="STAGING_VALIDATED",
                    decision_summary="STAGING_VALIDATED",
                ),
            )
        except ValueError:
            unsafe_rejected = True
        checks = [
            ("status boundary", payload.summary.status == "READY_FOR_STAGING_HANDOFF"),
            ("external staging boundary", payload.summary.external_staging_state == "WAITING_FOR_REAL_STAGING_EVIDENCE"),
            ("queue has actions", len(items) >= 8),
            ("P0/P1 prioritization", any(item.priority == "P0" for item in items) and any(item.priority == "P1" for item in items)),
            ("readiness gap items", _has_category(items, "readiness gap")),
            ("external execution items", _has_category(items, "external execution")),
            ("market response items", _has_category(items, "market response")),
            ("partner onboarding items", _has_category(items, "partner onboarding")),
            ("revenue forecast items", _has_category(items, "revenue forecast")),
            ("order or feedback risk items", any(item.category in {"order delivery", "feedback"} for item in items)),
            ("D9 impact", any(item.affects_d9 for item in items)),
            ("pilot impact", any(item.affects_pilot for item in items)),
            ("staging credential dependency", any(item.needs_staging_credentials for item in items)),
            ("business signoff dependency", any(item.needs_business_signoff for item in items)),
            ("security signoff dependency", any(item.needs_security_signoff for item in items)),
            ("partner feedback dependency", any(item.needs_partner_feedback for item in items)),
            (
                "lifting systems dimensions affect queue",
                any(
                    "lifting systems" in item.product_focus
                    and "load" in item.product_focus
                    and "noise" in item.product_focus
                    and "test cycle" in item.product_focus
                    for item in items
                ),
            ),
            (
                "JOOBOO education furniture peer path",
                any(item.partner_focus == "JOOBOO" or "education furniture" in item.product_focus for item in items),
            ),
            (
                "future partner peer path",
                any((item.partner_focus or "").lower() == "future partner" or "future partner" in item.title.lower() for item in items),
            ),
            (
                "forecast drives operating action",
                any(
                    item.category == "revenue forecast"
                    and "future revenue" in item.readiness_impact
                    and item.customer_or_account
                    and item.source_type.startswith("revenue_forecast_")
                    for item in items
                ),
            ),
            (
                "forecast remains internal-only",
                any(
                    item.category == "revenue forecast"
                    and item.customer_safe_boundary
                    and "internal-only" in item.customer_safe_boundary
                    and not item.needs_staging_credentials
                    for item in items
                ),
            ),
            ("handling record created", handling.queue_item_id == target.id and handling.handling_status == "in_progress"),
            (
                "handling persists after refresh",
                refreshed_target is not None
                and refreshed_target.handling is not None
                and refreshed_target.handling.owner == actor.email,
            ),
            ("unsafe handling claim rejected", unsafe_rejected),
            ("handling summary", refreshed.summary.in_progress >= 1 and refreshed.summary.my_items >= 1),
            (
                "representative category handling records",
                {"external execution", "market response", "partner onboarding"}.issubset(category_targets.keys()),
            ),
            (
                "manual-only safety",
                safety.get("email_sent") is False
                and safety.get("external_api_called") is False
                and safety.get("raw_token_recorded") is False,
            ),
            (
                "no staging or D9 claim",
                safety.get("staging_validated") is False and safety.get("d9_entered") is False,
            ),
            (
                "no automatic status mutation",
                safety.get("quote_status_changed") is False and safety.get("order_status_changed") is False,
            ),
        ]

        app = create_app()
        with TestClient(app) as client:
            login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
            token = login.json()["access_token"]
            response = client.get("/api/dashboard/daily-decision-queue", headers={"Authorization": f"Bearer {token}"})
            patch = client.patch(
                "/api/dashboard/daily-decision-queue/handling",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "queue_item_id": target.id,
                    "source_type": target.source_type,
                    "source_id": target.source_id,
                    "source_path": target.source_path,
                    "title": target.title,
                    "category": target.category,
                    "priority": target.priority,
                    "partner_focus": target.partner_focus,
                    "product_focus": target.product_focus,
                    "customer_or_account": target.customer_or_account,
                    "action": "acknowledge",
                    "owner": actor.email,
                    "internal_note": "HTTP route handling check.",
                },
            )
            filtered = client.get(
                "/api/dashboard/daily-decision-queue/handling",
                headers={"Authorization": f"Bearer {token}"},
                params={"category": target.category},
            )
            source_filtered = client.get(
                "/api/dashboard/daily-decision-queue/handling",
                headers={"Authorization": f"Bearer {token}"},
                params={"source_type": target.source_type, "source_id": target.source_id},
            )
        response_data = response.json() if response.status_code == 200 else {}
        checks.append(("route daily queue", response.status_code == 200 and response_data.get("items")))
        checks.append(("route safety flags", response_data.get("safety", {}).get("staging_validated") is False))
        checks.append(("route handling patch", patch.status_code == 200 and patch.json().get("handling_status") == "acknowledged"))
        checks.append(("route handling category filter", filtered.status_code == 200 and filtered.json()))
        checks.append(("route handling source filter", source_filtered.status_code == 200 and source_filtered.json()[0]["queue_item_id"] == target.id))

        for label, ok in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
