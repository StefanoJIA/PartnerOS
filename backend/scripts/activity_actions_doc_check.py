"""Validate canonical activity action guidance."""

from __future__ import annotations

from pathlib import Path

try:
    from record_redaction import redaction_issues
except ModuleNotFoundError:
    from scripts.record_redaction import redaction_issues

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "activity_actions.md"

REQUIRED_MARKERS = (
    "Activity Actions",
    "current on 2026-05-30",
    "activity_logs.action",
    "lowercase snake_case",
    "shipment_plan_created",
    "shipment_plan_updated",
    "shipment_status_changed",
    "production_milestones_generated",
    "production_milestone_updated",
    "supplier_confirmation_added",
    "customer_confirmation_added",
    "order_resource_created",
    "quote_marked_sent",
    "Quote delivery events are manual records only",
    "must not call carriers",
    "must not send the quote",
    "partner-neutral",
    "python scripts/activity_actions_doc_check.py",
    "python scripts/project_execution_chain_gate_check.py",
    "python scripts/d8_staging_execution_pack_check.py",
    "python scripts/project_execution_acceptance_audit_check.py",
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


def main() -> int:
    checks = [
        Check("activity actions doc exists"),
        Check("activity actions doc contains current canonical actions"),
        Check("activity actions doc avoids stale or mojibake markers"),
        Check("activity actions doc is redacted"),
    ]

    text = _text()
    checks[0].pass_("docs/activity_actions.md") if text else checks[0].fail(str(DOC))

    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    checks[1].pass_(f"{len(REQUIRED_MARKERS)} markers") if not missing else checks[1].fail(", ".join(missing))

    stale = [marker for marker in FORBIDDEN_MARKERS[:8] if marker in text]
    checks[2].pass_("no stale stage or mojibake markers") if not stale else checks[2].fail(", ".join(stale))

    redaction = [marker for marker in FORBIDDEN_MARKERS[8:] if marker.lower() in text.lower()]
    redaction.extend(redaction_issues(DOC, text, include_common_markers=False))
    checks[3].pass_("no secret-like markers") if not redaction else checks[3].fail(", ".join(redaction[:8]))

    print("Activity Actions Doc Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
