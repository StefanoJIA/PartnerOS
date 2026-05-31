"""Validate the project reorientation summary against the current execution state."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "project_reorientation_summary.md"

REQUIRED_MARKERS = (
    "Project Reorientation Summary",
    "READY_FOR_STAGING_HANDOFF",
    "D5 Lead Intelligence",
    "Closed as D5 Final",
    "D6 Quote MVP",
    "Closed as D6 Final",
    "Closed through D7.9",
    "waiting for real staging values and strict evidence",
    "Planned behind `STAGING_VALIDATED`",
    "not D0/D1 kickoff",
    "real `BACKEND_BASE_URL`",
    "real `SERVICE_PORTAL_PARTNEROS_TOKEN`",
    "python scripts/project_reorientation_summary_check.py",
    "python scripts/project_execution_chain_check.py",
    "backend port `8014`",
    "service.intelli-opus.com",
    "strict field whitelists",
    "Manufacturing partners are peer rows",
    "No product path may require final users to run pgAdmin",
    "No automatic email, webhook, carrier API",
)
FORBIDDEN_MARKERS = (
    "Current priority: complete **D0 documentation**",
    "是否进入 Phase D1",
    "immediately start D1",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "raw response body:",
    "password_hash",
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


def main() -> int:
    checks = [
        Check("project reorientation summary exists"),
        Check("project reorientation summary matches current execution state"),
        Check("project reorientation summary avoids stale D0/D1 priority"),
        Check("project reorientation summary is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/project_reorientation_summary.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:3] if marker in text]
    checks[2].pass_("no stale D0/D1 priority markers") if not stale else checks[2].fail(", ".join(stale))

    forbidden = [marker for marker in FORBIDDEN_MARKERS[3:] if marker in text]
    forbidden.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[3].pass_("no secret-like markers") if not forbidden else checks[3].fail(", ".join(forbidden[:8]))

    print("Project Reorientation Summary Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
