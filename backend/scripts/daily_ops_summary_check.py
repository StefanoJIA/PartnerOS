"""D5.8 read-only daily operations summary check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()


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


def _login(client: httpx.Client) -> dict[str, str] | None:
    r = client.post(
        f"{BASE}/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    if r.status_code != 200:
        return None
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def main() -> int:
    log_backend_base_url()
    checks: list[Check] = []

    c_route = Check("GET /api/a-domain/daily-ops-summary")
    c_summary = Check("summary counts present")
    c_focus = Check("today_focus array")
    c_safety = Check("safety flags disabled")
    c_actions = Check("quick_actions present")
    c_activity = Check("recent_activity array")
    checks.extend([c_route, c_summary, c_focus, c_safety, c_actions, c_activity])

    try:
        with httpx.Client(timeout=30.0) as client:
            headers = _login(client)
            if not headers:
                c_route.fail("login failed")
            else:
                r = client.get(f"{BASE}/api/a-domain/daily-ops-summary", headers=headers)
                if r.status_code != 200:
                    c_route.fail(f"HTTP {r.status_code}")
                else:
                    c_route.pass_(f"HTTP {r.status_code}")
                    body = r.json()
                    summary = body.get("summary") or {}
                    keys = (
                        "total_leads",
                        "overdue",
                        "due_today",
                        "due_soon",
                        "high_priority",
                        "needs_contact_research",
                        "ready_for_outreach",
                        "waiting_reply",
                        "needs_enrichment",
                    )
                    if all(k in summary for k in keys):
                        c_summary.pass_(f"overdue={summary.get('overdue')}")
                    else:
                        c_summary.fail("missing summary keys")

                    if isinstance(body.get("today_focus"), list):
                        c_focus.pass_(f"count={len(body['today_focus'])}")
                    else:
                        c_focus.fail("today_focus not a list")

                    safety = body.get("safety") or {}
                    if (
                        safety.get("automatic_sending_enabled") is False
                        and safety.get("linkedin_automation_enabled") is False
                        and safety.get("outlook_integration_enabled") is False
                    ):
                        c_safety.pass_("manual only")
                    else:
                        c_safety.fail(str(safety))

                    actions = body.get("quick_actions") or []
                    if len(actions) >= 4:
                        c_actions.pass_(f"count={len(actions)}")
                    else:
                        c_actions.fail(f"count={len(actions)}")

                    if isinstance(body.get("recent_activity"), list):
                        c_activity.pass_(f"count={len(body['recent_activity'])}")
                    else:
                        c_activity.fail("recent_activity not a list")
    except httpx.ConnectError:
        c_route.fail("backend not reachable")

    for c in checks:
        print(c.line())

    failed = [c for c in checks if not c.ok]
    if failed:
        print(f"\nDaily ops summary check: FAIL ({len(failed)} failed)")
        return 1
    print("\nDaily ops summary check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
