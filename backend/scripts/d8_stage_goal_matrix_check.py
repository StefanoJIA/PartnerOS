"""Check that the D8 delivery stage goal matrix points to real artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

REQUIRED_DOCS = (
    "docs/phase3/d8_delivery_stage_goal_matrix.md",
    "docs/phase3/d7_9_resource_center.md",
    "docs/phase3/d8_1_rbac_scoped_access.md",
    "docs/phase3/d8_2_runtime_hardening.md",
    "docs/phase3/d8_3_service_portal_staging_integration.md",
    "docs/phase3/d8_4_multi_partner_operations_dashboard.md",
    "docs/phase3/d8_5_market_response_intelligence.md",
    "docs/phase3/d8_integration_hardening.md",
    "docs/phase3/d8_strict_staging_cloud_validation.md",
    "docs/phase3/d8_local_staging_rehearsal.md",
    "docs/phase3/d8_readiness_audit.md",
    "docs/phase3/d8_staging_operator_handoff.md",
    "docs/phase3/d8_staging_handoff_bundle.md",
    "docs/phase3/d8_staging_input_preflight.md",
    "docs/phase3/d8_staging_access_request.md",
    "docs/phase3/d8_staging_operator_response_intake.md",
    "docs/phase3/d8_staging_gap_triage.md",
    "docs/phase3/d8_staging_execution_pack.md",
    "docs/phase3/d8_staging_records_policy.md",
    "docs/phase3/d8_staging_evidence_review.md",
    "docs/phase3/d8_production_coordination_plan.md",
    "docs/phase3/d9_post_launch_operating_loop.md",
    "docs/phase3/d9_operating_loop_kickoff.md",
    "docs/phase3/d9_1_operating_health_review.md",
    "docs/phase3/d9_2_order_operations_loop.md",
    "docs/phase3/d9_3_market_response_loop.md",
    "docs/phase3/d9_operating_records_policy.md",
    "docs/phase3/project_execution_chain_gate.md",
    "docs/phase3/project_execution_acceptance_audit.md",
    "docs/phase3/phase3_roadmap.md",
    "docs/phase3/ie_auto_project_plan.md",
)
REQUIRED_SCRIPTS = (
    "backend/scripts/d7_9_resource_center_check.py",
    "backend/scripts/d8_1_rbac_scoped_access_check.py",
    "backend/scripts/d8_2_runtime_hardening_check.py",
    "backend/scripts/d8_3_service_portal_staging_check.py",
    "backend/scripts/d8_4_partner_operations_check.py",
    "backend/scripts/d8_5_market_response_check.py",
    "backend/scripts/d8_integration_hardening_check.py",
    "backend/scripts/d8_strict_staging_evidence_check.py",
    "backend/scripts/d8_local_staging_rehearsal_check.py",
    "backend/scripts/d8_readiness_audit.py",
    "backend/scripts/d8_staging_operator_handoff.py",
    "backend/scripts/d8_staging_handoff_bundle_check.py",
    "backend/scripts/d8_staging_input_preflight_check.py",
    "backend/scripts/d8_staging_access_request_check.py",
    "backend/scripts/d8_staging_operator_response_intake_check.py",
    "backend/scripts/d8_staging_gap_triage_check.py",
    "backend/scripts/d8_staging_execution_pack_check.py",
    "backend/scripts/d8_staging_records_check.py",
    "backend/scripts/d8_staging_evidence_review_check.py",
    "backend/scripts/d8_production_coordination_check.py",
    "backend/scripts/d9_post_launch_plan_check.py",
    "backend/scripts/d9_operating_loop_kickoff_check.py",
    "backend/scripts/d9_1_operating_health_review_check.py",
    "backend/scripts/d9_2_order_operations_loop_check.py",
    "backend/scripts/d9_3_market_response_loop_check.py",
    "backend/scripts/d9_operating_records_check.py",
    "backend/scripts/phase3_roadmap_check.py",
    "backend/scripts/ie_auto_project_plan_check.py",
    "backend/scripts/project_execution_chain_check.py",
    "backend/scripts/project_execution_acceptance_audit_check.py",
    "backend/scripts/project_execution_records_check.py",
)
REQUIRED_MATRIX_MARKERS = (
    "D7.9 Resource Center",
    "D8.1 RBAC / Scoped Access",
    "D8.2 Runtime Hardening",
    "D8.3 Service Portal Staging",
    "D8.4 Partner Operations",
    "D8.5 Market Response",
    "D8 Integration Hardening",
    "Strict Staging / Cloud Validation",
    "D8 Local Staging Rehearsal",
    "D8 Readiness Audit",
    "D8 Staging Operator Handoff",
    "D8 Staging Handoff Bundle",
    "D8 Staging Input Preflight",
    "D8 Staging Access Request",
    "D8 Staging Operator Response Intake",
    "D8 Staging Gap Triage",
    "D8 Staging Execution Pack",
    "D8 Staging Records Policy",
    "D8 Staging Evidence Review",
    "D8 Production Coordination",
    "D9 Post-Launch Operating Loop",
    "D9 Operating Loop Kickoff",
    "D9.1 Operating Health Review",
    "D9.2 Order Operations Loop",
    "D9.3 Market Response Loop",
    "D9 Operating Records Policy",
    "Project Execution Chain Gate",
    "Project Execution Acceptance Audit",
    "Phase 3 Roadmap Check",
    "IE Auto Project Plan Check",
    "Project Execution Chain Check",
    "Project Execution Records Check",
    "--evidence-json",
    "--gap-markdown",
    "No automatic customer or supplier notification",
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


def _exists(paths: tuple[str, ...]) -> list[str]:
    return [path for path in paths if not (REPO_ROOT / path).exists()]


def main() -> int:
    checks = [
        Check("required docs exist"),
        Check("required scripts exist"),
        Check("matrix contains stage markers"),
        Check("matrix keeps safety boundaries"),
        Check("strict staging output artifacts documented"),
    ]

    missing_docs = _exists(REQUIRED_DOCS)
    checks[0].pass_(f"{len(REQUIRED_DOCS)} docs") if not missing_docs else checks[0].fail(", ".join(missing_docs))

    missing_scripts = _exists(REQUIRED_SCRIPTS)
    checks[1].pass_(f"{len(REQUIRED_SCRIPTS)} scripts") if not missing_scripts else checks[1].fail(
        ", ".join(missing_scripts)
    )

    matrix_path = REPO_ROOT / "docs/phase3/d8_delivery_stage_goal_matrix.md"
    text = matrix_path.read_text(encoding="utf-8") if matrix_path.exists() else ""
    missing_markers = [marker for marker in REQUIRED_MATRIX_MARKERS if marker not in text]
    checks[2].pass_("all stages") if not missing_markers else checks[2].fail(", ".join(missing_markers))

    safety_terms = ("No automatic", "No email", "No customer-facing internal cost", "AI remains advisory")
    missing_safety = [term for term in safety_terms if term not in text]
    checks[3].pass_("safety invariants") if not missing_safety else checks[3].fail(", ".join(missing_safety))

    if "--evidence-json" in text and "--gap-markdown" in text and "docs/records" in text:
        checks[4].pass_("evidence and gap outputs")
    else:
        checks[4].fail("missing evidence/gap command")

    print("D8 Stage Goal Matrix Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
