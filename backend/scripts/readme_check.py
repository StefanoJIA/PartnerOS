"""Validate README current-stage and D8/D9 handoff guidance."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "README.md"

REQUIRED_MARKERS = (
    "D7",
    "closed through D7.9",
    "D8",
    "READY_FOR_STAGING_HANDOFF",
    "D9",
    "staging evidence review and production coordination",
    "Current D8/D9 docs",
    "D8 Staging Execution Pack",
    "D8 Staging Evidence Review",
    "D8 Production Coordination Runbook",
    "D9 Operating Execution Pack",
    "Project Execution Acceptance Audit",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/d8_staging_evidence_review_check.py",
    "python scripts/project_execution_status.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "python scripts/readme_check.py",
    "python scripts/operator_guide_check.py",
)
FORBIDDEN_MARKERS = (
    "**D7** is Order / Production / Shipment.",
    "D7.1 design complete",
    "No Phase 2 yet",
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


def _token_assignment_issues(text: str) -> list[str]:
    issues: list[str] = []
    for line in text.splitlines():
        if TOKEN_ASSIGNMENT.search(line) and "<portal-server-token>" not in line:
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
    return issues


def main() -> int:
    checks = [
        Check("README exists"),
        Check("README contains current stage and handoff gates"),
        Check("README avoids stale stage claims"),
        Check("README is redacted"),
    ]

    text = _text()
    checks[0].pass_("README.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    checks[2].pass_("no stale D7/D5.2 boundary markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = _token_assignment_issues(text)
    redaction.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("README Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
