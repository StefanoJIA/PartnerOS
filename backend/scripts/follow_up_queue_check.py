"""D5.7 read-only follow-up queue check."""

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
    print("D5.7 Follow-up Queue Check")
    checks = [
        Check("follow-up queue API accessible"),
        Check("summary contract"),
        Check("rows contract"),
        Check("due status variety"),
        Check("no automatic sending"),
    ]

    with httpx.Client(timeout=30.0) as client:
        headers = _login(client)
        if not headers:
            for c in checks:
                c.fail("login failed")
            for c in checks:
                print(c.line())
            print("\nResult: FAIL")
            return 1

        r = client.get(f"{BASE}/api/a-domain/follow-up-queue", headers=headers)
        if r.status_code != 200:
            checks[0].fail(r.text[:200])
        else:
            checks[0].pass_()
            body = r.json()
            summary = body.get("summary") or {}
            rows = body.get("rows") or []

            if all(k in summary for k in ("total", "overdue", "due_today", "due_soon", "no_follow_up_date", "waiting_reply")):
                checks[1].pass_(f"total={summary.get('total')}")
            else:
                checks[1].fail("missing summary keys")

            if isinstance(rows, list):
                checks[2].pass_(f"{len(rows)} rows")
            else:
                checks[2].fail("rows not a list")

            statuses = {row.get("due_status") for row in rows}
            if statuses & {"no_follow_up_date", "scheduled", "due_soon", "overdue", "due_today"} or summary.get("total", 0) == 0:
                checks[3].pass_(f"statuses={sorted(statuses)}")
            else:
                checks[3].fail(f"unexpected statuses {statuses}")

            blob = r.text.lower()
            if "automatically_sent" not in blob and "outlook" not in blob:
                checks[4].pass_("manual scheduling only")
            else:
                checks[4].fail("unexpected auto-send wording")

    for c in checks:
        print(c.line())
    ok = all(c.ok for c in checks)
    print(f"\nResult: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
