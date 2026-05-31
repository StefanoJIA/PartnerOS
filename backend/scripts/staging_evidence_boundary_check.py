"""Ensure staging validation docs also carry the real-evidence wait boundary."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "docs",
)
REQUIRED_PAIR = "WAITING_FOR_REAL_STAGING_EVIDENCE"
STAGING_MARKER = "STAGING_VALIDATED"


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


def _markdown_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.is_file():
            files.append(root)
            continue
        if not root.is_dir():
            continue
        for path in root.rglob("*.md"):
            try:
                relative = path.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                relative = path.as_posix()
            if relative.startswith("docs/records/"):
                continue
            files.append(path)
    return sorted(files)


def _display(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def _issues() -> list[str]:
    issues: list[str] = []
    for path in _markdown_files():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"{_display(path)}:unreadable")
            continue
        if STAGING_MARKER in text and REQUIRED_PAIR not in text:
            issues.append(_display(path))
    return issues


def main() -> int:
    checks = [
        Check("markdown staging boundary scan"),
        Check("STAGING_VALIDATED docs mention real-evidence wait state"),
    ]

    files = _markdown_files()
    checks[0].pass_(f"{len(files)} markdown files")

    issues = _issues()
    checks[1].pass_(REQUIRED_PAIR) if not issues else checks[1].fail(", ".join(issues[:12]))

    print("Staging Evidence Boundary Check")
    for check in checks:
        print(check.line())
    passed = all(check.ok for check in checks)
    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
