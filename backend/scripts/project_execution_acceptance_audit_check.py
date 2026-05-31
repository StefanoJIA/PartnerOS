"""Validate the project execution acceptance audit."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DOC = REPO_ROOT / "docs" / "phase3" / "project_execution_acceptance_audit.md"
STATUS_SCRIPT = BACKEND_ROOT / "scripts" / "project_execution_status.py"

REQUIRED_MARKERS = (
    "READY_FOR_STAGING_HANDOFF",
    "READY_FOR_STAGING",
    "WAITING_FOR_STAGING_VALIDATION",
    "STAGING_VALIDATED",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "human Go / No-Go handoff",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "d8_staging_evidence_review_check.py",
    "Agent Guide",
    "agent_guide_check.py",
    "README",
    "readme_check.py",
    "Product Vision",
    "product_vision_check.py",
    "Desktop Target Architecture",
    "desktop_target_architecture_check.py",
    "Runtime Modes",
    "runtime_modes_check.py",
    "Database Lifecycle",
    "database_lifecycle_doc_check.py",
    "Desktop Packaging Docs",
    "desktop_packaging_docs_check.py",
    "Web-to-Desktop Migration",
    "web_to_desktop_migration_doc_check.py",
    "Desktop Transition Roadmap",
    "desktop_transition_roadmap_check.py",
    "Project Reorientation Summary",
    "project_reorientation_summary_check.py",
    "Developer Guide",
    "dev_guide_check.py",
    "Integrated Backend Standards",
    "integrated_backend_standards_check.py",
    "Lead Intelligence Docs",
    "lead_intelligence_docs_check.py",
    "Manual A-Domain Test Plan",
    "manual_a_domain_test_plan_check.py",
    "Codex Skill Pack",
    "codex_skill_pack_check.py",
    "Activity Actions",
    "activity_actions_doc_check.py",
    "Deployment Readiness Checklist",
    "deployment_readiness_checklist_check.py",
    "Testing Guide",
    "testing_guide_check.py",
    "D5.2 Testing Summary",
    "testing_summary_d5_2_check.py",
    "IE Auto Project Plan",
    "Phase 3 Roadmap",
    "D8 Delivery Stage Goal Matrix",
    "Operator Guide",
    "operator_guide_check.py",
    "D8 Local Staging Rehearsal",
    "D8 Staging Handoff Bundle",
    "D8 Staging Operator Runbook",
    "D8 Staging Input Preflight",
    "D8 Staging Access Request",
    "D8 Staging Operator Response Intake",
    "D8 Staging Gap Triage",
    "D8 Staging Evidence Review",
    "D8 Production Coordination Plan",
    "D8 Production Coordination Runbook",
    "D9 Post-Launch Operating Loop",
    "D9 Operating Loop Kickoff",
    "D9 Operating Execution Pack",
    "D9.1 Operating Health Review",
    "D9.2 Order Operations Loop",
    "D9.3 Market Response Loop",
    "D9.4 Improvement Backlog",
    "Project Execution Chain Gate",
    "project_execution_status.py",
    "project_execution_acceptance_audit_check.py",
    "d8_staging_handoff_bundle.md",
    "d8_staging_operator_runbook.md",
    "d8_staging_access_request.md",
    "WAITING_FOR_PRIVATE_VALUES",
    "real `BACKEND_BASE_URL`",
    "real `SERVICE_PORTAL_PARTNEROS_TOKEN`",
    "d8_strict_staging_evidence_YYYYMMDD.json",
    "No `.env`",
    "No email, webhook, carrier API",
)
FORBIDDEN_MARKERS = (
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
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


def _run_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _extract(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return "UNKNOWN"


def _status_next_action(chain_state: str, readiness_state: str, coordination_state: str) -> tuple[str, str]:
    spec = importlib.util.spec_from_file_location("project_execution_status_for_acceptance", STATUS_SCRIPT)
    if not spec or not spec.loader:
        return "UNKNOWN", "project_execution_status.py could not be loaded"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._next_action(chain_state, readiness_state, coordination_state)


def main() -> int:
    checks = [
        Check("acceptance audit doc exists"),
        Check("acceptance audit maps requirements to evidence"),
        Check("acceptance audit is redacted"),
        Check("D8 readiness remains pre-staging"),
        Check("production coordination remains gated"),
        Check("current next action points to staging handoff runbook"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/project_execution_acceptance_audit.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in text.lower()]
    checks[2].pass_("no secret-like markers") if not forbidden else checks[2].fail(", ".join(forbidden))

    readiness = _run_script("scripts/d8_readiness_audit.py")
    readiness_output = "\n".join(part for part in (readiness.stdout.strip(), readiness.stderr.strip()) if part)
    readiness_state = _extract(readiness_output, "Overall:")
    if readiness.returncode == 0 and readiness_state == "READY_FOR_STAGING":
        checks[3].pass_(readiness_state)
    else:
        checks[3].fail(readiness_state)

    production = _run_script("scripts/d8_production_coordination_check.py")
    production_output = "\n".join(part for part in (production.stdout.strip(), production.stderr.strip()) if part)
    coordination_state = _extract(production_output, "Coordination State:")
    if production.returncode == 0 and coordination_state == "WAITING_FOR_STAGING_VALIDATION":
        checks[4].pass_(coordination_state)
    else:
        checks[4].fail(coordination_state)

    current_stage, next_action = _status_next_action(
        "READY_FOR_STAGING_HANDOFF",
        readiness_state,
        coordination_state,
    )
    status_output = f"Current Stage: {current_stage}\nNext Action: {next_action}"
    next_action_markers = (
        "Current Stage: READY_FOR_STAGING_HANDOFF",
        "d8_staging_handoff_bundle.md",
        "d8_staging_operator_runbook.md",
        "d8_staging_access_request.md",
    )
    missing_next_action = [marker for marker in next_action_markers if marker not in status_output]
    if not missing_next_action:
        checks[5].pass_("staging handoff runbook path")
    else:
        checks[5].fail(", ".join(missing_next_action))

    print("Project Execution Acceptance Audit Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
