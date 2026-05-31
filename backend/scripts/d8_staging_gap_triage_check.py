"""Validate the D8 staging gap triage runbook and existing gap registers."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d8_staging_gap_triage.md"
RECORDS_ROOT = REPO_ROOT / "docs" / "records"
GAP_REGISTER_PATTERN = re.compile(r"^d8_strict_staging_gaps_\d{8}\.md$")
ALLOWED_GAP_STATUSES = {"open", "blocked", "fixed_pending_rerun", "closed"}

REQUIRED_DOC_MARKERS = (
    "D8 Staging Gap Triage",
    "strict staging evidence",
    "d8_strict_staging_evidence_YYYYMMDD.json",
    "d8_strict_staging_gaps_YYYYMMDD.md",
    "python scripts/d8_staging_records_check.py",
    "python scripts/d8_readiness_audit.py",
    "configuration, token/CORS, runtime readiness, portal bridge contract, field leakage, test data, or unknown",
    "fixed_pending_rerun",
    "Owner: TBD` is allowed only as a human owner placeholder",
    "not an auto-assignee, notification target, or permission to create tickets",
    "No automatic customer or supplier notification",
    "No customer portal deployment",
)
REQUIRED_GAP_MARKERS = (
    "Recommended action",
    "Owner",
    "Status",
)
FORBIDDEN_MARKERS = (
    "SERVICE_PORTAL_PARTNEROS_TOKEN=",
    "PORTAL_CUSTOMER_API_TOKEN=",
    "Bearer ",
    "raw response body",
    "backend/storage",
    "local_data",
    "internal_cost",
    "estimated_margin",
    "pricing_breakdown_json",
    "supplier_private",
    "storage_key",
    "secret_key",
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


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _missing(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def _gap_records() -> list[Path]:
    if not RECORDS_ROOT.exists():
        return []
    return sorted(RECORDS_ROOT.glob("d8_strict_staging_gaps_*.md"))


def _status_issues(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    header: list[str] | None = None
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        normalized = [cell.lower() for cell in cells]
        if {"check", "recommended action", "owner", "status"}.issubset(set(normalized)):
            header = normalized
            continue
        if header is None or all(set(cell) <= {"-"} for cell in normalized):
            continue
        if "status" not in header:
            continue
        status_index = header.index("status")
        if status_index >= len(cells):
            issues.append(f"{path.name}:{line_no}:missing status")
            continue
        status = cells[status_index].strip("` ").lower()
        if status not in ALLOWED_GAP_STATUSES:
            issues.append(f"{path.name}:{line_no}:invalid status {status or '<empty>'}")
    return issues


def _gap_issues(records: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in records:
        if not GAP_REGISTER_PATTERN.match(path.name):
            issues.append(f"{path.name}:noncanonical name")
        text = _text(path)
        missing = _missing(text, REQUIRED_GAP_MARKERS)
        if missing:
            issues.append(f"{path.name}:missing {','.join(missing)}")
        issues.extend(_status_issues(path, text))
        lowered = text.lower()
        for marker in FORBIDDEN_MARKERS:
            if marker.lower() in lowered:
                issues.append(f"{path.name}:{marker}")
        issues.extend(redaction_issues(path, text, include_common_markers=False))
    return issues


def main() -> int:
    checks = [
        Check("D8 staging gap triage doc exists"),
        Check("D8 staging gap triage doc is actionable"),
        Check("existing D8 gap registers are triage-ready"),
    ]

    text = _text(DOC)
    checks[0].pass_("docs/phase3/d8_staging_gap_triage.md") if text else checks[0].fail(str(DOC))

    missing = _missing(text, REQUIRED_DOC_MARKERS)
    checks[1].pass_(f"{len(REQUIRED_DOC_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    gap_records = _gap_records()
    issues = _gap_issues(gap_records)
    checks[2].pass_(f"{len(gap_records)} gap register(s)") if not issues else checks[2].fail(", ".join(issues[:8]))

    print("D8 Staging Gap Triage Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
