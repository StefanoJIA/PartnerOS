"""Run the local project execution planning and staging-readiness gate chain."""

from __future__ import annotations

import subprocess
import sys
import re
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
REPORT_NAME_PATTERN = re.compile(r"^project_execution_chain_\d{8}\.md$")

CHAIN = (
    ("IE Auto project plan", "scripts/ie_auto_project_plan_check.py"),
    ("Phase 3 roadmap", "scripts/phase3_roadmap_check.py"),
    ("D8 stage goal matrix", "scripts/d8_stage_goal_matrix_check.py"),
    ("Project execution acceptance audit", "scripts/project_execution_acceptance_audit_check.py"),
    ("Operator guide", "scripts/operator_guide_check.py"),
    ("D8 readiness audit", "scripts/d8_readiness_audit.py"),
    ("D8 local staging rehearsal", "scripts/d8_local_staging_rehearsal_check.py"),
    ("D8 staging handoff bundle", "scripts/d8_staging_handoff_bundle_check.py"),
    ("D8 staging operator runbook", "scripts/d8_staging_operator_runbook_check.py"),
    ("D8 staging input preflight", "scripts/d8_staging_input_preflight_check.py"),
    ("D8 staging access request", "scripts/d8_staging_access_request_check.py"),
    ("D8 staging operator response intake", "scripts/d8_staging_operator_response_intake_check.py"),
    ("D8 staging gap triage", "scripts/d8_staging_gap_triage_check.py"),
    ("D8 staging evidence review", "scripts/d8_staging_evidence_review_check.py"),
    ("D8 production coordination", "scripts/d8_production_coordination_check.py"),
    ("D8 production coordination runbook", "scripts/d8_production_coordination_runbook_check.py"),
    ("D9 post-launch plan", "scripts/d9_post_launch_plan_check.py"),
    ("D9 operating execution pack", "scripts/d9_operating_execution_pack_check.py"),
    ("D9 operating loop kickoff", "scripts/d9_operating_loop_kickoff_check.py"),
    ("D9.1 operating health review", "scripts/d9_1_operating_health_review_check.py"),
    ("D9.2 order operations loop", "scripts/d9_2_order_operations_loop_check.py"),
    ("D9.3 market response loop", "scripts/d9_3_market_response_loop_check.py"),
    ("D9.4 improvement backlog", "scripts/d9_4_improvement_backlog_check.py"),
    ("D9 operating records", "scripts/d9_operating_records_check.py"),
    ("Project execution records", "scripts/project_execution_records_check.py"),
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

    def markdown_row(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        if redaction_issues(Path(f"{self.label}.txt"), self.detail):
            detail = "summary omitted because it contained secret-like or forbidden markers"
        else:
            detail = self.detail.replace("|", "\\|") or "n/a"
        return f"| {self.label} | {status} | {detail} |"


def _parse_args(argv: list[str] | None = None):
    parser = ArgumentParser(description="Run the local project execution planning gate chain.")
    parser.add_argument(
        "--report-markdown",
        help="Optional redacted Markdown report path, for example ../docs/records/project_execution_chain_YYYYMMDD.md. Relative paths are resolved from backend/.",
    )
    return parser.parse_args(argv or [])


def _run_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _summary(output: str) -> str:
    for prefix in ("Overall:", "Coordination State:", "Result:"):
        for line in output.splitlines():
            if line.startswith(prefix):
                return line.strip()
    return output.splitlines()[-1].strip() if output.splitlines() else "no output"


def _safe_output_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    resolved = path.resolve()
    forbidden_roots = ((REPO_ROOT / "local_data").resolve(), (BACKEND_ROOT / "storage").resolve())
    for root in forbidden_roots:
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        raise ValueError("project execution report must not be under local_data or backend/storage")
    if not REPORT_NAME_PATTERN.match(resolved.name):
        raise ValueError("project execution report must be named project_execution_chain_YYYYMMDD.md")
    return resolved


def _write_report(raw_path: str | None, checks: list[Check], state: str) -> None:
    if not raw_path:
        return
    path = _safe_output_path(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Project Execution Chain Report",
        "",
        f"Generated at: {generated}",
        f"State: `{state}`",
        "",
        "This report stores gate labels, pass/fail status, and redacted one-line summaries only. It does not store raw command output, response bodies, portal tokens, customer files, backend storage paths, or secrets.",
        "",
        "| Gate | Status | Summary |",
        "|---|---|---|",
    ]
    lines.extend(check.markdown_row() for check in checks)
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- No staging or cloud endpoint is called by this aggregate gate.",
            "- No email, webhook, carrier API, customer notification, supplier notification, order mutation, shipment mutation, payment action, nginx edit, or service portal deployment is performed.",
            "- Run strict staging evidence separately with real environment values when the staging operator is ready.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    checks: list[Check] = []
    for label, script in CHAIN:
        check = Check(label)
        result = _run_script(script)
        output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        if result.returncode == 0:
            check.pass_(_summary(output))
        else:
            failing_line = next((line for line in output.splitlines() if line.startswith("[FAIL]")), "")
            check.fail(failing_line or _summary(output))
        checks.append(check)

    print("Project Execution Chain Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    state = "READY_FOR_STAGING_HANDOFF" if passed else "LOCAL_EXECUTION_CHAIN_INCOMPLETE"
    try:
        _write_report(args.report_markdown, checks, state)
    except OSError as exc:
        print(f"[FAIL] report output write ({str(exc)[:120]})")
        passed = False
        state = "LOCAL_EXECUTION_CHAIN_INCOMPLETE"
    except ValueError as exc:
        print(f"[FAIL] report output path ({exc})")
        passed = False
        state = "LOCAL_EXECUTION_CHAIN_INCOMPLETE"
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    print(f"State: {state}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
