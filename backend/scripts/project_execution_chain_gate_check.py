"""Validate the project execution chain gate documentation."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "project_execution_chain_gate.md"

REQUIRED_MARKERS = (
    "Project Execution Chain Gate",
    "READY_FOR_STAGING_HANDOFF",
    "LOCAL_EXECUTION_CHAIN_INCOMPLETE",
    "project_execution_chain_gate_check.py",
    "project_execution_chain_check.py",
    "project_execution_status.py",
    "project_execution_records_check.py",
    "Current Proof Records",
    "docs/records/project_execution_chain_20260531.md",
    "docs/records/d8_staging_operator_handoff_20260531.md",
    "docs/records/d8_staging_access_request_20260531.md",
    "D8 staging handoff bundle",
    "D8 staging access request",
    "D8 production coordination",
    "D9 operating records",
    "STAGING_VALIDATED",
    "SERVICE_PORTAL_PARTNEROS_TOKEN",
    "SERVICE_PORTAL_ORIGIN",
    "No automatic customer or supplier notification",
    "No email, webhook, carrier API",
    "AI recommendations and execution summaries remain advisory",
)
FORBIDDEN_MARKERS = (
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
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


def _missing(text: str) -> list[str]:
    return [marker for marker in REQUIRED_MARKERS if marker not in text]


def _forbidden(text: str) -> list[str]:
    issues = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    issues.extend(redaction_issues(DOC, text, include_common_markers=False))
    return issues


def _proof_record_issues() -> list[str]:
    issues: list[str] = []
    for marker in REQUIRED_MARKERS:
        if not marker.startswith("docs/records/"):
            continue
        path = REPO_ROOT / marker
        if not path.is_file():
            issues.append(marker)
    return issues


def main() -> int:
    checks = [
        Check("project execution chain gate doc exists"),
        Check("chain gate names commands, states, proof records, and gates"),
        Check("chain gate proof records exist"),
        Check("chain gate remains redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/phase3/project_execution_chain_gate.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text)
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    record_issues = _proof_record_issues()
    checks[2].pass_("current proof records present") if not record_issues else checks[2].fail(
        ", ".join(record_issues)
    )

    forbidden = _forbidden(text)
    checks[3].pass_("redacted") if not forbidden else checks[3].fail(", ".join(forbidden))

    print("Project Execution Chain Gate Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
