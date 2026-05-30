"""Validate the project execution acceptance audit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DOC = REPO_ROOT / "docs" / "phase3" / "project_execution_acceptance_audit.md"

REQUIRED_MARKERS = (
    "READY_FOR_STAGING_HANDOFF",
    "READY_FOR_STAGING",
    "WAITING_FOR_STAGING_VALIDATION",
    "STAGING_VALIDATED",
    "IE Auto Project Plan",
    "Phase 3 Roadmap",
    "D8 Delivery Stage Goal Matrix",
    "D8 Local Staging Rehearsal",
    "D8 Staging Handoff Bundle",
    "D8 Staging Input Preflight",
    "D8 Staging Access Request",
    "D8 Staging Operator Response Intake",
    "D8 Staging Gap Triage",
    "D8 Staging Evidence Review",
    "D8 Production Coordination Plan",
    "D9 Post-Launch Operating Loop",
    "D9 Operating Loop Kickoff",
    "Project Execution Chain Gate",
    "project_execution_status.py",
    "project_execution_acceptance_audit_check.py",
    "WAITING_FOR_PRIVATE_VALUES",
    "real `BACKEND_BASE_URL`",
    "real `SERVICE_PORTAL_PARTNEROS_TOKEN`",
    "d8_strict_staging_evidence_YYYYMMDD.json",
    "No `.env`",
    "No email, webhook, carrier API",
)
FORBIDDEN_MARKERS = (
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "raw response body:",
    "password_hash",
    "database_url",
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
    try:
        return DOC.read_text(encoding="utf-8")
    except OSError:
        return ""


def _missing(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def _run_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _extract(output: str, prefix: str) -> str:
    for line in output.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return "UNKNOWN"


def main() -> int:
    checks = [
        Check("acceptance audit doc exists"),
        Check("acceptance audit maps requirements to evidence"),
        Check("acceptance audit is redacted"),
        Check("D8 readiness remains pre-staging"),
        Check("production coordination remains gated"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/project_execution_acceptance_audit.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in text.lower()]
    checks[2].pass_("no secret-like markers") if not forbidden else checks[2].fail(", ".join(forbidden))

    readiness = _run_script("scripts/d8_readiness_audit.py")
    readiness_output = "\n".join(part for part in (readiness.stdout.strip(), readiness.stderr.strip()) if part)
    readiness_state = _extract(readiness_output, "Overall:")
    if readiness.returncode == 0 and readiness_state == "READY_FOR_STAGING":
        checks[3].pass_(readiness_state)
    else:
        checks[3].fail(readiness_state)

    production = _run_script("scripts/d8_production_coordination_check.py")
    production_output = "\n".join(part for part in (production.stdout.strip(), production.stderr.strip()) if part)
    coordination_state = _extract(production_output, "Coordination State:")
    if production.returncode == 0 and coordination_state == "WAITING_FOR_STAGING_VALIDATION":
        checks[4].pass_(coordination_state)
    else:
        checks[4].fail(coordination_state)

    print("Project Execution Acceptance Audit Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
