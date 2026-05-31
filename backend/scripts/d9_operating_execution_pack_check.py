"""Validate the D9 operating execution pack."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DOC = REPO_ROOT / "docs" / "phase3" / "d9_operating_execution_pack.md"

REQUIRED_FILES = (
    "docs/phase3/d9_operating_execution_pack.md",
    "docs/phase3/d9_post_launch_operating_loop.md",
    "docs/phase3/d9_operating_loop_kickoff.md",
    "docs/phase3/d9_1_operating_health_review.md",
    "docs/phase3/d9_2_order_operations_loop.md",
    "docs/phase3/d9_3_market_response_loop.md",
    "docs/phase3/d9_4_improvement_backlog.md",
    "docs/phase3/d9_operating_records_policy.md",
    "backend/scripts/d8_staging_evidence_review_check.py",
    "backend/scripts/d9_operating_execution_pack_check.py",
    "backend/scripts/d9_post_launch_plan_check.py",
    "backend/scripts/d9_operating_loop_kickoff_check.py",
    "backend/scripts/d9_1_operating_health_review_check.py",
    "backend/scripts/d9_2_order_operations_loop_check.py",
    "backend/scripts/d9_3_market_response_loop_check.py",
    "backend/scripts/d9_4_improvement_backlog_check.py",
    "backend/scripts/d9_operating_records_check.py",
)
REQUIRED_DOC_MARKERS = (
    "D9 Operating Execution Pack",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "human Go / No-Go handoff",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "python scripts/d8_staging_evidence_review_check.py",
    "python scripts/d9_post_launch_plan_check.py",
    "python scripts/d9_operating_loop_kickoff_check.py",
    "python scripts/d9_1_operating_health_review_check.py",
    "python scripts/d9_2_order_operations_loop_check.py",
    "python scripts/d9_3_market_response_loop_check.py",
    "python scripts/d9_4_improvement_backlog_check.py",
    "python scripts/d9_operating_records_check.py",
    "No `.env`",
    "No automatic ticket creation",
)
SCRIPTS = (
    "scripts/d8_staging_evidence_review_check.py",
    "scripts/d9_post_launch_plan_check.py",
    "scripts/d9_operating_loop_kickoff_check.py",
    "scripts/d9_1_operating_health_review_check.py",
    "scripts/d9_2_order_operations_loop_check.py",
    "scripts/d9_3_market_response_loop_check.py",
    "scripts/d9_4_improvement_backlog_check.py",
    "scripts/d9_operating_records_check.py",
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


def _run_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _doc_text() -> str:
    try:
        return DOC.read_text(encoding="utf-8")
    except OSError:
        return ""


def _result_pass(result: subprocess.CompletedProcess[str]) -> bool:
    if result.returncode != 0:
        return False
    result_lines = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("Result:")]
    return bool(result_lines) and result_lines[-1] == "Result: PASS"


def main() -> int:
    checks = [
        Check("D9 execution pack files present"),
        Check("D9 execution pack doc is actionable"),
        Check("D9 execution pack doc is redacted"),
        *(Check(f"{script} runs") for script in SCRIPTS),
    ]

    missing_files = _missing_files()
    checks[0].pass_(f"{len(REQUIRED_FILES)} files") if not missing_files else checks[0].fail(
        ", ".join(missing_files)
    )

    text = _doc_text()
    missing_markers = [marker for marker in REQUIRED_DOC_MARKERS if marker not in text]
    checks[1].pass_("commands and boundaries") if not missing_markers else checks[1].fail(
        ", ".join(missing_markers)
    )

    redaction = redaction_issues(DOC, text, include_common_markers=False)
    checks[2].pass_("no secret-like markers") if not redaction else checks[2].fail(", ".join(redaction[:8]))

    for index, script in enumerate(SCRIPTS, start=3):
        result = _run_script(script)
        if _result_pass(result):
            checks[index].pass_("PASS")
        else:
            checks[index].fail((result.stdout + result.stderr)[:160])

    print("D9 Operating Execution Pack Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
