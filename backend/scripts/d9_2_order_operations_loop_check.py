"""Validate the D9.2 order operations loop plan."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d9_2_order_operations_loop.md"

REQUIRED_MARKERS = (
    "D9.2 Order Operations Loop",
    "STAGING_VALIDATED",
    "READY_FOR_PRODUCTION_COORDINATION",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "python scripts/d9_2_order_operations_loop_check.py",
    "python scripts/d9_operating_loop_kickoff_check.py",
    "python scripts/d9_operating_records_check.py",
    "docs/records/d9_order_operations_YYYYMMDD.md",
    "Confirmation summary",
    "Partner split summary",
    "Supplier summary",
    "Production summary",
    "Shipment summary",
    "Resource summary",
    "Feedback summary",
    "Owner: TBD` is allowed only as a human owner placeholder",
    "not an auto-assignee, notification target, or permission to create tickets",
    "No customer or supplier notification",
    "No automatic order, production, shipment, delivery, payment, inventory, or partner-selection mutation",
    "No `.env`",
    "No email, webhook, carrier API",
)
FORBIDDEN_MARKERS = (
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "Cookie:",
    "raw response body:",
    "password_hash",
    "database_url",
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


def _missing(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def main() -> int:
    checks = [
        Check("D9.2 order operations doc exists"),
        Check("D9.2 order operations loop is actionable"),
        Check("D9.2 order operations loop is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/d9_2_order_operations_loop.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    forbidden.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[2].pass_("no secret-like markers") if not forbidden else checks[2].fail(", ".join(forbidden))

    print("D9.2 Order Operations Loop Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
