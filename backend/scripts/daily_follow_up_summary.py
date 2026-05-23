"""D5.7 daily follow-up summary CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()


def main() -> int:
    log_backend_base_url()
    with httpx.Client(timeout=30.0) as client:
        login = client.post(
            f"{BASE}/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        if login.status_code != 200:
            print("Login failed")
            return 1
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        r = client.get(f"{BASE}/api/a-domain/follow-up-queue", headers=headers)
        if r.status_code != 200:
            print(f"Follow-up queue failed: {r.status_code}")
            return 1
        body = r.json()
        s = body.get("summary") or {}
        rows = body.get("rows") or []

    print("D5.7 Daily Follow-up Summary")
    print(f"Overdue: {s.get('overdue', 0)}")
    print(f"Due today: {s.get('due_today', 0)}")
    print(f"Due soon: {s.get('due_soon', 0)}")
    print(f"No follow-up date: {s.get('no_follow_up_date', 0)}")
    print(f"Waiting reply: {s.get('waiting_reply', 0)}")
    print("\nTop 10 follow-up actions:")
    priority = {"overdue": 0, "due_today": 1, "due_soon": 2, "no_follow_up_date": 3, "scheduled": 4}

    def sort_key(row: dict) -> tuple:
        return (priority.get(row.get("due_status", "scheduled"), 9), row.get("days_until_due") or 999)

    for i, row in enumerate(sorted(rows, key=sort_key)[:10], start=1):
        company = row.get("company_name", "—")
        status = row.get("due_status", "—")
        action = row.get("next_action") or row.get("recommended_action") or "—"
        print(f"{i}. {company} — {status} — {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
