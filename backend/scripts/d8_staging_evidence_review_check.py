"""Review saved D8 strict staging evidence for handoff decisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
RECORDS_ROOT = REPO_ROOT / "docs" / "records"
DOC = REPO_ROOT / "docs" / "phase3" / "d8_staging_evidence_review.md"

REQUIRED_DOC_MARKERS = (
    "D8 Staging Evidence Review",
    "WAITING_FOR_STAGING_EVIDENCE",
    "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "STAGING_GAPS_REQUIRE_TRIAGE",
    "d8_strict_staging_evidence_YYYYMMDD.json",
    "d8_strict_staging_gaps_YYYYMMDD.md",
    "python scripts/d8_staging_evidence_review_check.py",
    "python scripts/d8_staging_records_check.py",
    "python scripts/d8_readiness_audit.py",
    "No `.env`",
    "No email, webhook, carrier API",
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


def _doc_text() -> str:
    try:
        return DOC.read_text(encoding="utf-8")
    except OSError:
        return ""


def _evidence_files() -> list[Path]:
    if not RECORDS_ROOT.exists():
        return []
    return sorted(
        RECORDS_ROOT.glob("d8_strict_staging_evidence_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _evidence_state() -> tuple[str, str]:
    files = _evidence_files()
    if not files:
        return "WAITING_FOR_STAGING_EVIDENCE", "no strict staging evidence JSON found"

    latest = files[0]
    data = _read_json(latest)
    result = str(data.get("result") or "").upper()
    checks = data.get("checks")
    safety = data.get("safety")
    if result not in {"PASS", "FAIL"} or not isinstance(checks, list) or not isinstance(safety, dict):
        return "EVIDENCE_UNREADABLE", latest.name
    if safety.get("token_redacted") is not True or safety.get("response_bodies_stored") is not False:
        return "EVIDENCE_UNSAFE", latest.name

    if result == "PASS":
        return "READY_FOR_PRODUCTION_COORDINATION_REVIEW", latest.name

    gap_name = latest.name.replace("evidence", "gaps").replace(".json", ".md")
    gap_path = RECORDS_ROOT / gap_name
    if gap_path.exists():
        return "STAGING_GAPS_REQUIRE_TRIAGE", f"{latest.name}; gap register {gap_name}"
    return "STAGING_GAPS_REQUIRE_TRIAGE", f"{latest.name}; gap register missing"


def main() -> int:
    checks = [
        Check("evidence review doc exists"),
        Check("evidence review doc is actionable"),
        Check("evidence review doc is redacted"),
        Check("saved strict staging evidence review"),
    ]

    text = _doc_text()
    checks[0].pass_("docs/phase3/d8_staging_evidence_review.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_DOC_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_DOC_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    forbidden = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    forbidden.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[2].pass_("no secret-like markers") if not forbidden else checks[2].fail(", ".join(forbidden))

    state, detail = _evidence_state()
    if state in {
        "WAITING_FOR_STAGING_EVIDENCE",
        "READY_FOR_PRODUCTION_COORDINATION_REVIEW",
        "STAGING_GAPS_REQUIRE_TRIAGE",
    }:
        checks[3].pass_(f"{state}: {detail}")
    else:
        checks[3].fail(f"{state}: {detail}")

    print("D8 Staging Evidence Review Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Review State: {state}")
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
