"""Check D8 production coordination readiness from local plans and saved evidence."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

PLAN_DOC = REPO_ROOT / "docs" / "phase3" / "d8_production_coordination_plan.md"
RUNBOOK_DOC = REPO_ROOT / "docs" / "phase3" / "d8_production_coordination_runbook.md"
REQUIRED_PLAN_MARKERS = (
    "STAGING_VALIDATED",
    "D8 Production Coordination Runbook",
    "service.intelli-opus.com",
    "No nginx or upstream change from this repository",
    "No customer or supplier notification",
    "No email, webhook, carrier API",
    "No automatic order, shipment, delivery, payment, or partner-selection mutation",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "Rollback",
    "Go / No-Go",
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


def _readiness_status() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "scripts/d8_readiness_audit.py"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    status = "UNKNOWN"
    for line in output.splitlines():
        if line.startswith("Overall:"):
            status = line.split(":", 1)[1].strip()
            break
    return result.returncode == 0 and status != "UNKNOWN", status


def _evidence_review_status() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "scripts/d8_staging_evidence_review_check.py"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    status = "UNKNOWN"
    for line in output.splitlines():
        if line.startswith("Review State:"):
            status = line.split(":", 1)[1].strip()
            break
    return result.returncode == 0 and status != "UNKNOWN", status


def _plan_text() -> str:
    return PLAN_DOC.read_text(encoding="utf-8") if PLAN_DOC.exists() else ""


def _runbook_text() -> str:
    return RUNBOOK_DOC.read_text(encoding="utf-8") if RUNBOOK_DOC.exists() else ""


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    checks = [
        Check("production coordination plan exists"),
        Check("production coordination safety markers"),
        Check("production coordination runbook exists"),
        Check("D8 readiness audit available"),
        Check("D8 evidence review available"),
        Check("production coordination state"),
    ]

    text = _plan_text()
    if text:
        checks[0].pass_(_display_path(PLAN_DOC))
    else:
        checks[0].fail(_display_path(PLAN_DOC))

    missing = [marker for marker in REQUIRED_PLAN_MARKERS if marker not in text]
    checks[1].pass_("required gates and boundaries") if not missing else checks[1].fail(", ".join(missing))

    runbook_text = _runbook_text()
    if runbook_text:
        checks[2].pass_(_display_path(RUNBOOK_DOC))
    else:
        checks[2].fail(_display_path(RUNBOOK_DOC))

    audit_ok, status = _readiness_status()
    checks[3].pass_(status) if audit_ok else checks[3].fail(status)

    review_ok, review_state = _evidence_review_status()
    checks[4].pass_(review_state) if review_ok else checks[4].fail(review_state)

    if status == "STAGING_VALIDATED" and review_state == "READY_FOR_PRODUCTION_COORDINATION_REVIEW":
        checks[5].pass_("READY_FOR_PRODUCTION_COORDINATION")
        coordination_state = "READY_FOR_PRODUCTION_COORDINATION"
    elif status in {"READY_FOR_STAGING", "STAGING_GAPS_OPEN"}:
        checks[5].pass_(f"WAITING_FOR_STAGING_VALIDATION: {status}")
        coordination_state = "WAITING_FOR_STAGING_VALIDATION"
    elif status == "STAGING_VALIDATED":
        checks[5].fail(f"BLOCKED_BY_EVIDENCE_REVIEW: {review_state}")
        coordination_state = "BLOCKED_BY_EVIDENCE_REVIEW"
    else:
        checks[5].fail(f"BLOCKED_BY_READINESS_AUDIT: {status}")
        coordination_state = "BLOCKED_BY_READINESS_AUDIT"

    print("D8 Production Coordination Check")
    for check in checks:
        print(check.line())
    local_plan_ok = all(check.ok for check in checks[:5])
    passed = local_plan_ok and checks[5].ok
    print(f"Coordination State: {coordination_state}")
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
