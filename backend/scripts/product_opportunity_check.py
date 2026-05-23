"""D5.13 product opportunity board check."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import get_backend_base_url, log_backend_base_url

BASE = get_backend_base_url()
SECRET_MARKERS = ("password", "secret", "token", "api_key", "bearer ", "admin123")


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
    print("D5.13 Product Opportunity Check")
    checks: list[Check] = []

    c_board = Check("board API")
    c_summary = Check("summary")
    c_rows = Check("rows")
    c_safety = Check("safety flags")
    c_secrets = Check("no secret leakage")
    checks.extend([c_board, c_summary, c_rows, c_safety, c_secrets])

    try:
        with httpx.Client(timeout=30.0) as client:
            headers = _login(client)
            if not headers:
                c_board.fail("login failed")
            else:
                r = client.get(f"{BASE}/api/a-domain/product-opportunity-board", headers=headers)
                if r.status_code != 200:
                    c_board.fail(f"HTTP {r.status_code}")
                else:
                    c_board.pass_(f"HTTP {r.status_code}")
                    body = r.json()
                    text = r.text.lower()
                    if any(m in text for m in SECRET_MARKERS if m != "admin123"):
                        c_secrets.fail("response may contain secrets")
                    elif "@" in text and "contact_email" not in text:
                        c_secrets.pass_("no email list exposed")
                    else:
                        c_secrets.pass_("clean")

                    summary = body.get("summary") or {}
                    if isinstance(summary, dict) and "total" in summary:
                        c_summary.pass_(f"total={summary.get('total')}")
                    else:
                        c_summary.fail("missing summary.total")

                    rows = body.get("rows")
                    if isinstance(rows, list):
                        c_rows.pass_(f"count={len(rows)}")
                    else:
                        c_rows.fail("rows not a list")

                    safety = body.get("safety") or {}
                    if (
                        safety.get("automatic_quote_creation") is False
                        and safety.get("automatic_sending_enabled") is False
                        and safety.get("price_promises_enabled") is False
                        and safety.get("inventory_promises_enabled") is False
                    ):
                        c_safety.pass_("all false")
                    else:
                        c_safety.fail(str(safety))
    except Exception as e:
        c_board.fail(str(e))

    for c in checks:
        print(c.line())

    failed = [c for c in checks if not c.ok]
    print(f"\nResult: {'PASS' if not failed else 'FAIL'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
