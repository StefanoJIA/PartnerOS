"""Validate the IE Auto project plan against current execution artifacts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "phase3" / "ie_auto_project_plan.md"

REQUIRED_POSITIONING = (
    "intelliOffice / PartnerOS",
    "service.intelli-opus.com",
    "HOSUN, JOOBOO, and future factories",
    "must not hard-code brand privilege",
)
REQUIRED_LIFECYCLE = (
    "Lead",
    "Product Fit",
    "Manual Outreach",
    "Quote",
    "Customer Confirmation",
    "Order",
    "Partner Split",
    "Supplier Confirmation",
    "Production Milestones",
    "Shipment Tracking",
    "Feedback",
    "Market Intelligence",
)
REQUIRED_STATE_ROWS = (
    "D5 Lead Intelligence",
    "D6 Quote MVP",
    "D7.9 Resource Center",
    "D8.1 RBAC / Scoped Access",
    "D8.5 Market Response Intelligence",
    "D8 Production Coordination Plan",
    "D8 Production Coordination Runbook",
    "D9 Post-Launch Operating Loop",
    "D9 Operating Execution Pack",
    "D9 Operating Loop Kickoff",
    "D9.1 Operating Health Review",
    "D9.2 Order Operations Loop",
    "D9.3 Market Response Loop",
    "D9.4 Improvement Backlog",
    "D9 Operating Records Policy",
    "D8 Staging Handoff Bundle",
    "D8 Staging Operator Runbook",
    "D8 Local Staging Rehearsal",
    "D8 Staging Input Preflight",
    "D8 Staging Access Request",
    "D8 Staging Operator Response Intake",
    "D8 Staging Gap Triage",
    "D8 Staging Evidence Review",
    "Project Execution Chain Gate",
    "Project Execution Acceptance Audit",
)
REQUIRED_ORDER_MARKERS = (
    "D7.9 Resource Center (done)",
    "D8.1 RBAC / scoped access (done)",
    "D8.5 Market response intelligence (done)",
    "Strict staging/cloud validation (evidence workflow added)",
    "D8 production coordination plan (added)",
    "D8 production coordination runbook (added)",
    "D9 post-launch operating loop (planned)",
    "D9 operating execution pack (planned)",
    "D9 operating loop kickoff (planned)",
    "D9.1 operating health review (planned)",
    "D9.2 order operations loop (planned)",
    "D9.3 market response loop (planned)",
    "D9.4 improvement backlog (planned)",
    "D9 operating records policy (planned)",
    "D8 staging handoff bundle (added)",
    "D8 staging operator runbook (added)",
    "D8 local staging rehearsal (added)",
    "D8 staging input preflight (added)",
    "D8 staging access request (added)",
    "D8 staging operator response intake (added)",
    "D8 staging gap triage (added)",
    "D8 staging evidence review (added)",
    "project execution chain gate (added)",
    "project execution acceptance audit (added)",
)
REQUIRED_SAFETY = (
    "No automatic email / LinkedIn / Outlook sending",
    "No automatic supplier or customer notification",
    "No automatic order creation from PDF parsing",
    "No automatic production, shipment, payment, inventory reservation, or delivery promise",
    "No internal cost, margin, pricing breakdown",
    "AI can assist",
    "must not execute irreversible business actions",
)
REQUIRED_NEXT_BRIEF = (
    "Strict staging evidence run",
    "scripts/d8_strict_staging_evidence_check.py",
    "BACKEND_BASE_URL",
    "READY_FOR_STAGING",
    "STAGING_GAPS_OPEN",
    "STAGING_VALIDATED",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "d9_operating_records_policy.md",
)
REQUIRED_LINKED_DOCS = (
    "docs/phase3/d8_delivery_stage_goal_matrix.md",
    "docs/phase3/d8_readiness_audit.md",
    "docs/phase3/d8_staging_operator_handoff.md",
    "docs/phase3/d8_staging_execution_pack.md",
    "docs/phase3/d8_local_staging_rehearsal.md",
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
    return PLAN_DOC.read_text(encoding="utf-8") if PLAN_DOC.exists() else ""


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def _missing_files(paths: tuple[str, ...]) -> list[str]:
    return [path for path in paths if not (REPO_ROOT / path).exists()]


def main() -> int:
    checks = [
        Check("IE Auto project plan exists"),
        Check("product positioning and partner neutrality"),
        Check("operating lifecycle is complete"),
        Check("current state mapping reaches D9"),
        Check("recommended execution order reaches D9"),
        Check("non-negotiable safety rules"),
        Check("immediate next brief remains strict staging"),
        Check("referenced D8/D9 docs exist"),
    ]

    text = _text()
    checks[0].pass_(_display_path(PLAN_DOC)) if text else checks[0].fail(_display_path(PLAN_DOC))

    missing = _missing_markers(text, REQUIRED_POSITIONING)
    checks[1].pass_("PartnerOS, service portal, neutral partners") if not missing else checks[1].fail(
        ", ".join(missing)
    )

    missing = _missing_markers(text, REQUIRED_LIFECYCLE)
    checks[2].pass_(f"{len(REQUIRED_LIFECYCLE)} stages") if not missing else checks[2].fail(", ".join(missing))

    missing = _missing_markers(text, REQUIRED_STATE_ROWS)
    checks[3].pass_("D5-D9") if not missing else checks[3].fail(", ".join(missing))

    missing = _missing_markers(text, REQUIRED_ORDER_MARKERS)
    checks[4].pass_("D7.9 through D9") if not missing else checks[4].fail(", ".join(missing))

    missing = _missing_markers(text, REQUIRED_SAFETY)
    checks[5].pass_("manual and advisory boundaries") if not missing else checks[5].fail(", ".join(missing))

    missing = _missing_markers(text, REQUIRED_NEXT_BRIEF)
    checks[6].pass_("strict staging evidence") if not missing else checks[6].fail(", ".join(missing))

    missing_files = _missing_files(REQUIRED_LINKED_DOCS)
    checks[7].pass_(f"{len(REQUIRED_LINKED_DOCS)} docs") if not missing_files else checks[7].fail(
        ", ".join(missing_files)
    )

    print("IE Auto Project Plan Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
