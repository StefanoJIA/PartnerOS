"""Validate the current D7.6+/D8 testing guide."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "testing.md"

REQUIRED_MARKERS = (
    "Testing Guide",
    "Preferred local validation port",
    "8014",
    "READY_FOR_STAGING_HANDOFF",
    "d7_7_portal_bridge_check.py",
    "d7_6_shipment_tracking_check.py",
    "d7_5_production_milestone_check.py",
    "smoke_all_d5.py",
    "dev_runtime_doctor.py",
    "readme_check.py",
    "deployment_readiness_checklist_check.py",
    "testing_guide_check.py",
    "operator_guide_check.py",
    "project_execution_chain_check.py",
    "project_execution_status.py",
    "python -m pytest -q",
    "npm run test -- --run",
    "d8_strict_staging_evidence_check.py --evidence-json",
    "d8_staging_evidence_review_check.py",
    "STAGING_VALIDATED",
    "PARTNEROS_TEST_DATABASE_URL",
    "Legacy D5/D6 Checks",
    "not the current D7.6+/D8 validation matrix",
    "Do not send email/webhooks",
    "service.intelli-opus.com",
)
FORBIDDEN_MARKERS = (
    "D5.2.11 Internal MVP Release Pack",
    "D5.2.2 smoke test",
    "8010 示例",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "raw response body:",
    "password_hash",
)
TOKEN_ASSIGNMENT = re.compile(r"SERVICE_PORTAL_PARTNEROS_TOKEN\s*=")


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


def _redaction_issues(text: str) -> list[str]:
    issues: list[str] = []
    for marker in FORBIDDEN_MARKERS[3:]:
        if marker.lower() in text.lower():
            issues.append(marker)
    for line in text.splitlines():
        if TOKEN_ASSIGNMENT.search(line) and "<portal-server-token>" not in line:
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
    issues.extend(redaction_issues(DOC, text, include_common_markers=False))
    return issues


def main() -> int:
    checks = [
        Check("testing guide exists"),
        Check("testing guide contains current D7.6+/D8 validation matrix"),
        Check("testing guide avoids stale primary D5/D6 test matrix"),
        Check("testing guide is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/testing.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:3] if marker in text]
    checks[2].pass_("no stale primary D5/D6 matrix markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = _redaction_issues(text)
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Testing Guide Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
