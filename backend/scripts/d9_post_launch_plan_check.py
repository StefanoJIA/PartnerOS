"""Validate the D9 post-launch operating loop plan."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "phase3" / "d9_post_launch_operating_loop.md"
RECORDS_POLICY_DOC = REPO_ROOT / "docs" / "phase3" / "d9_operating_records_policy.md"
KICKOFF_DOC = REPO_ROOT / "docs" / "phase3" / "d9_operating_loop_kickoff.md"
HEALTH_REVIEW_DOC = REPO_ROOT / "docs" / "phase3" / "d9_1_operating_health_review.md"
ORDER_OPERATIONS_DOC = REPO_ROOT / "docs" / "phase3" / "d9_2_order_operations_loop.md"
MARKET_RESPONSE_DOC = REPO_ROOT / "docs" / "phase3" / "d9_3_market_response_loop.md"
IMPROVEMENT_BACKLOG_DOC = REPO_ROOT / "docs" / "phase3" / "d9_4_improvement_backlog.md"

REQUIRED_MARKERS = (
    "D9 Post-Launch Operating Loop",
    "STAGING_VALIDATED",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "python scripts/d8_staging_evidence_review_check.py",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "Portal feedback",
    "Order operations",
    "Market response intelligence",
    "Human review",
    "No automatic customer or supplier notification",
    "No email, webhook, carrier API",
    "No automatic order, shipment, delivery, payment, or partner-selection mutation",
    "No internal cost, margin, pricing breakdown",
    "No nginx or service portal deployment from this repository",
    "D9.1",
    "D9.1 Operating Health Review",
    "D9.2",
    "D9.2 Order Operations Loop",
    "D9.3",
    "D9.3 Market Response Loop",
    "D9.4",
    "D9.4 Improvement Backlog",
    "D9 Operating Records Policy",
    "D9 Operating Loop Kickoff",
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


def _read_text() -> str:
    return PLAN_DOC.read_text(encoding="utf-8") if PLAN_DOC.exists() else ""


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _result_pass(result: subprocess.CompletedProcess[str]) -> bool:
    if result.returncode != 0:
        return False
    result_lines = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("Result:")]
    return bool(result_lines) and result_lines[-1] == "Result: PASS"


def _records_gate_status() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "scripts/d9_operating_records_check.py"],
        cwd=REPO_ROOT / "backend",
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    if _result_pass(result):
        return True, "PASS"
    detail = next((line for line in output.splitlines() if line.startswith("[FAIL]")), "")
    return False, detail or output[:160] or "records gate failed"


def main() -> int:
    checks = [
        Check("D9 plan exists"),
        Check("D9 plan contains stage markers"),
        Check("D9 plan preserves safety boundaries"),
        Check("D9 plan is redacted"),
        Check("D9 entry criteria depend on staging validation"),
        Check("D9 operating records policy exists"),
        Check("D9 operating records gate runs"),
        Check("D9 kickoff checklist exists"),
        Check("D9.1 operating health review exists"),
        Check("D9.2 order operations loop exists"),
        Check("D9.3 market response loop exists"),
        Check("D9.4 improvement backlog exists"),
    ]

    text = _read_text()
    checks[0].pass_(_display_path(PLAN_DOC)) if text else checks[0].fail(_display_path(PLAN_DOC))

    stage_markers = ("D9.1", "D9.2", "D9.3", "D9.4")
    missing_stages = [marker for marker in stage_markers if marker not in text]
    checks[1].pass_("D9.1-D9.4") if not missing_stages else checks[1].fail(", ".join(missing_stages))

    safety_markers = (
        "No automatic customer or supplier notification",
        "No email, webhook, carrier API",
        "No automatic order, shipment, delivery, payment, or partner-selection mutation",
        "No internal cost, margin, pricing breakdown",
        "No nginx or service portal deployment from this repository",
    )
    missing_safety = [marker for marker in safety_markers if marker not in text]
    checks[2].pass_("safety invariants") if not missing_safety else checks[2].fail(", ".join(missing_safety))

    redaction = redaction_issues(PLAN_DOC, text, include_common_markers=False)
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    if (
        "STAGING_VALIDATED" in text
        and "WAITING_FOR_REAL_STAGING_EVIDENCE" in text
        and "D8 Production Coordination Plan" in text
        and "READY_FOR_PRODUCTION_COORDINATION_REVIEW" in text
        and "docs/records/d8_production_go_no_go_YYYYMMDD.md" in text
    ):
        checks[4].pass_("after D8 production coordination, Go / No-Go, and evidence review")
    else:
        checks[4].fail("missing D8/STAGING_VALIDATED/Go-No-Go/evidence review dependency")

    if RECORDS_POLICY_DOC.exists():
        checks[5].pass_(_display_path(RECORDS_POLICY_DOC))
    else:
        checks[5].fail(_display_path(RECORDS_POLICY_DOC))

    records_ok, records_detail = _records_gate_status()
    checks[6].pass_(records_detail) if records_ok else checks[6].fail(records_detail)

    if KICKOFF_DOC.exists():
        checks[7].pass_(_display_path(KICKOFF_DOC))
    else:
        checks[7].fail(_display_path(KICKOFF_DOC))

    if HEALTH_REVIEW_DOC.exists():
        checks[8].pass_(_display_path(HEALTH_REVIEW_DOC))
    else:
        checks[8].fail(_display_path(HEALTH_REVIEW_DOC))

    if ORDER_OPERATIONS_DOC.exists():
        checks[9].pass_(_display_path(ORDER_OPERATIONS_DOC))
    else:
        checks[9].fail(_display_path(ORDER_OPERATIONS_DOC))

    if MARKET_RESPONSE_DOC.exists():
        checks[10].pass_(_display_path(MARKET_RESPONSE_DOC))
    else:
        checks[10].fail(_display_path(MARKET_RESPONSE_DOC))

    if IMPROVEMENT_BACKLOG_DOC.exists():
        checks[11].pass_(_display_path(IMPROVEMENT_BACKLOG_DOC))
    else:
        checks[11].fail(_display_path(IMPROVEMENT_BACKLOG_DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    if missing and checks[0].ok:
        checks.append(Check("D9 required planning markers"))
        checks[-1].fail(", ".join(missing[:8]))

    print("D9 Post-Launch Plan Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
