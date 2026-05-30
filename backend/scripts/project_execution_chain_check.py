"""Run the local project execution planning and staging-readiness gate chain."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

CHAIN = (
    ("IE Auto project plan", "scripts/ie_auto_project_plan_check.py"),
    ("Phase 3 roadmap", "scripts/phase3_roadmap_check.py"),
    ("D8 stage goal matrix", "scripts/d8_stage_goal_matrix_check.py"),
    ("D8 readiness audit", "scripts/d8_readiness_audit.py"),
    ("D8 production coordination", "scripts/d8_production_coordination_check.py"),
    ("D9 post-launch plan", "scripts/d9_post_launch_plan_check.py"),
    ("D9 operating records", "scripts/d9_operating_records_check.py"),
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


def main() -> int:
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
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    if passed:
        print("State: READY_FOR_STAGING_HANDOFF")
    else:
        print("State: LOCAL_EXECUTION_CHAIN_INCOMPLETE")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
