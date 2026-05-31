"""Validate the desktop transition roadmap against the current execution state."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "roadmap_desktop_transition.md"

REQUIRED_MARKERS = (
    "Desktop Transition Roadmap",
    "READY_FOR_STAGING_HANDOFF",
    "PartnerOS is the internal source of truth",
    "Windows-first",
    "D5",
    "Closed as D5 Final",
    "D6",
    "Closed as D6 Final",
    "D7",
    "Closed through D7.9",
    "D8",
    "waiting for real staging values and evidence",
    "D9",
    "Planned behind `STAGING_VALIDATED`",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "human Go / No-Go handoff",
    "docs/records/d8_production_go_no_go_YYYYMMDD.md",
    "python scripts/agent_guide_check.py",
    "python scripts/testing_guide_check.py",
    "python scripts/desktop_transition_roadmap_check.py",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/project_execution_chain_check.py",
    "backend port `8014`",
    "No final-user workflow may require pgAdmin",
    "No automatic email, webhook, carrier API",
    "service.intelli-opus.com",
)
FORBIDDEN_MARKERS = (
    "[ ] README",
    "Phase D5",
    "D5.2",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
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
        Check("desktop transition roadmap exists"),
        Check("desktop transition roadmap matches current D7-D9 execution state"),
        Check("desktop transition roadmap avoids stale checklist markers"),
        Check("desktop transition roadmap is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/roadmap_desktop_transition.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:3] if marker in text]
    checks[2].pass_("no stale D0-D6 checklist markers") if not stale else checks[2].fail(", ".join(stale))

    forbidden = [marker for marker in FORBIDDEN_MARKERS[3:] if marker in text]
    forbidden.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[3].pass_("no secret-like markers") if not forbidden else checks[3].fail(", ".join(forbidden[:8]))

    print("Desktop Transition Roadmap Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
