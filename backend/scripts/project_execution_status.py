"""Summarize the current project execution state from authoritative local gates."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
RECORDS_ROOT = REPO_ROOT / "docs" / "records"
ACCESS_REQUEST_PATTERN = re.compile(r"^d8_staging_access_request_\d{8}\.md$")


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


def _run_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)


def _extract_line(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return "UNKNOWN"


def _result_pass(result: subprocess.CompletedProcess[str], output: str) -> bool:
    if result.returncode != 0:
        return False
    result_lines = [line.strip() for line in output.splitlines() if line.strip().startswith("Result:")]
    return not result_lines or result_lines[-1] == "Result: PASS"


def _latest_access_request_record() -> str:
    if not RECORDS_ROOT.exists():
        return "docs/records/d8_staging_access_request_YYYYMMDD.md"
    records = sorted(
        (path for path in RECORDS_ROOT.glob("d8_staging_access_request_*.md") if ACCESS_REQUEST_PATTERN.match(path.name)),
        key=lambda path: path.name,
        reverse=True,
    )
    if not records:
        return "docs/records/d8_staging_access_request_YYYYMMDD.md"
    return f"docs/records/{records[0].name}"


def _next_action(
    chain_state: str,
    readiness: str,
    coordination: str,
    access_request_record: str | None = None,
) -> tuple[str, str]:
    access_request_record = access_request_record or _latest_access_request_record()
    if chain_state != "READY_FOR_STAGING_HANDOFF":
        return "LOCAL_EXECUTION_CHAIN_INCOMPLETE", "Fix the failing local gate before staging handoff."
    if readiness == "READY_FOR_STAGING":
        return (
            "READY_FOR_STAGING_HANDOFF",
            f"Use docs/phase3/d8_staging_handoff_bundle.md and docs/phase3/d8_staging_operator_runbook.md, track the latest committed request at {access_request_record}, obtain private staging values via d8_staging_access_request.md, then run strict staging evidence.",
        )
    if readiness == "STAGING_GAPS_OPEN":
        return "STAGING_GAPS_OPEN", "Close the latest strict staging gap register, then rerun strict staging evidence."
    if readiness == "STAGING_EVIDENCE_LOCAL_REHEARSAL":
        return (
            "STAGING_EVIDENCE_LOCAL_REHEARSAL",
            "Replace the local rehearsal PASS evidence with strict staging evidence from real staging values before production coordination.",
        )
    if readiness == "STAGING_VALIDATED" and coordination == "READY_FOR_PRODUCTION_COORDINATION":
        return (
            "READY_FOR_PRODUCTION_COORDINATION",
            "Proceed with docs/phase3/d8_production_coordination_runbook.md for the D8 production coordination Go / No-Go handoff.",
        )
    if readiness == "STAGING_VALIDATED" and coordination == "BLOCKED_BY_EVIDENCE_REVIEW":
        return (
            "BLOCKED_BY_EVIDENCE_REVIEW",
            "Run scripts/d8_staging_evidence_review_check.py, fix the reviewed evidence/gap state, then rerun production coordination.",
        )
    if readiness == "STAGING_VALIDATED":
        return (
            "STAGING_VALIDATED",
            "Run production coordination and confirm the Go / No-Go plan with docs/phase3/d8_production_coordination_runbook.md.",
        )
    return "LOCAL_ARTIFACTS_INCOMPLETE", "Run the reported failing gate and fix missing local artifacts."


def main() -> int:
    checks = [
        Check("project execution chain gate"),
        Check("project execution chain"),
        Check("D8 readiness audit"),
        Check("D8 production coordination"),
    ]

    chain_gate = _run_script("scripts/project_execution_chain_gate_check.py")
    chain_gate_output = _combined_output(chain_gate)
    if _result_pass(chain_gate, chain_gate_output):
        checks[0].pass_("PASS")
    else:
        checks[0].fail(next((line for line in chain_gate_output.splitlines() if line.startswith("[FAIL]")), "gate failed"))

    chain = _run_script("scripts/project_execution_chain_check.py")
    chain_output = _combined_output(chain)
    chain_state = _extract_line(chain_output, "State:")
    if _result_pass(chain, chain_output) and chain_state != "UNKNOWN":
        checks[1].pass_(chain_state)
    else:
        checks[1].fail(next((line for line in chain_output.splitlines() if line.startswith("[FAIL]")), chain_state))

    readiness = _run_script("scripts/d8_readiness_audit.py")
    readiness_output = _combined_output(readiness)
    readiness_state = _extract_line(readiness_output, "Overall:")
    if _result_pass(readiness, readiness_output) and readiness_state != "UNKNOWN":
        checks[2].pass_(readiness_state)
    else:
        checks[2].fail(next((line for line in readiness_output.splitlines() if line.startswith("[FAIL]")), readiness_state))

    production = _run_script("scripts/d8_production_coordination_check.py")
    production_output = _combined_output(production)
    coordination_state = _extract_line(production_output, "Coordination State:")
    if _result_pass(production, production_output) and coordination_state != "UNKNOWN":
        checks[3].pass_(coordination_state)
    else:
        checks[3].fail(next((line for line in production_output.splitlines() if line.startswith("[FAIL]")), coordination_state))

    status_chain_state = chain_state if checks[0].ok else "LOCAL_EXECUTION_CHAIN_INCOMPLETE"
    current_stage, next_action = _next_action(
        status_chain_state,
        readiness_state,
        coordination_state,
        _latest_access_request_record(),
    )
    passed = all(check.ok for check in checks)

    print("Project Execution Status")
    for check in checks:
        print(check.line())
    print(f"Current Stage: {current_stage}")
    print(f"Next Action: {next_action}")
    print("Boundaries: no tokens, no .env, no staging calls beyond explicit evidence runs, no notifications, no nginx or service portal deployment.")
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
