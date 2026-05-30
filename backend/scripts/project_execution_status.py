"""Summarize the current project execution state from authoritative local gates."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


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


def _next_action(chain_state: str, readiness: str, coordination: str) -> tuple[str, str]:
    if chain_state != "READY_FOR_STAGING_HANDOFF":
        return "LOCAL_EXECUTION_CHAIN_INCOMPLETE", "Fix the failing local gate before staging handoff."
    if readiness == "READY_FOR_STAGING":
        return (
            "READY_FOR_STAGING_HANDOFF",
            "Use docs/phase3/d8_staging_access_request.md to obtain private staging values, then run strict staging evidence.",
        )
    if readiness == "STAGING_GAPS_OPEN":
        return "STAGING_GAPS_OPEN", "Close the latest strict staging gap register, then rerun strict staging evidence."
    if readiness == "STAGING_VALIDATED" and coordination == "READY_FOR_PRODUCTION_COORDINATION":
        return "READY_FOR_PRODUCTION_COORDINATION", "Proceed with the D8 production coordination Go / No-Go handoff."
    if readiness == "STAGING_VALIDATED":
        return "STAGING_VALIDATED", "Run production coordination and confirm the Go / No-Go plan."
    return "LOCAL_ARTIFACTS_INCOMPLETE", "Run the reported failing gate and fix missing local artifacts."


def main() -> int:
    checks = [
        Check("project execution chain"),
        Check("D8 readiness audit"),
        Check("D8 production coordination"),
    ]

    chain = _run_script("scripts/project_execution_chain_check.py")
    chain_output = _combined_output(chain)
    chain_state = _extract_line(chain_output, "State:")
    if chain.returncode == 0 and chain_state != "UNKNOWN":
        checks[0].pass_(chain_state)
    else:
        checks[0].fail(next((line for line in chain_output.splitlines() if line.startswith("[FAIL]")), chain_state))

    readiness = _run_script("scripts/d8_readiness_audit.py")
    readiness_output = _combined_output(readiness)
    readiness_state = _extract_line(readiness_output, "Overall:")
    if readiness.returncode == 0 and readiness_state != "UNKNOWN":
        checks[1].pass_(readiness_state)
    else:
        checks[1].fail(next((line for line in readiness_output.splitlines() if line.startswith("[FAIL]")), readiness_state))

    production = _run_script("scripts/d8_production_coordination_check.py")
    production_output = _combined_output(production)
    coordination_state = _extract_line(production_output, "Coordination State:")
    if production.returncode == 0 and coordination_state != "UNKNOWN":
        checks[2].pass_(coordination_state)
    else:
        checks[2].fail(next((line for line in production_output.splitlines() if line.startswith("[FAIL]")), coordination_state))

    current_stage, next_action = _next_action(chain_state, readiness_state, coordination_state)
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
