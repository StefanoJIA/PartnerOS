"""Validate the D9 operating loop kickoff checklist."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d9_operating_loop_kickoff.md"

REQUIRED_MARKERS = (
    "D9 Operating Loop Kickoff",
    "D8 production coordination",
    "STAGING_VALIDATED",
    "READY_FOR_PRODUCTION_COORDINATION",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "D9.1 Operating Health Review",
    "d9_1_operating_health_review.md",
    "python scripts/d9_1_operating_health_review_check.py",
    "D9.2 Order Operations Loop",
    "d9_2_order_operations_loop.md",
    "python scripts/d9_2_order_operations_loop_check.py",
    "D9.3 Market Response Loop",
    "d9_3_market_response_loop.md",
    "python scripts/d9_3_market_response_loop_check.py",
    "D9.4 Improvement Backlog",
    "d9_4_improvement_backlog.md",
    "python scripts/d9_4_improvement_backlog_check.py",
    "python scripts/d9_operating_loop_kickoff_check.py",
    "python scripts/d9_post_launch_plan_check.py",
    "python scripts/d9_operating_records_check.py",
    "docs/records/d9_operating_review_YYYYMMDD.md",
    "Owner:",
    "Next action:",
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
        Check("D9 kickoff doc exists"),
        Check("D9 kickoff is actionable"),
        Check("D9 kickoff is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/d9_operating_loop_kickoff.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    forbidden.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[2].pass_("no secret-like markers") if not forbidden else checks[2].fail(", ".join(forbidden))

    print("D9 Operating Loop Kickoff Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
