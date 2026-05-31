"""D8.0 build and staging integration readiness checklist validator."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "phase3" / "d8_0_real_staging_integration_build_closure.md"
README = REPO_ROOT / "README.md"
OPERATOR_GUIDE = REPO_ROOT / "docs" / "operator_guide.md"

REQUIRED_DOC_MARKERS = (
    "READY_FOR_STAGING_HANDOFF",
    "npm run build",
    "docker compose up -d db",
    "alembic upgrade head",
    "PORTAL_CUSTOMER_API_ENABLED",
    "PORTAL_CUSTOMER_API_TOKEN",
    "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
    "PUBLIC_BASE_URL",
    "python scripts/d7_8_portal_live_integration_check.py",
    "python scripts/d8_3_service_portal_staging_check.py",
    "Do not deploy or modify `service.intelli-opus.com`",
    "Do not create or refresh proof records",
    "WAITING_FOR_REAL_STAGING_EVIDENCE",
    "Do not enter D9",
)

REQUIRED_README_MARKERS = (
    "D8.0 Real Staging Integration & Build Closure",
    "python scripts/d8_0_staging_build_readiness_check.py",
    "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
)

REQUIRED_OPERATOR_MARKERS = (
    "D8.0 Real Staging Integration & Build Closure",
    "READY_FOR_STAGING_HANDOFF",
    "PORTAL_CUSTOMER_API_ENABLED",
    "PORTAL_CUSTOMER_API_TOKEN",
    "PORTAL_CUSTOMER_ALLOWED_ORIGINS",
    "PUBLIC_BASE_URL",
    "Do not create or refresh proof records",
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
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _marker_check(label: str, text: str, markers: tuple[str, ...]) -> Check:
    check = Check(label)
    missing = [marker for marker in markers if marker not in text]
    if missing:
        check.fail(", ".join(missing))
    else:
        check.pass_(f"{len(markers)} markers")
    return check


def main() -> int:
    doc_text = _text(DOC)
    readme_text = _text(README)
    operator_text = _text(OPERATOR_GUIDE)

    checks = [
        Check("D8.0 checklist doc exists"),
        _marker_check("D8.0 checklist content", doc_text, REQUIRED_DOC_MARKERS),
        _marker_check("README D8.0 pointers", readme_text, REQUIRED_README_MARKERS),
        _marker_check("operator guide D8.0 pointers", operator_text, REQUIRED_OPERATOR_MARKERS),
    ]

    checks[0].pass_(str(DOC.relative_to(REPO_ROOT))) if DOC.exists() else checks[0].fail(
        str(DOC.relative_to(REPO_ROOT))
    )

    print("D8.0 Staging Build Readiness Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
