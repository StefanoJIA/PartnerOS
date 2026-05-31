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
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "human D8 Go/No-Go handoff",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "Project Execution Chain Record",
    "docs/records/project_execution_chain_20260531.md",
    "D8 Staging Operator Handoff Record",
    "docs/records/d8_staging_operator_handoff_20260531.md",
    "D8 Staging Access Request Record",
    "docs/records/d8_staging_access_request_20260531.md",
    "Port 8014 (D7.6+ validation default)",
    '$env:BACKEND_BASE_URL="http://127.0.0.1:8014"',
    '$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8014"',
    "Current D8/D9 docs",
    "Current PartnerOS Local Status",
    "http://127.0.0.1:8014/health",
    "D8 Staging Execution Pack",
    "D8 Staging Evidence Review",
    "D8 Production Coordination Runbook",
    "D9 Operating Execution Pack",
    "Project Execution Acceptance Audit",
    "Completion Proof Ledger",
    "PROVED_LOCAL",
    "MISSING_EXTERNAL",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "https://<redacted-backend>",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/d8_staging_evidence_review_check.py",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/project_execution_status.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "python scripts/product_vision_check.py",
    "python scripts/desktop_target_architecture_check.py",
    "python scripts/runtime_modes_check.py",
    "python scripts/database_lifecycle_doc_check.py",
    "python scripts/desktop_packaging_docs_check.py",
    "python scripts/web_to_desktop_migration_doc_check.py",
    "python scripts/desktop_transition_roadmap_check.py",
    "python scripts/project_reorientation_summary_check.py",
    "python scripts/dev_guide_check.py",
    "python scripts/integrated_backend_standards_check.py",
    "python scripts/lead_intelligence_docs_check.py",
    "python scripts/manual_a_domain_test_plan_check.py",
    "python scripts/codex_skill_pack_check.py",
    "python scripts/activity_actions_doc_check.py",
    "python scripts/readme_check.py",
    "python scripts/deployment_readiness_checklist_check.py",
    "python scripts/testing_guide_check.py",
    "python scripts/testing_summary_d5_2_check.py",
    "python scripts/operator_guide_check.py",
)
FORBIDDEN_MARKERS = (
    "**D7** is Order / Production / Shipment.",
    "D7.1 design complete",
    "No Phase 2 yet",
    "Current MVP Status（D5.2.2+ detail）",
    "§ Changing backend port",
    "uvicorn :8000",
)
TOKEN_ASSIGNMENT = re.compile(r"SERVICE_PORTAL_PARTNEROS_TOKEN\s*=")
PROOF_RECORD_MARKERS = tuple(marker for marker in REQUIRED_MARKERS if marker.startswith("docs/records/"))


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


def _proof_record_issues() -> list[str]:
    issues: list[str] = []
    for marker in PROOF_RECORD_MARKERS:
        if "YYYYMMDD" in marker:
            continue
        if not (REPO_ROOT / marker).is_file():
            issues.append(marker)
    return issues


def main() -> int:
    checks = [
        Check("README exists"),
        Check("README contains current stage and handoff gates"),
        Check("README proof record links exist"),
        Check("README avoids stale stage claims"),
        Check("README is redacted"),
    ]

    text = _text()
    checks[0].pass_("README.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    proof_records = _proof_record_issues()
    checks[2].pass_("current proof records present") if not proof_records else checks[2].fail(
        ", ".join(proof_records)
    )

    stale = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    checks[3].pass_("no stale D7/D5.2 boundary markers") if not stale else checks[3].fail(", ".join(stale))

    redaction = _token_assignment_issues(text)
    redaction.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[4].pass_("no secret-like markers") if not redaction else checks[4].fail(", ".join(redaction[:8]))

    print("README Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
