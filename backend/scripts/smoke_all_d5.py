"""D5.11 — one-shot smoke runner for D5.x MVP checks."""

from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Callable

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.backend_url import log_backend_base_url


class SmokeResult:
    def __init__(self, label: str) -> None:
        self.label = label
        self.level = "PASS"
        self.detail = ""

    def pass_(self, detail: str = "") -> None:
        self.level = "PASS"
        self.detail = detail

    def warn(self, detail: str = "") -> None:
        self.level = "WARN"
        self.detail = detail

    def fail(self, detail: str = "") -> None:
        self.level = "FAIL"
        self.detail = detail

    @property
    def ok(self) -> bool:
        return self.level != "FAIL"

    def line(self) -> str:
        suffix = f" ({self.detail})" if self.detail else ""
        return f"[{self.level}] {self.label}{suffix}"


def _load_script(module_name: str):
    path = BACKEND_ROOT / "scripts" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _run_quiet(label: str, fn: Callable[[], int], *, warn_ok: bool = False) -> SmokeResult:
    res = SmokeResult(label)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = fn()
    except Exception as e:  # noqa: BLE001
        res.fail(str(e)[:120])
        return res

    output = buf.getvalue()
    if code == 0:
        if warn_ok and "WARN" in output:
            res.warn("completed with warnings")
        else:
            res.pass_()
    else:
        lines = [ln.strip() for ln in output.strip().splitlines() if ln.strip()]
        hint = lines[-1][:100] if lines else f"exit {code}"
        res.fail(hint)
    return res


def run(*, verbose: bool = True) -> int:
    if verbose:
        log_backend_base_url()
        print("D5 Smoke All")

    check_database_config = _load_script("check_database_config")
    check_backend_runtime = _load_script("check_backend_runtime")
    config_readiness_check = _load_script("config_readiness_check")
    smoke_demo_ready = _load_script("smoke_demo_ready")
    pilot_workflow_check = _load_script("pilot_workflow_check")
    outreach_queue_check = _load_script("outreach_queue_check")
    real_lead_batch_check = _load_script("real_lead_batch_check")
    follow_up_queue_check = _load_script("follow_up_queue_check")
    daily_follow_up_summary = _load_script("daily_follow_up_summary")
    daily_ops_summary_check = _load_script("daily_ops_summary_check")
    daily_work_summary = _load_script("daily_work_summary")
    portal_readiness_check = _load_script("portal_readiness_check")
    portal_consumer_check = _load_script("portal_consumer_check")
    dev_runtime_doctor = _load_script("dev_runtime_doctor")

    steps: list[tuple[str, Callable[[], int], bool]] = [
        ("database", check_database_config.main, False),
        ("backend runtime", check_backend_runtime.run, False),
        ("config readiness", config_readiness_check.run, True),
        ("demo ready", lambda: smoke_demo_ready.run_checks(seed_demo=False), False),
        ("pilot workflow", pilot_workflow_check.run, False),
        ("outreach queue", outreach_queue_check.run, False),
        ("real lead batch", real_lead_batch_check.run, False),
        ("follow-up queue", follow_up_queue_check.main, False),
        ("daily follow-up summary", daily_follow_up_summary.main, False),
        ("daily ops summary", daily_ops_summary_check.main, False),
        ("daily work summary", daily_work_summary.main, False),
        ("portal readiness", portal_readiness_check.run, False),
        ("portal consumer", portal_consumer_check.run, False),
        ("dev runtime doctor", dev_runtime_doctor.run, True),
    ]

    results = [_run_quiet(label, fn, warn_ok=warn_ok) for label, fn, warn_ok in steps]

    if verbose:
        for r in results:
            print(r.line())

    fails = [r for r in results if not r.ok]
    warns = [r for r in results if r.level == "WARN"]

    if verbose:
        print()
        if fails:
            print("Result: FAIL")
        elif warns:
            print("Result: PASS with warnings")
        else:
            print("Result: PASS")

    return 1 if fails else 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
