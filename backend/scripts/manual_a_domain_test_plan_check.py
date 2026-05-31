"""Validate the manual A-domain UAT plan."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "manual_a_domain_test_plan.md"
TEMPLATE_DOC = REPO_ROOT / "docs" / "templates" / "manual_test_record_template.md"
IMPORT_TEMPLATE_DOC = REPO_ROOT / "docs" / "templates" / "lead_import_template.md"

REQUIRED_MARKERS = (
    "Manual A-Domain Test Plan",
    "current on 2026-05-30",
    "READY_FOR_STAGING_HANDOFF",
    "http://127.0.0.1:8014",
    "Manual Test Record Template",
    "/lead-intelligence",
    "PUBLIC_ENRICHMENT_ENABLED=false",
    "lift_system_signal",
    "general_office_furniture_only",
    "project_based_furniture",
    "oem_odm_fit",
    "segment_rule",
    "scoring_rule",
    "enrichment_evidence",
    "safety_boundary",
    "must not",
    "python scripts/manual_a_domain_test_plan_check.py",
    "python scripts/lead_intelligence_docs_check.py",
    "python scripts/project_execution_chain_gate_check.py",
)
REQUIRED_TEMPLATE_MARKERS = (
    "Manual Test Record Template",
    "Allowed Issue Type values",
    "safety_boundary",
    "redacted UAT summaries only",
    "python scripts/manual_a_domain_test_plan_check.py",
)
REQUIRED_IMPORT_TEMPLATE_MARKERS = (
    "Lead Import Template Guide",
    "lead_import_template.csv",
    "Company -> Contact -> Lead -> Score / Segments -> Interaction -> Next Action",
    "No LinkedIn automation",
    "oem_odm_fit",
    "python scripts/manual_a_domain_test_plan_check.py",
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
    "D6 Productization | **Not started**",
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


def _text() -> str:
    try:
        return DOC.read_text(encoding="utf-8")
    except OSError:
        return ""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def main() -> int:
    checks = [
        Check("manual A-domain test plan exists"),
        Check("manual A-domain test plan matches current UAT contract"),
        Check("manual A-domain templates match current UAT contract"),
        Check("manual A-domain test plan avoids stale or mojibake markers"),
        Check("manual A-domain test plan is redacted"),
    ]

    text = _text()
    template = _read(TEMPLATE_DOC)
    import_template = _read(IMPORT_TEMPLATE_DOC)
    checks[0].pass_("docs/manual_a_domain_test_plan.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    template_missing = [marker for marker in REQUIRED_TEMPLATE_MARKERS if marker not in template]
    template_missing.extend(marker for marker in REQUIRED_IMPORT_TEMPLATE_MARKERS if marker not in import_template)
    if template and import_template and not template_missing:
        checks[2].pass_(f"{len(REQUIRED_TEMPLATE_MARKERS) + len(REQUIRED_IMPORT_TEMPLATE_MARKERS)} markers")
    else:
        missing_detail = template_missing or [str(path) for path, content in ((TEMPLATE_DOC, template), (IMPORT_TEMPLATE_DOC, import_template)) if not content]
        checks[2].fail(", ".join(missing_detail))

    combined = "\n".join((text, template, import_template))
    stale = [marker for marker in FORBIDDEN_MARKERS[:9] if marker in combined]
    checks[3].pass_("no stale stage or mojibake markers") if not stale else checks[3].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[9:] if marker.lower() in combined.lower()]
    redaction.extend(redaction_issues(DOC, text, include_common_markers=False))
    redaction.extend(redaction_issues(TEMPLATE_DOC, template, include_common_markers=False))
    redaction.extend(redaction_issues(IMPORT_TEMPLATE_DOC, import_template, include_common_markers=False))
    checks[4].pass_("no secret-like markers") if not redaction else checks[4].fail(", ".join(redaction[:8]))

    print("Manual A-Domain Test Plan Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
