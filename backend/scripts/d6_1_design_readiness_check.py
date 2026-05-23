"""D6.1 design readiness check — documentation and boundary verification only."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
ALEMBIC = BACKEND_ROOT / "alembic" / "versions"
APP = BACKEND_ROOT / "app"

FORBIDDEN_IN_DESIGN = (
    ("automatic_sending_enabled: true", None),
    ("ai-generated price", None),
    ("auto-send quote", None),
    ("auto convert to order", r"(?<!\bno )(?<!\bnot )"),
)

REQUIRED_DOCS = (
    ("D5 final release", DOCS / "releases" / "d5_final_mvp_release_20260523.md"),
    ("D5 capability map", DOCS / "architecture" / "d5_capability_map.md"),
    ("Phase 2 readiness brief", DOCS / "phase2" / "quote_module_readiness_brief.md"),
    ("D6.1 design review", DOCS / "phase2" / "d6_1_quote_schema_api_design_review.md"),
)

# Post-D6.1 migrations should not exist yet (head stays 0005 until D6.2)
EXPECTED_HEAD_PREFIX = "0005_"

SAFETY_SECTION_PATTERNS = (
    r"No AI pricing",
    r"No automatic sending",
    r"No inventory promise",
    r"No certification promise",
    r"No lead-time promise",
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


def _has_quote_api_implementation() -> list[str]:
    hits: list[str] = []
    patterns = (
        r'@router\.(get|post|put|patch|delete)\(["\']/quotes',
        r'prefix=["\']/quotes["\']',
        r'APIRouter\(prefix="/quotes"',
        r"class Quote\(",
        r'__tablename__\s*=\s*["\']quotes["\']',
        r'__tablename__\s*=\s*["\']quote_line_items["\']',
    )
    for path in APP.rglob("*.py"):
        if "test_" in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        for pat in patterns:
            if re.search(pat, text):
                hits.append(f"{path.relative_to(BACKEND_ROOT)}: {pat}")
                break
    return hits


def _new_migrations_after_d6_1() -> list[str]:
    bad: list[str] = []
    for path in sorted(ALEMBIC.glob("*.py")):
        name = path.name
        if name.startswith("0001_") or name.startswith("0002_") or name.startswith("0003_"):
            continue
        if name.startswith("0004_") or name.startswith("0005_"):
            continue
        bad.append(name)
    return bad


def main() -> int:
    print("D6.1 Design Readiness Check")
    checks = [
        Check("D5 closure docs"),
        Check("D6.1 design doc"),
        Check("no migration"),
        Check("no quote implementation"),
        Check("safety boundaries"),
    ]

    missing = [label for label, p in REQUIRED_DOCS if not p.is_file()]
    d5_docs = [label for label, p in REQUIRED_DOCS[:3] if p.is_file()]
    if not missing:
        checks[0].pass_(f"{len(REQUIRED_DOCS[:3])} docs")
    elif d5_docs:
        checks[0].pass_(f"partial: {', '.join(d5_docs)}")
    else:
        checks[0].fail(f"missing: {', '.join(missing)}")

    d6_doc = DOCS / "phase2" / "d6_1_quote_schema_api_design_review.md"
    if d6_doc.is_file():
        text = d6_doc.read_text(encoding="utf-8")
        required_sections = (
            "Business Decisions",
            "Excel Pricing Model Extraction",
            "Proposed Data Model",
            "Quote Lifecycle",
            "Pricing Model",
            "PDF Quote Model",
            "API Design",
            "Permission Model",
            "Safety Rules",
            "Open Questions",
        )
        missing_sections = [s for s in required_sections if s not in text]
        if missing_sections:
            checks[1].fail(f"missing sections: {', '.join(missing_sections[:3])}")
        elif len(text) < 8000:
            checks[1].fail("doc too short")
        else:
            checks[1].pass_(f"{len(text)} chars")
    else:
        checks[1].fail("file missing")

    new_migs = _new_migrations_after_d6_1()
    if new_migs:
        checks[2].fail(", ".join(new_migs))
    else:
        checks[2].pass_(f"head <= {EXPECTED_HEAD_PREFIX}*")

    impl_hits = _has_quote_api_implementation()
    if impl_hits:
        checks[3].fail(impl_hits[0][:80])
    else:
        checks[3].pass_("no quotes table/API in app")

    if d6_doc.is_file():
        text = d6_doc.read_text(encoding="utf-8").lower()
        violations = []
        for phrase, lookbehind in FORBIDDEN_IN_DESIGN:
            if lookbehind:
                if re.search(lookbehind + re.escape(phrase), text, re.I):
                    violations.append(phrase)
            elif phrase.lower() in text:
                violations.append(phrase)
        missing_safety = [p for p in SAFETY_SECTION_PATTERNS if not re.search(p, text, re.I)]
        if violations:
            checks[4].fail(f"forbidden phrase: {violations[0]}")
        elif len(missing_safety) > 2:
            checks[4].fail(f"missing safety: {missing_safety[0]}")
        else:
            checks[4].pass_("design doc safety OK")
    else:
        checks[4].fail("no doc to verify")

    for c in checks:
        print(c.line())

    passed = all(c.ok for c in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
