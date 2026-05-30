"""Validate the D8 staging operator response intake runbook."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d8_staging_operator_response_intake.md"

REQUIRED_MARKERS = (
    "D8 Staging Operator Response Intake",
    "READY_FOR_STAGING",
    "WAITING_FOR_OPERATOR_RESPONSE",
    "READY_FOR_STRICT_EVIDENCE_RUN",
    "READY_FOR_EVIDENCE_REVIEW",
    "BACKEND_BASE_URL",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "SERVICE_PORTAL_ORIGIN",
    "DEPLOYED_COMMIT",
    "TEST_DATA_SCOPE",
    "provided privately",
    "d8_strict_staging_evidence_YYYYMMDD.json",
    "d8_strict_staging_gaps_YYYYMMDD.md",
    "python scripts/d8_staging_operator_response_intake_check.py",
    "python scripts/d8_staging_input_preflight_check.py",
    "python scripts/d8_staging_records_check.py",
    "python scripts/d8_staging_evidence_review_check.py",
    "python scripts/d8_readiness_audit.py",
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


def _forbidden(text: str) -> list[str]:
    issues = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    for line in text.splitlines():
        if "SERVICE_PORTAL_PARTNEROS_TOKEN" in line and "=" in line and "<portal-server-token>" not in line:
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
    return issues


def main() -> int:
    checks = [
        Check("operator response intake doc exists"),
        Check("operator response intake is actionable"),
        Check("operator response intake is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/d8_staging_operator_response_intake.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = _forbidden(text)
    checks[2].pass_("no secret-like markers") if not forbidden else checks[2].fail(", ".join(forbidden))

    print("D8 Staging Operator Response Intake Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
