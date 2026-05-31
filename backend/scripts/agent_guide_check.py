"""Validate the root AGENTS.md execution guide."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "AGENTS.md"

REQUIRED_MARKERS = (
    "PartnerOS Agent Guide",
    "internal source of truth",
    "service.intelli-opus.com",
    "Preferred local backend smoke port: `8014`",
    "Docker Postgres: `127.0.0.1:5435`",
    "Never commit `.env`, `local_data/`, `backend/storage/`",
    "Never expose internal cost, margin, pricing breakdowns",
    "Do not auto-send email/webhooks",
    "call carrier APIs",
    "automatically change order status to shipped/delivered",
    "D7.1-D7.6 are complete",
    "D7.7 adds `/api/v1/portal/customer/*`",
    "Feedback tickets do not auto-reply",
    '$env:BACKEND_BASE_URL="http://127.0.0.1:8014"',
    "python scripts/d7_7_portal_bridge_check.py",
    "python scripts/d7_6_shipment_tracking_check.py",
    "python scripts/d7_5_production_milestone_check.py",
    "python scripts/smoke_all_d5.py",
    "python scripts/dev_runtime_doctor.py",
    "python -m pytest -q",
    '$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"',
    "npm run test -- --run",
    "Commit and push only after the requested checks pass",
)
FORBIDDEN_MARKERS = (
    "PORTAL_CUSTOMER_API_TOKEN=",
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
    "Bearer ",
    "raw response body:",
    "password_hash",
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


def _text() -> str:
    try:
        return DOC.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> int:
    checks = [
        Check("AGENTS.md exists"),
        Check("AGENTS.md contains current runtime, D7, and safety guidance"),
        Check("AGENTS.md is redacted"),
    ]

    text = _text()
    checks[0].pass_("AGENTS.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    forbidden.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[2].pass_("no secret-like markers") if not forbidden else checks[2].fail(", ".join(forbidden[:8]))

    print("Agent Guide Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
