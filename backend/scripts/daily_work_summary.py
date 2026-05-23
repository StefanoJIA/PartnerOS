"""D5.10 daily work summary CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()


def main() -> int:
    parser = argparse.ArgumentParser(description="D5.10 daily work summary (read-only)")
    parser.add_argument("--date", help="YYYY-MM-DD (default: today from API)")
    args = parser.parse_args()

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
        params = {"date": args.date} if args.date else None
        r = client.get(f"{BASE}/api/a-domain/daily-work-summary", headers=headers, params=params)
        if r.status_code != 200:
            print(f"Daily work summary failed: {r.status_code}")
            return 1
        body = r.json()

    s = body.get("summary") or {}
    print("D5.10 Daily Work Summary")
    print(f"Date: {body.get('date', '—')}")
    print(f"Manual outreach sent: {s.get('manual_outreach_sent', 0)}")
    print(f"Contact research updates: {s.get('contact_research_updates', 0)}")
    print(f"Follow-ups scheduled: {s.get('follow_ups_scheduled', 0)}")
    print(f"Leads touched: {s.get('leads_touched', 0)}")
    drafts = s.get("drafts_generated")
    print(f"Drafts generated: {drafts if drafts is not None else 'not tracked'}")
    print(f"Overdue remaining: {s.get('overdue_remaining', 0)}")
    print(f"Due soon: {s.get('due_soon', 0)}")
    print("\nTomorrow focus:")
    focus = body.get("tomorrow_focus") or []
    if not focus:
        print("  (none)")
    for i, row in enumerate(focus[:10], 1):
        print(f"{i}. {row.get('company_name')} — {row.get('reason')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
