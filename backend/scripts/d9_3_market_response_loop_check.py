"""Validate the D9.3 market response loop plan."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d9_3_market_response_loop.md"

REQUIRED_MARKERS = (
    "D9.3 Market Response Loop",
    "STAGING_VALIDATED",
    "READY_FOR_PRODUCTION_COORDINATION",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "python scripts/d9_3_market_response_loop_check.py",
    "python scripts/d9_operating_loop_kickoff_check.py",
    "python scripts/d9_operating_records_check.py",
    "docs/records/d9_market_response_YYYYMMDD.md",
    "Feedback summary",
    "Quote outcome summary",
    "Product gap summary",
    "Demand summary",
    "Partner-fit summary",
    "Advisory summary",
    "advisory planning loop",
    "Owner: TBD` is allowed only as a human owner placeholder",
    "not an auto-assignee, notification target, or permission to create tickets",
    "No automatic customer reply",
    "No automatic pricing, product, quote, order, shipment, payment, inventory, or partner-selection mutation",
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
        Check("D9.3 market response doc exists"),
        Check("D9.3 market response loop is actionable"),
        Check("D9.3 market response loop is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/d9_3_market_response_loop.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    forbidden.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[2].pass_("no secret-like markers") if not forbidden else checks[2].fail(", ".join(forbidden))

    print("D9.3 Market Response Loop Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
