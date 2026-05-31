"""Validate the current D8/D9 deployment readiness checklist."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "deployment_readiness_checklist.md"

REQUIRED_MARKERS = (
    "READY_FOR_STAGING_HANDOFF",
    "READY_FOR_STAGING",
    "STAGING_VALIDATED",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "WAITING_FOR_STAGING_VALIDATION",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "D9 operating-loop work remains gated",
    "human Go / No-Go handoff",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "BACKEND_BASE_URL",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "SERVICE_PORTAL_ORIGIN",
    "python scripts/readme_check.py",
    "python scripts/deployment_readiness_checklist_check.py",
    "python scripts/operator_guide_check.py",
    "python scripts/project_execution_status.py",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/project_execution_chain_check.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/d8_staging_input_preflight_check.py",
    "python scripts/d8_strict_staging_evidence_check.py --evidence-json",
    "python scripts/d8_staging_records_check.py",
    "python scripts/d8_staging_evidence_review_check.py",
    "python scripts/d8_readiness_audit.py",
    "python scripts/d8_production_coordination_check.py",
    "python scripts/d8_production_coordination_runbook_check.py",
    "python scripts/d9_operating_execution_pack_check.py",
    "LOCAL_REHEARSAL_READY",
    "service.intelli-opus.com",
    "No carrier API, webhook, email",
)
FORBIDDEN_MARKERS = (
    "D5.2 Internal MVP",
    "No Phase 2 yet",
    "Do not start Phase 2",
    "portal_consumer_check.py",
    "portal_readiness_check.py",
    "smoke_demo_ready.py",
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


def _redaction_issues(text: str) -> list[str]:
    issues: list[str] = []
    for marker in FORBIDDEN_MARKERS:
        if marker.lower() in text.lower():
            issues.append(marker)
    for line in text.splitlines():
        if TOKEN_ASSIGNMENT.search(line) and "<portal-server-token>" not in line:
            issues.append("SERVICE_PORTAL_PARTNEROS_TOKEN=<non-placeholder>")
    issues.extend(redaction_issues(DOC, text, include_common_markers=False))
    return issues


def main() -> int:
    checks = [
        Check("deployment readiness checklist exists"),
        Check("deployment readiness checklist matches D8/D9 stage gates"),
        Check("deployment readiness checklist avoids stale D5/D6 deploy gates"),
        Check("deployment readiness checklist is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/deployment_readiness_checklist.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:6] if marker in text]
    checks[2].pass_("no stale D5/D6 deployment checklist markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = _redaction_issues(text)
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Deployment Readiness Checklist Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
