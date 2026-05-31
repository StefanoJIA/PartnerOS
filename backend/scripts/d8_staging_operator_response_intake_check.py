"""Validate the D8 staging operator response intake runbook."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d8_staging_operator_response_intake.md"

REQUIRED_MARKERS = (
    "D8 Staging Operator Response Intake",
    "READY_FOR_STAGING",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "until strict staging evidence from real staging values replaces it",
    "WAITING_FOR_OPERATOR_RESPONSE",
    "READY_FOR_STRICT_EVIDENCE_RUN",
    "READY_FOR_EVIDENCE_REVIEW",
    "BACKEND_BASE_URL",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "SERVICE_PORTAL_ORIGIN",
    "DEPLOYED_COMMIT",
    "TEST_DATA_SCOPE",
    "EVIDENCE_ARTIFACTS",
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
    "must not be used as `STAGING_VALIDATED` or `STAGING_GAPS_OPEN` evidence",
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
TOKEN_STATUS = re.compile(r"^\s*SERVICE_PORTAL_PARTNEROS_TOKEN\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)
BACKEND_URL_STATUS = re.compile(r"^\s*BACKEND_BASE_URL\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)
EVIDENCE_ARTIFACTS_STATUS = re.compile(r"^\s*EVIDENCE_ARTIFACTS\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)


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
    issues.extend(redaction_issues(DOC, text, include_common_markers=False))
    for line in text.splitlines():
        backend_url = BACKEND_URL_STATUS.match(line)
        if backend_url and backend_url.group("value").strip() != "provided privately":
            issues.append("BACKEND_BASE_URL:<non-private-status>")
        status = TOKEN_STATUS.match(line)
        if status and status.group("value").strip() != "provided privately":
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN:<non-private-status>")
        artifacts = EVIDENCE_ARTIFACTS_STATUS.match(line)
        if artifacts:
            value = artifacts.group("value")
            if (
                "d8_strict_staging_evidence_YYYYMMDD.json" not in value
                or "d8_strict_staging_gaps_YYYYMMDD.md" not in value
            ):
                issues.append("EVIDENCE_ARTIFACTS:<noncanonical-name>")
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
