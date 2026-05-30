"""Validate the D8 strict staging execution pack."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

REQUIRED_FILES = (
    "backend/scripts/d8_readiness_audit.py",
    "backend/scripts/d8_stage_goal_matrix_check.py",
    "backend/scripts/d8_integration_hardening_check.py",
    "backend/scripts/d8_strict_staging_evidence_check.py",
    "backend/scripts/d8_staging_operator_handoff.py",
    "backend/scripts/d8_staging_handoff_bundle_check.py",
    "backend/scripts/d8_staging_access_request_check.py",
    "backend/scripts/d8_staging_gap_triage_check.py",
    "backend/scripts/d8_staging_records_check.py",
    "backend/scripts/d8_production_coordination_check.py",
    "backend/scripts/d9_post_launch_plan_check.py",
    "backend/scripts/d9_operating_records_check.py",
    "backend/scripts/phase3_roadmap_check.py",
    "backend/scripts/ie_auto_project_plan_check.py",
    "backend/scripts/project_execution_chain_check.py",
    "backend/scripts/project_execution_status.py",
    "backend/scripts/project_execution_acceptance_audit_check.py",
    "backend/scripts/project_execution_records_check.py",
    "docs/phase3/d8_readiness_audit.md",
    "docs/phase3/d8_delivery_stage_goal_matrix.md",
    "docs/phase3/d8_strict_staging_cloud_validation.md",
    "docs/phase3/d8_staging_operator_handoff.md",
    "docs/phase3/d8_staging_handoff_bundle.md",
    "docs/phase3/d8_staging_access_request.md",
    "docs/phase3/d8_staging_gap_triage.md",
    "docs/phase3/d8_staging_records_policy.md",
    "docs/phase3/d8_production_coordination_plan.md",
    "docs/phase3/d9_post_launch_operating_loop.md",
    "docs/phase3/d9_operating_records_policy.md",
    "docs/phase3/project_execution_chain_gate.md",
    "docs/phase3/project_execution_acceptance_audit.md",
    "docs/phase3/phase3_roadmap.md",
    "docs/phase3/ie_auto_project_plan.md",
)
HANDOFF_MARKERS = (
    "BACKEND_BASE_URL",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "SERVICE_PORTAL_ORIGIN",
    "python scripts/d8_readiness_audit.py",
    "python scripts/d8_stage_goal_matrix_check.py",
    "python scripts/d8_integration_hardening_check.py",
    "python scripts/d8_staging_handoff_bundle_check.py",
    "python scripts/d8_staging_access_request_check.py",
    "python scripts/d8_staging_gap_triage_check.py",
    "python scripts/d8_staging_records_check.py",
    "python scripts/d8_production_coordination_check.py",
    "python scripts/d9_post_launch_plan_check.py",
    "python scripts/d9_operating_records_check.py",
    "python scripts/phase3_roadmap_check.py",
    "python scripts/ie_auto_project_plan_check.py",
    "python scripts/project_execution_chain_check.py",
    "python scripts/project_execution_status.py",
    "python scripts/project_execution_acceptance_audit_check.py",
    "python scripts/project_execution_records_check.py",
    "--evidence-json",
    "--gap-markdown",
    "Do not deploy or modify `service.intelli-opus.com`",
    "Do not print, screenshot, commit, or paste portal tokens",
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


def _missing_files() -> list[str]:
    return [path for path in REQUIRED_FILES if not (REPO_ROOT / path).exists()]


def _run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script, *args],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _generate_handoff() -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory(prefix="d8_handoff_") as tmp:
        output = Path(tmp) / "handoff.md"
        result = _run_script("scripts/d8_staging_operator_handoff.py", "--output", str(output))
        text = output.read_text(encoding="utf-8") if output.exists() else ""
        combined_output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        return result.returncode, text, combined_output


def main() -> int:
    checks = [
        Check("execution pack files present"),
        Check("readiness audit runs"),
        Check("stage goal matrix check runs"),
        Check("staging handoff bundle check runs"),
        Check("staging access request check runs"),
        Check("staging gap triage check runs"),
        Check("staging records check runs"),
        Check("production coordination check runs"),
        Check("D9 post-launch plan check runs"),
        Check("D9 operating records check runs"),
        Check("Phase 3 roadmap check runs"),
        Check("IE Auto project plan check runs"),
        Check("project execution chain check runs"),
        Check("project execution status summary runs"),
        Check("project execution acceptance audit runs"),
        Check("project execution records check runs"),
        Check("handoff generator runs"),
        Check("handoff contains required commands and safety markers"),
    ]

    missing = _missing_files()
    checks[0].pass_(f"{len(REQUIRED_FILES)} files") if not missing else checks[0].fail(", ".join(missing))

    readiness = _run_script("scripts/d8_readiness_audit.py")
    if readiness.returncode == 0 and "Overall:" in readiness.stdout:
        checks[1].pass_(next((line for line in readiness.stdout.splitlines() if line.startswith("Overall:")), "ok"))
    else:
        checks[1].fail((readiness.stdout + readiness.stderr)[:160])

    matrix = _run_script("scripts/d8_stage_goal_matrix_check.py")
    if matrix.returncode == 0 and "Result: PASS" in matrix.stdout:
        checks[2].pass_("PASS")
    else:
        checks[2].fail((matrix.stdout + matrix.stderr)[:160])

    handoff_bundle = _run_script("scripts/d8_staging_handoff_bundle_check.py")
    if handoff_bundle.returncode == 0 and "Result: PASS" in handoff_bundle.stdout:
        checks[3].pass_("PASS")
    else:
        checks[3].fail((handoff_bundle.stdout + handoff_bundle.stderr)[:160])

    access_request = _run_script("scripts/d8_staging_access_request_check.py")
    if access_request.returncode == 0 and "Result: PASS" in access_request.stdout:
        checks[4].pass_("PASS")
    else:
        checks[4].fail((access_request.stdout + access_request.stderr)[:160])

    gap_triage = _run_script("scripts/d8_staging_gap_triage_check.py")
    if gap_triage.returncode == 0 and "Result: PASS" in gap_triage.stdout:
        checks[5].pass_("PASS")
    else:
        checks[5].fail((gap_triage.stdout + gap_triage.stderr)[:160])

    records = _run_script("scripts/d8_staging_records_check.py")
    if records.returncode == 0 and "Result: PASS" in records.stdout:
        checks[6].pass_("PASS")
    else:
        checks[6].fail((records.stdout + records.stderr)[:160])

    production = _run_script("scripts/d8_production_coordination_check.py")
    if production.returncode == 0 and "Result: PASS" in production.stdout:
        checks[7].pass_("PASS")
    else:
        checks[7].fail((production.stdout + production.stderr)[:160])

    d9 = _run_script("scripts/d9_post_launch_plan_check.py")
    if d9.returncode == 0 and "Result: PASS" in d9.stdout:
        checks[8].pass_("PASS")
    else:
        checks[8].fail((d9.stdout + d9.stderr)[:160])

    d9_records = _run_script("scripts/d9_operating_records_check.py")
    if d9_records.returncode == 0 and "Result: PASS" in d9_records.stdout:
        checks[9].pass_("PASS")
    else:
        checks[9].fail((d9_records.stdout + d9_records.stderr)[:160])

    roadmap = _run_script("scripts/phase3_roadmap_check.py")
    if roadmap.returncode == 0 and "Result: PASS" in roadmap.stdout:
        checks[10].pass_("PASS")
    else:
        checks[10].fail((roadmap.stdout + roadmap.stderr)[:160])

    project_plan = _run_script("scripts/ie_auto_project_plan_check.py")
    if project_plan.returncode == 0 and "Result: PASS" in project_plan.stdout:
        checks[11].pass_("PASS")
    else:
        checks[11].fail((project_plan.stdout + project_plan.stderr)[:160])

    execution_chain = _run_script("scripts/project_execution_chain_check.py")
    if execution_chain.returncode == 0 and "Result: PASS" in execution_chain.stdout:
        checks[12].pass_("PASS")
    else:
        checks[12].fail((execution_chain.stdout + execution_chain.stderr)[:160])

    execution_status = _run_script("scripts/project_execution_status.py")
    if execution_status.returncode == 0 and "Result: PASS" in execution_status.stdout:
        checks[13].pass_("PASS")
    else:
        checks[13].fail((execution_status.stdout + execution_status.stderr)[:160])

    acceptance_audit = _run_script("scripts/project_execution_acceptance_audit_check.py")
    if acceptance_audit.returncode == 0 and "Result: PASS" in acceptance_audit.stdout:
        checks[14].pass_("PASS")
    else:
        checks[14].fail((acceptance_audit.stdout + acceptance_audit.stderr)[:160])

    execution_records = _run_script("scripts/project_execution_records_check.py")
    if execution_records.returncode == 0 and "Result: PASS" in execution_records.stdout:
        checks[15].pass_("PASS")
    else:
        checks[15].fail((execution_records.stdout + execution_records.stderr)[:160])

    handoff_code, handoff_text, handoff_output = _generate_handoff()
    if handoff_code == 0 and handoff_text:
        checks[16].pass_("generated")
    else:
        checks[16].fail(handoff_output[:160])

    missing_markers = [marker for marker in HANDOFF_MARKERS if marker not in handoff_text]
    if not missing_markers:
        checks[17].pass_("commands and safety boundaries")
    else:
        checks[17].fail(", ".join(missing_markers))

    print("D8 Staging Execution Pack Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
