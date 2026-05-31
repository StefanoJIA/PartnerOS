"""Validate D8 staging evidence records before commit or handoff."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
RECORDS_ROOT = REPO_ROOT / "docs" / "records"
POLICY_DOC = REPO_ROOT / "docs" / "phase3" / "d8_staging_records_policy.md"

EVIDENCE_PATTERN = re.compile(r"^d8_strict_staging_evidence_\d{8}\.json$")
STAGING_RECORD_PATTERN = re.compile(
    r"^d8_(?:strict_staging_(?:evidence|gaps)_\d{8}|staging_operator_handoff_\d{8}|staging_access_request_\d{8}|production_go_no_go_\d{8})\.(?:json|md)$"
)
CURRENT_HANDOFF_PATTERN = re.compile(r"^d8_staging_operator_handoff_\d{8}\.md$")
CURRENT_ACCESS_REQUEST_PATTERN = re.compile(r"^d8_staging_access_request_\d{8}\.md$")
BACKEND_URL_STATUS = re.compile(r"^\s*BACKEND_BASE_URL\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)
PORTAL_TOKEN_STATUS = re.compile(r"^\s*SERVICE_PORTAL_PARTNEROS_TOKEN\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)
EXTRA_FORBIDDEN_RECORD_MARKERS = ("supplier_reference", "partneros-staging.example.com")
REQUIRED_POLICY_MARKERS = (
    "D8 Staging Records Policy",
    "d8_staging_operator_handoff_YYYYMMDD.md",
    "d8_staging_access_request_YYYYMMDD.md",
    "d8_strict_staging_evidence_YYYYMMDD.json",
    "d8_strict_staging_gaps_YYYYMMDD.md",
    "current operator handoff and staging access request records",
    "remote backend host is stored as `https://<redacted-backend>`",
    "Strict staging evidence and gap records are not required before the real staging run",
    "WAITING_FOR_STAGING_EVIDENCE",
    "Do not paste real `SERVICE_PORTAL_PARTNEROS_TOKEN`",
    "Do not store raw API response bodies",
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


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _policy_text() -> str:
    try:
        return POLICY_DOC.read_text(encoding="utf-8")
    except OSError:
        return ""


def _policy_marker_issues(text: str) -> list[str]:
    return [marker for marker in REQUIRED_POLICY_MARKERS if marker not in text]


def _sensitive_marker_issues(records: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in records:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"{path.name}:unreadable")
            continue
        issues.extend(redaction_issues(path, text, EXTRA_FORBIDDEN_RECORD_MARKERS))
        for line_no, line in enumerate(text.splitlines(), start=1):
            backend_url = BACKEND_URL_STATUS.match(line)
            if backend_url and backend_url.group("value").strip() != "provided privately":
                issues.append(f"{path.name}:{line_no}:BACKEND_BASE_URL:<non-private-status>")
            portal_token = PORTAL_TOKEN_STATUS.match(line)
            if portal_token and portal_token.group("value").strip() != "provided privately":
                issues.append(f"{path.name}:{line_no}:SERVICE_PORTAL_PARTNEROS_TOKEN:<non-private-status>")
    return issues


def _naming_issues(records: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in records:
        if not STAGING_RECORD_PATTERN.match(path.name):
            issues.append(path.name)
    return issues


def _required_current_record_issues(records: list[Path]) -> list[str]:
    names = [path.name for path in records]
    issues: list[str] = []
    if not any(CURRENT_HANDOFF_PATTERN.match(name) for name in names):
        issues.append("d8_staging_operator_handoff_YYYYMMDD.md")
    if not any(CURRENT_ACCESS_REQUEST_PATTERN.match(name) for name in names):
        issues.append("d8_staging_access_request_YYYYMMDD.md")
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
        backend_base_url = str(data.get("backend_base_url") or "")
        if backend_base_url.startswith(("http://", "https://")):
            host = (urlparse(backend_base_url).hostname or "").lower()
            if host not in {"localhost", "127.0.0.1", "::1", "<redacted-backend>"}:
                issues.append(f"{path.name}:backend_base_url_redaction")
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
        Check("D8 staging records policy exists"),
        Check("D8 staging records policy matches current gate"),
        Check("docs/records exists"),
        Check("D8 staging record names are canonical"),
        Check("current D8 handoff records exist"),
        Check("D8 staging records are redacted"),
        Check("strict staging evidence schema"),
    ]

    policy_text = _policy_text()
    checks[0].pass_("docs/phase3/d8_staging_records_policy.md") if policy_text else checks[0].fail(
        str(POLICY_DOC)
    )

    policy_missing = _policy_marker_issues(policy_text)
    checks[1].pass_(f"{len(REQUIRED_POLICY_MARKERS)} markers") if not policy_missing else checks[1].fail(
        ", ".join(policy_missing)
    )

    if RECORDS_ROOT.exists() and RECORDS_ROOT.is_dir():
        checks[2].pass_(_display_path(RECORDS_ROOT))
    else:
        checks[2].fail("missing docs/records")

    records = _staging_records()
    naming = _naming_issues(records)
    checks[3].pass_(f"{len(records)} D8 records") if not naming else checks[3].fail(", ".join(naming))

    required_current = _required_current_record_issues(records)
    checks[4].pass_("handoff and access request records") if not required_current else checks[4].fail(
        ", ".join(required_current)
    )

    sensitive = _sensitive_marker_issues(records)
    checks[5].pass_("no token assignments or internal markers") if not sensitive else checks[5].fail(
        ", ".join(sensitive[:8])
    )

    evidence = _evidence_issues(records)
    checks[6].pass_("all evidence JSON valid") if not evidence else checks[6].fail(", ".join(evidence[:8]))

    print("D8 Staging Records Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
