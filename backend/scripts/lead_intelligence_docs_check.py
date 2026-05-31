"""Validate Lead Intelligence planning docs."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = (
    REPO_ROOT / "docs" / "lead_intelligence_mvp.md",
    REPO_ROOT / "docs" / "public_source_enrichment_mvp.md",
    REPO_ROOT / "docs" / "lead_intelligence_scoring_notes.md",
)

REQUIRED_MARKERS = (
    "Lead Intelligence MVP",
    "Public-Source Enrichment MVP",
    "Lead Intelligence Scoring Notes",
    "current on 2026-05-30",
    "READY_FOR_STAGING_HANDOFF",
    "backend/app/services/a_domain/intelligence_score.py",
    "/lead-intelligence",
    "lift_system_signal",
    "general_office_furniture_only",
    "oem_odm_fit",
    "project_based_furniture",
    "PUBLIC_ENRICHMENT_ENABLED=false",
    "evidence-first",
    "human-in-the-loop",
    "must not silently overwrite formal CRM facts",
    "must not trigger outreach or external notifications",
    "AI-assisted output remains advisory and human-reviewed",
    "python scripts/lead_intelligence_docs_check.py",
    "python scripts/project_execution_chain_gate_check.py",
)
FORBIDDEN_MARKERS = (
    "娑?",
    "閿?",
    "閳?",
    "鎼?",
    "锛",
    "鈥",
    "D0-D5.2",
    "Phase 1",
    "No CRM v1",
    "No runtime change",
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


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> int:
    checks = [
        Check("Lead Intelligence docs exist"),
        Check("Lead Intelligence docs match current operating contract"),
        Check("Lead Intelligence docs avoid stale or mojibake markers"),
        Check("Lead Intelligence docs are redacted"),
    ]

    texts = {path: _read(path) for path in DOCS}
    missing_files = [str(path) for path, text in texts.items() if not text]
    checks[0].pass_(f"{len(DOCS)} docs") if not missing_files else checks[0].fail(", ".join(missing_files))

    combined = "\n".join(texts.values())
    missing = [marker for marker in REQUIRED_MARKERS if marker not in combined]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:10] if marker in combined]
    checks[2].pass_("no stale pilot or mojibake markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[10:] if marker.lower() in combined.lower()]
    for path, text in texts.items():
        redaction.extend(redaction_issues(path, text, include_common_markers=False))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Lead Intelligence Docs Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
