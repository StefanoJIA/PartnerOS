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
    "backend/scripts/d8_local_staging_rehearsal_check.py",
    "backend/scripts/d8_staging_operator_handoff.py",
    "backend/scripts/d8_staging_handoff_bundle_check.py",
    "backend/scripts/d8_staging_operator_runbook_check.py",
    "backend/scripts/d8_staging_input_preflight_check.py",
    "backend/scripts/d8_staging_access_request_check.py",
    "backend/scripts/d8_staging_operator_response_intake_check.py",
    "backend/scripts/d8_staging_gap_triage_check.py",
    "backend/scripts/d8_staging_records_check.py",
    "backend/scripts/d8_staging_evidence_review_check.py",
    "backend/scripts/d8_production_coordination_check.py",
    "backend/scripts/d8_production_coordination_runbook_check.py",
    "backend/scripts/d9_post_launch_plan_check.py",
    "backend/scripts/d9_operating_execution_pack_check.py",
    "backend/scripts/d9_operating_loop_kickoff_check.py",
    "backend/scripts/d9_1_operating_health_review_check.py",
    "backend/scripts/d9_2_order_operations_loop_check.py",
    "backend/scripts/d9_3_market_response_loop_check.py",
    "backend/scripts/d9_4_improvement_backlog_check.py",
    "backend/scripts/d9_operating_records_check.py",
    "backend/scripts/phase3_roadmap_check.py",
    "backend/scripts/ie_auto_project_plan_check.py",
    "backend/scripts/project_execution_chain_check.py",
    "backend/scripts/project_execution_status.py",
    "backend/scripts/project_execution_acceptance_audit_check.py",
    "backend/scripts/project_execution_records_check.py",
    "backend/scripts/agent_guide_check.py",
    "backend/scripts/readme_check.py",
    "backend/scripts/desktop_transition_roadmap_check.py",
    "backend/scripts/project_reorientation_summary_check.py",
    "backend/scripts/dev_guide_check.py",
    "backend/scripts/deployment_readiness_checklist_check.py",
    "backend/scripts/testing_guide_check.py",
    "backend/scripts/operator_guide_check.py",
    "README.md",
    "AGENTS.md",
    "docs/roadmap_desktop_transition.md",
    "docs/project_reorientation_summary.md",
    "docs/dev_guide.md",
    "docs/deployment_readiness_checklist.md",
    "docs/testing.md",
    "docs/operator_guide.md",
    "docs/phase3/d8_readiness_audit.md",
    "docs/phase3/d8_delivery_stage_goal_matrix.md",
    "docs/phase3/d8_strict_staging_cloud_validation.md",
    "docs/phase3/d8_local_staging_rehearsal.md",
    "docs/phase3/d8_staging_operator_handoff.md",
    "docs/phase3/d8_staging_handoff_bundle.md",
    "docs/phase3/d8_staging_operator_runbook.md",
    "docs/phase3/d8_staging_input_preflight.md",
    "docs/phase3/d8_staging_access_request.md",
    "docs/phase3/d8_staging_operator_response_intake.md",
    "docs/phase3/d8_staging_gap_triage.md",
    "docs/phase3/d8_staging_records_policy.md",
    "docs/phase3/d8_staging_evidence_review.md",
    "docs/phase3/d8_production_coordination_plan.md",
    "docs/phase3/d8_production_coordination_runbook.md",
    "docs/phase3/d9_post_launch_operating_loop.md",
    "docs/phase3/d9_operating_execution_pack.md",
    "docs/phase3/d9_operating_loop_kickoff.md",
    "docs/phase3/d9_1_operating_health_review.md",
    "docs/phase3/d9_2_order_operations_loop.md",
    "docs/phase3/d9_3_market_response_loop.md",
    "docs/phase3/d9_4_improvement_backlog.md",
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
    "docs/phase3/d8_staging_handoff_bundle.md",
    "docs/phase3/d8_staging_operator_runbook.md",
    "docs/phase3/d8_production_coordination_runbook.md",
    "python scripts/d8_readiness_audit.py",
    "python scripts/d8_stage_goal_matrix_check.py",
    "python scripts/d8_integration_hardening_check.py",
    "python scripts/d8_local_staging_rehearsal_check.py",
    "python scripts/d8_staging_handoff_bundle_check.py",
    "python scripts/d8_staging_operator_runbook_check.py",
    "python scripts/d8_staging_input_preflight_check.py",
    "python scripts/d8_staging_access_request_check.py",
    "python scripts/d8_staging_operator_response_intake_check.py",
    "python scripts/d8_staging_gap_triage_check.py",
    "python scripts/d8_staging_records_check.py",
    "python scripts/d8_staging_evidence_review_check.py",
    "python scripts/d8_production_coordination_check.py",
    "python scripts/d8_production_coordination_runbook_check.py",
    "python scripts/d9_post_launch_plan_check.py",
    "python scripts/d9_operating_execution_pack_check.py",
    "python scripts/d9_operating_loop_kickoff_check.py",
    "python scripts/d9_1_operating_health_review_check.py",
    "python scripts/d9_2_order_operations_loop_check.py",
    "python scripts/d9_3_market_response_loop_check.py",
    "python scripts/d9_4_improvement_backlog_check.py",
    "python scripts/d9_operating_records_check.py",
    "python scripts/phase3_roadmap_check.py",
    "python scripts/ie_auto_project_plan_check.py",
    "python scripts/agent_guide_check.py",
    "python scripts/readme_check.py",
    "python scripts/desktop_transition_roadmap_check.py",
    "python scripts/project_reorientation_summary_check.py",
    "python scripts/dev_guide_check.py",
    "python scripts/deployment_readiness_checklist_check.py",
    "python scripts/testing_guide_check.py",
    "python scripts/operator_guide_check.py",
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
        output = Path(tmp) / "d8_staging_operator_handoff_20990101.md"
        result = _run_script("scripts/d8_staging_operator_handoff.py", "--output", str(output))
        text = output.read_text(encoding="utf-8") if output.exists() else ""
        combined_output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        return result.returncode, text, combined_output


