"""Validate D9 post-launch operating review records."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
RECORDS_ROOT = REPO_ROOT / "docs" / "records"
POLICY_DOC = REPO_ROOT / "docs" / "phase3" / "d9_operating_records_policy.md"
POLICY_MARKERS = (
    "D9 Operating Records Policy",
    "D9 operating records may be committed only after a redacted D8 Go / No-Go decision record exists",
    "requires each committed D9 record to include the Safety section markers",
    "Owner: TBD` is allowed only as a human owner placeholder",
    "not an auto-assignee, notification target, or permission to create tickets",
)
RECORD_REQUIRED_MARKERS = (
    "## Safety",
    "No tokens or raw response bodies included.",
    "No internal cost, margin, supplier private note, backend path, storage key, database URL, or secret included.",
    "No automatic customer/supplier notification or business-status mutation triggered.",
)

D9_RECORD_PATTERN = re.compile(
    r"^d9_(?:operating_review|operating_health|order_operations|market_response|improvement_backlog)_\d{8}\.md$"
)
D8_GO_NO_GO_PATTERN = re.compile(r"^d8_production_go_no_go_\d{8}\.md$")


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


def _d9_records() -> list[Path]:
    if not RECORDS_ROOT.exists():
        return []
    return sorted(path for path in RECORDS_ROOT.iterdir() if path.is_file() and path.name.startswith("d9_"))


def _d8_go_no_go_records() -> list[Path]:
    if not RECORDS_ROOT.exists():
        return []
    return sorted(
        path for path in RECORDS_ROOT.iterdir() if path.is_file() and D8_GO_NO_GO_PATTERN.match(path.name)
    )


def _naming_issues(records: list[Path]) -> list[str]:
    return [path.name for path in records if not D9_RECORD_PATTERN.match(path.name)]


def _redaction_issues(records: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in records:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"{path.name}:unreadable")
            continue
        issues.extend(redaction_issues(path, text))
    return issues


def _safety_marker_issues(records: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in records:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"{path.name}:unreadable")
            continue
        missing = [marker for marker in RECORD_REQUIRED_MARKERS if marker not in text]
        if missing:
            issues.append(f"{path.name}:missing {', '.join(missing)}")
    return issues


def _policy_text() -> str:
    try:
        return POLICY_DOC.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> int:
    checks = [
        Check("docs/records exists"),
        Check("D9 operating records policy is explicit"),
        Check("D9 operating record names are canonical"),
        Check("D9 operating records are gated by D8 Go / No-Go"),
        Check("D9 operating records include safety markers"),
        Check("D9 operating records are redacted"),
    ]

    policy_text = _policy_text()
    policy_missing = [marker for marker in POLICY_MARKERS if marker not in policy_text]
    checks[1].pass_(f"{len(POLICY_MARKERS)} markers") if not policy_missing else checks[1].fail(
        ", ".join(policy_missing)
    )

    if RECORDS_ROOT.exists() and RECORDS_ROOT.is_dir():
        checks[0].pass_(_display_path(RECORDS_ROOT))
    else:
        checks[0].fail("missing docs/records")

    records = _d9_records()
    naming = _naming_issues(records)
    checks[2].pass_(f"{len(records)} D9 records") if not naming else checks[2].fail(", ".join(naming))

    go_no_go_records = _d8_go_no_go_records()
    if not records:
        checks[3].pass_("no D9 records")
    elif go_no_go_records:
        checks[3].pass_(go_no_go_records[-1].name)
    else:
        checks[3].fail("D9 records require docs/records/d8_production_go_no_go_YYYYMMDD.md")

    safety = _safety_marker_issues(records)
    checks[4].pass_("required record safety markers") if not safety else checks[4].fail(", ".join(safety[:4]))

    redaction = _redaction_issues(records)
    checks[5].pass_("no token assignments or forbidden markers") if not redaction else checks[5].fail(
        ", ".join(redaction[:8])
    )

    print("D9 Operating Records Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
