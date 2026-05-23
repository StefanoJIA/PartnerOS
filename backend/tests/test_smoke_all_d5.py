"""Tests for D5.11 smoke_all_d5 runner."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _load(name: str):
    path = BACKEND_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


smoke = _load("smoke_all_d5")


def test_run_quiet_pass():
    r = smoke._run_quiet("demo", lambda: 0)
    assert r.level == "PASS"


def test_run_quiet_fail():
    r = smoke._run_quiet("demo", lambda: 1)
    assert r.level == "FAIL"


def test_run_quiet_warn_ok():
    def _fn():
        print("[WARN] PUBLIC_BASE_URL not set")
        return 0

    r = smoke._run_quiet("config", _fn, warn_ok=True)
    assert r.level == "WARN"


def test_smoke_all_passes_when_all_steps_ok(monkeypatch):
    ok = smoke.SmokeResult("x")
    ok.pass_()
    monkeypatch.setattr(smoke, "_run_quiet", lambda *a, **k: ok)
    assert smoke.run(verbose=False) == 0


def test_smoke_all_fails_on_step_fail(monkeypatch):
    bad = smoke.SmokeResult("x")
    bad.fail("nope")
    monkeypatch.setattr(smoke, "_run_quiet", lambda *a, **k: bad)
    assert smoke.run(verbose=False) == 1