def main() -> int:
    checks = [
        Check("execution pack files present"),
        Check("readiness audit runs"),
        Check("stage goal matrix check runs"),
        Check("local staging rehearsal check runs"),
        Check("staging handoff bundle check runs"),
        Check("staging operator runbook check runs"),
        Check("staging input preflight check runs"),
        Check("staging access request check runs"),
        Check("staging operator response intake check runs"),
        Check("staging gap triage check runs"),
        Check("staging records check runs"),
        Check("staging evidence review check runs"),
        Check("production coordination check runs"),
        Check("production coordination runbook check runs"),
        Check("D9 post-launch plan check runs"),
        Check("D9 operating execution pack check runs"),
        Check("D9 operating loop kickoff check runs"),
        Check("D9.1 operating health review check runs"),
        Check("D9.2 order operations loop check runs"),
        Check("D9.3 market response loop check runs"),
        Check("D9.4 improvement backlog check runs"),
        Check("D9 operating records check runs"),
        Check("Phase 3 roadmap check runs"),
        Check("IE Auto project plan check runs"),
        Check("project execution chain check runs"),
        Check("project execution status summary runs"),
        Check("project execution acceptance audit runs"),
        Check("project execution records check runs"),
        Check("agent guide check runs"),
        Check("README check runs"),
        Check("desktop transition roadmap check runs"),
        Check("project reorientation summary check runs"),
        Check("developer guide check runs"),
        Check("deployment readiness checklist check runs"),
        Check("testing guide check runs"),
        Check("operator guide check runs"),
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

    local_rehearsal = _run_script("scripts/d8_local_staging_rehearsal_check.py")
    if local_rehearsal.returncode == 0 and "Result: PASS" in local_rehearsal.stdout:
        checks[3].pass_("PASS")
    else:
        checks[3].fail((local_rehearsal.stdout + local_rehearsal.stderr)[:160])

    handoff_bundle = _run_script("scripts/d8_staging_handoff_bundle_check.py")
    if handoff_bundle.returncode == 0 and "Result: PASS" in handoff_bundle.stdout:
        checks[4].pass_("PASS")
    else:
        checks[4].fail((handoff_bundle.stdout + handoff_bundle.stderr)[:160])

    operator_runbook = _run_script("scripts/d8_staging_operator_runbook_check.py")
    if operator_runbook.returncode == 0 and "Result: PASS" in operator_runbook.stdout:
        checks[5].pass_("PASS")
    else:
        checks[5].fail((operator_runbook.stdout + operator_runbook.stderr)[:160])

    input_preflight = _run_script("scripts/d8_staging_input_preflight_check.py")
    if input_preflight.returncode == 0 and "Result: PASS" in input_preflight.stdout:
        checks[6].pass_("PASS")
    else:
        checks[6].fail((input_preflight.stdout + input_preflight.stderr)[:160])

    access_request = _run_script("scripts/d8_staging_access_request_check.py")
    if access_request.returncode == 0 and "Result: PASS" in access_request.stdout:
        checks[7].pass_("PASS")
    else:
        checks[7].fail((access_request.stdout + access_request.stderr)[:160])

    operator_response_intake = _run_script("scripts/d8_staging_operator_response_intake_check.py")
    if operator_response_intake.returncode == 0 and "Result: PASS" in operator_response_intake.stdout:
        checks[8].pass_("PASS")
    else:
        checks[8].fail((operator_response_intake.stdout + operator_response_intake.stderr)[:160])

    gap_triage = _run_script("scripts/d8_staging_gap_triage_check.py")
    if gap_triage.returncode == 0 and "Result: PASS" in gap_triage.stdout:
        checks[9].pass_("PASS")
    else:
        checks[9].fail((gap_triage.stdout + gap_triage.stderr)[:160])

    records = _run_script("scripts/d8_staging_records_check.py")
    if records.returncode == 0 and "Result: PASS" in records.stdout:
        checks[10].pass_("PASS")
    else:
        checks[10].fail((records.stdout + records.stderr)[:160])

    evidence_review = _run_script("scripts/d8_staging_evidence_review_check.py")
    if evidence_review.returncode == 0 and "Result: PASS" in evidence_review.stdout:
        checks[11].pass_("PASS")
    else:
        checks[11].fail((evidence_review.stdout + evidence_review.stderr)[:160])

    production = _run_script("scripts/d8_production_coordination_check.py")
    if production.returncode == 0 and "Result: PASS" in production.stdout:
        checks[12].pass_("PASS")
    else:
        checks[12].fail((production.stdout + production.stderr)[:160])

    production_runbook = _run_script("scripts/d8_production_coordination_runbook_check.py")
    if production_runbook.returncode == 0 and "Result: PASS" in production_runbook.stdout:
        checks[13].pass_("PASS")
    else:
        checks[13].fail((production_runbook.stdout + production_runbook.stderr)[:160])

    d9 = _run_script("scripts/d9_post_launch_plan_check.py")
    if d9.returncode == 0 and "Result: PASS" in d9.stdout:
        checks[14].pass_("PASS")
    else:
        checks[14].fail((d9.stdout + d9.stderr)[:160])

    d9_pack = _run_script("scripts/d9_operating_execution_pack_check.py")
    if d9_pack.returncode == 0 and "Result: PASS" in d9_pack.stdout:
        checks[15].pass_("PASS")
    else:
        checks[15].fail((d9_pack.stdout + d9_pack.stderr)[:160])

    d9_kickoff = _run_script("scripts/d9_operating_loop_kickoff_check.py")
    if d9_kickoff.returncode == 0 and "Result: PASS" in d9_kickoff.stdout:
        checks[16].pass_("PASS")
    else:
        checks[16].fail((d9_kickoff.stdout + d9_kickoff.stderr)[:160])

    d9_health = _run_script("scripts/d9_1_operating_health_review_check.py")
    if d9_health.returncode == 0 and "Result: PASS" in d9_health.stdout:
        checks[17].pass_("PASS")
    else:
        checks[17].fail((d9_health.stdout + d9_health.stderr)[:160])

    d9_orders = _run_script("scripts/d9_2_order_operations_loop_check.py")
    if d9_orders.returncode == 0 and "Result: PASS" in d9_orders.stdout:
        checks[18].pass_("PASS")
    else:
        checks[18].fail((d9_orders.stdout + d9_orders.stderr)[:160])

    d9_market = _run_script("scripts/d9_3_market_response_loop_check.py")
    if d9_market.returncode == 0 and "Result: PASS" in d9_market.stdout:
        checks[19].pass_("PASS")
    else:
        checks[19].fail((d9_market.stdout + d9_market.stderr)[:160])

    d9_backlog = _run_script("scripts/d9_4_improvement_backlog_check.py")
    if d9_backlog.returncode == 0 and "Result: PASS" in d9_backlog.stdout:
        checks[20].pass_("PASS")
    else:
        checks[20].fail((d9_backlog.stdout + d9_backlog.stderr)[:160])

    d9_records = _run_script("scripts/d9_operating_records_check.py")
    if d9_records.returncode == 0 and "Result: PASS" in d9_records.stdout:
        checks[21].pass_("PASS")
    else:
        checks[21].fail((d9_records.stdout + d9_records.stderr)[:160])

    roadmap = _run_script("scripts/phase3_roadmap_check.py")
    if roadmap.returncode == 0 and "Result: PASS" in roadmap.stdout:
        checks[22].pass_("PASS")
    else:
        checks[22].fail((roadmap.stdout + roadmap.stderr)[:160])

    project_plan = _run_script("scripts/ie_auto_project_plan_check.py")
    if project_plan.returncode == 0 and "Result: PASS" in project_plan.stdout:
        checks[23].pass_("PASS")
    else:
        checks[23].fail((project_plan.stdout + project_plan.stderr)[:160])

    execution_chain = _run_script("scripts/project_execution_chain_check.py")
    if execution_chain.returncode == 0 and "Result: PASS" in execution_chain.stdout:
        checks[24].pass_("PASS")
    else:
        checks[24].fail((execution_chain.stdout + execution_chain.stderr)[:160])

    execution_status = _run_script("scripts/project_execution_status.py")
    if execution_status.returncode == 0 and "Result: PASS" in execution_status.stdout:
        checks[25].pass_("PASS")
    else:
        checks[25].fail((execution_status.stdout + execution_status.stderr)[:160])

    acceptance_audit = _run_script("scripts/project_execution_acceptance_audit_check.py")
    if acceptance_audit.returncode == 0 and "Result: PASS" in acceptance_audit.stdout:
        checks[26].pass_("PASS")
    else:
        checks[26].fail((acceptance_audit.stdout + acceptance_audit.stderr)[:160])

    execution_records = _run_script("scripts/project_execution_records_check.py")
    if execution_records.returncode == 0 and "Result: PASS" in execution_records.stdout:
        checks[27].pass_("PASS")
    else:
        checks[27].fail((execution_records.stdout + execution_records.stderr)[:160])

    agent_guide = _run_script("scripts/agent_guide_check.py")
    if agent_guide.returncode == 0 and "Result: PASS" in agent_guide.stdout:
        checks[28].pass_("PASS")
    else:
        checks[28].fail((agent_guide.stdout + agent_guide.stderr)[:160])

    readme = _run_script("scripts/readme_check.py")
    if readme.returncode == 0 and "Result: PASS" in readme.stdout:
        checks[29].pass_("PASS")
    else:
        checks[29].fail((readme.stdout + readme.stderr)[:160])

    desktop_transition = _run_script("scripts/desktop_transition_roadmap_check.py")
    if desktop_transition.returncode == 0 and "Result: PASS" in desktop_transition.stdout:
        checks[30].pass_("PASS")
    else:
        checks[30].fail((desktop_transition.stdout + desktop_transition.stderr)[:160])

    reorientation = _run_script("scripts/project_reorientation_summary_check.py")
    if reorientation.returncode == 0 and "Result: PASS" in reorientation.stdout:
        checks[31].pass_("PASS")
    else:
        checks[31].fail((reorientation.stdout + reorientation.stderr)[:160])

    dev_guide = _run_script("scripts/dev_guide_check.py")
    if dev_guide.returncode == 0 and "Result: PASS" in dev_guide.stdout:
        checks[32].pass_("PASS")
    else:
        checks[32].fail((dev_guide.stdout + dev_guide.stderr)[:160])

    deployment_readiness = _run_script("scripts/deployment_readiness_checklist_check.py")
    if deployment_readiness.returncode == 0 and "Result: PASS" in deployment_readiness.stdout:
        checks[33].pass_("PASS")
    else:
        checks[33].fail((deployment_readiness.stdout + deployment_readiness.stderr)[:160])

    testing_guide = _run_script("scripts/testing_guide_check.py")
    if testing_guide.returncode == 0 and "Result: PASS" in testing_guide.stdout:
        checks[34].pass_("PASS")
    else:
        checks[34].fail((testing_guide.stdout + testing_guide.stderr)[:160])

    operator_guide = _run_script("scripts/operator_guide_check.py")
    if operator_guide.returncode == 0 and "Result: PASS" in operator_guide.stdout:
        checks[35].pass_("PASS")
    else:
        checks[35].fail((operator_guide.stdout + operator_guide.stderr)[:160])

    handoff_code, handoff_text, handoff_output = _generate_handoff()
    if handoff_code == 0 and handoff_text:
        checks[36].pass_("generated")
    else:
        checks[36].fail(handoff_output[:160])

    missing_markers = [marker for marker in HANDOFF_MARKERS if marker not in handoff_text]
    if not missing_markers:
        checks[37].pass_("commands and safety boundaries")
    else:
        checks[37].fail(", ".join(missing_markers))

    print("D8 Staging Execution Pack Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
