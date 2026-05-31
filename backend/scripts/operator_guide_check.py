"""Validate the operator guide's current D8/D9 handoff guidance."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "operator_guide.md"

REQUIRED_MARKERS = (
    "D8 Integration Hardening",
    "d8_staging_handoff_bundle.md",
    "READY_FOR_STAGING_HANDOFF",
    "port 8014 (D7.6+ validation default)",
    '$env:BACKEND_BASE_URL="http://127.0.0.1:8014"',
    '$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"',
    "d8_staging_operator_runbook.md",
    "d8_staging_input_preflight_check.py",
    "d8_staging_access_request_check.py",
    "d8_staging_operator_response_intake_check.py",
    "d8_staging_records_check.py",
    "d8_staging_evidence_review_check.py",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "d8_production_coordination_check.py",
    "d8_production_coordination_runbook_check.py",
    "D9 starts only after `STAGING_VALIDATED`, `READY_FOR_PRODUCTION_COORDINATION_REVIEW`, and production coordination",
    "d9_operating_execution_pack_check.py",
    "d9_operating_loop_kickoff_check.py",
    "d9_operating_records_check.py",
    "project_execution_status.py",
    "project_execution_acceptance_audit_check.py",
    "desktop_transition_roadmap_check.py",
    "deployment_readiness_checklist_check.py",
    "testing_guide_check.py",
    "operator_guide_check.py",
    "carrier APIs",
    "service.intelli-opus.com",
)
FORBIDDEN_MARKERS = (
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "raw response body:",
    "password_hash",
    "database_url",
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


def main() -> int:
    checks = [
        Check("operator guide exists"),
        Check("operator guide contains current D8/D9 handoff gates"),
        Check("operator guide is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/operator_guide.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    for line in text.splitlines():
        if TOKEN_ASSIGNMENT.search(line) and "<portal-server-token>" not in line:
            forbidden.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
    forbidden.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[2].pass_("no secret-like markers") if not forbidden else checks[2].fail(", ".join(forbidden[:8]))

    print("Operator Guide Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
