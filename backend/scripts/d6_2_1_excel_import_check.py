"""D6.2.1 Excel pricing import alignment check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
WORKBOOK = REPO_ROOT / "local_data" / "报价模型与格式.xlsx"


def _run_import_dry_run() -> tuple[int, str]:
    import importlib.util

    script = BACKEND_ROOT / "scripts" / "import_pricing_excel.py"
    spec = importlib.util.spec_from_file_location("import_pricing_excel", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.run(WORKBOOK, apply=False, overwrite=False)
    return rc, buf.getvalue()


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    overall_pass = True
    overall_warn = False

    ignore = subprocess.run(
        ["git", "check-ignore", str(WORKBOOK)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    ignored = ignore.returncode == 0
    checks.append(("workbook ignored", ignored, "git check-ignore"))
    if not ignored:
        overall_pass = False

    if not WORKBOOK.is_file():
        checks.append(("workbook readable", False, "file missing"))
        checks.append(("sheets detected", False, "skipped"))
        checks.append(("headers detected", False, "skipped"))
        checks.append(("candidate rows found", False, "skipped"))
        print("D6.2.1 Excel Import Check")
        for name, ok, note in checks:
            status = "PASS" if ok else "WARN"
            print(f"[{status}] {name} ({note})")
        print("Result: WARN")
        print("Place workbook at local_data/报价模型与格式.xlsx")
        return 0

    rc, out = _run_import_dry_run()
    readable = rc == 0
    checks.append(("workbook readable", readable, f"exit={rc}"))

    sheets_ok = "Available sheets:" in out and "成本" in out or "cost" in out.lower()
    checks.append(("sheets detected", sheets_ok, "sheet list"))

    headers_ok = "Header row:" in out and "Matched columns:" in out
    checks.append(("headers detected", headers_ok, "header debug"))

    candidates_ok = False
    for line in out.splitlines():
        if "total candidate rows:" in line:
            try:
                n = int(line.split(":")[-1].strip())
                candidates_ok = n > 0
            except ValueError:
                candidates_ok = False
            break
    checks.append(("candidate rows found", candidates_ok, "dry-run summary"))

    if not all(ok for _, ok, _ in checks):
        overall_pass = False

    print("D6.2.1 Excel Import Check")
    for name, ok, note in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
    result = "PASS" if overall_pass else "FAIL"
    print(f"Result: {result}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
