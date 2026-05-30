"""Validate redacted project execution chain reports under docs/records."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
RECORDS_ROOT = REPO_ROOT / "docs" / "records"

REPORT_PATTERN = re.compile(r"^project_execution_chain_\d{8}\.md$")
REQUIRED_MARKERS = (
    "Project Execution Chain Report",
    "State:",
    "| Gate | Status | Summary |",
    "READY_FOR_STAGING_HANDOFF",
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


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _reports() -> list[Path]:
    if not RECORDS_ROOT.exists():
        return []
    return sorted(path for path in RECORDS_ROOT.iterdir() if path.is_file() and path.name.startswith("project_execution_chain_"))


def _naming_issues(reports: list[Path]) -> list[str]:
    return [path.name for path in reports if not REPORT_PATTERN.match(path.name)]


def _marker_issues(reports: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in reports:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"{path.name}:unreadable")
            continue
        for marker in REQUIRED_MARKERS:
            if marker not in text:
                issues.append(f"{path.name}:missing {marker}")
    return issues


def _redaction_issues(reports: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in reports:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"{path.name}:unreadable")
            continue
        issues.extend(redaction_issues(path, text))
    return issues


def main() -> int:
    checks = [
        Check("docs/records exists"),
        Check("project execution report names are canonical"),
        Check("project execution reports contain required markers"),
        Check("project execution reports are redacted"),
    ]

    if RECORDS_ROOT.exists() and RECORDS_ROOT.is_dir():
        checks[0].pass_(_display_path(RECORDS_ROOT))
    else:
        checks[0].fail("missing docs/records")

    reports = _reports()
    naming = _naming_issues(reports)
    checks[1].pass_(f"{len(reports)} report(s)") if not naming else checks[1].fail(", ".join(naming))

    markers = _marker_issues(reports)
    checks[2].pass_("all reports") if not markers else checks[2].fail(", ".join(markers[:8]))

    redaction = _redaction_issues(reports)
    checks[3].pass_("no token assignments or forbidden markers") if not redaction else checks[3].fail(
        ", ".join(redaction[:8])
    )

    print("Project Execution Records Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
