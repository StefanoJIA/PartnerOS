"""Validate D8 staging evidence records before commit or handoff."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
RECORDS_ROOT = REPO_ROOT / "docs" / "records"

EVIDENCE_PATTERN = re.compile(r"^d8_strict_staging_evidence_\d{8}\.json$")
STAGING_RECORD_PATTERN = re.compile(
    r"^d8_(?:strict_staging_(?:evidence|gaps)_\d{8}|staging_operator_handoff(?:_\d{8})?)\.(?:json|md)$"
)
FORBIDDEN_RECORD_MARKERS = (
    "backend/storage",
    "local_data",
    "internal_cost",
    "estimated_margin",
    "pricing_breakdown_json",
    "cost_snapshot_json",
    "supplier_private",
    "supplier_reference",
    "storage_key",
    "portal_customer_api_token",
    "secret_key",
    "password_hash",
    "database_url",
)
TOKEN_ASSIGNMENT_PATTERN = re.compile(
    r"(SERVICE_PORTAL_PARTNEROS_TOKEN|PORTAL_CUSTOMER_API_TOKEN):?\s*=\s*['\"]?([^'\"\s]+)",
    re.IGNORECASE,
)
ALLOWED_TOKEN_PLACEHOLDERS = {
    "<portal-server-token>",
    "<redacted>",
    "***",
    "REDACTED",
}


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


def _staging_records() -> list[Path]:
    if not RECORDS_ROOT.exists():
        return []
    return sorted(path for path in RECORDS_ROOT.iterdir() if path.is_file() and path.name.startswith("d8_"))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _token_assignment_issues(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = TOKEN_ASSIGNMENT_PATTERN.search(line)
        if not match:
            continue
        value = match.group(2).strip()
        if value not in ALLOWED_TOKEN_PLACEHOLDERS and not (value.startswith("<") and value.endswith(">")):
            issues.append(f"{path.name}:{line_no}")
    return issues


def _sensitive_marker_issues(records: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in records:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"{path.name}:unreadable")
            continue
        lowered = text.lower()
        for marker in FORBIDDEN_RECORD_MARKERS:
            if marker in lowered:
                issues.append(f"{path.name}:{marker}")
        issues.extend(_token_assignment_issues(path, text))
    return issues


def _naming_issues(records: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in records:
        if not STAGING_RECORD_PATTERN.match(path.name):
            issues.append(path.name)
    return issues


def _evidence_issues(records: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in records:
        if not EVIDENCE_PATTERN.match(path.name):
            continue
        data = _read_json(path)
        if not data:
            issues.append(f"{path.name}:invalid json")
            continue
        result = str(data.get("result") or "").upper()
        if result not in {"PASS", "FAIL"}:
            issues.append(f"{path.name}:result")
        if not isinstance(data.get("checks"), list):
            issues.append(f"{path.name}:checks")
        safety = data.get("safety")
        if not isinstance(safety, dict):
            issues.append(f"{path.name}:safety")
            continue
        if safety.get("token_redacted") is not True:
            issues.append(f"{path.name}:token_redacted")
        if safety.get("response_bodies_stored") is not False:
            issues.append(f"{path.name}:response_bodies_stored")
        if result == "FAIL":
            gap_name = path.name.replace("evidence", "gaps").replace(".json", ".md")
            if not (RECORDS_ROOT / gap_name).exists():
                issues.append(f"{path.name}:missing {gap_name}")
    return issues


def main() -> int:
    checks = [
        Check("docs/records exists"),
        Check("D8 staging record names are canonical"),
        Check("D8 staging records are redacted"),
        Check("strict staging evidence schema"),
    ]

    if RECORDS_ROOT.exists() and RECORDS_ROOT.is_dir():
        checks[0].pass_(str(RECORDS_ROOT.relative_to(REPO_ROOT)))
    else:
        checks[0].fail("missing docs/records")

    records = _staging_records()
    naming = _naming_issues(records)
    checks[1].pass_(f"{len(records)} D8 records") if not naming else checks[1].fail(", ".join(naming))

    sensitive = _sensitive_marker_issues(records)
    checks[2].pass_("no token assignments or internal markers") if not sensitive else checks[2].fail(
        ", ".join(sensitive[:8])
    )

    evidence = _evidence_issues(records)
    checks[3].pass_("all evidence JSON valid") if not evidence else checks[3].fail(", ".join(evidence[:8]))

    print("D8 Staging Records Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
