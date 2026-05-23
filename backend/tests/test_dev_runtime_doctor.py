"""Tests for D5.11 dev runtime doctor."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = BACKEND_ROOT / "scripts"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


doctor = _load("dev_runtime_doctor")


def _item(level: str):
    it = doctor.RuntimeItem("x")
    if level == "PASS":
        it.pass_()
    else:
        it.fail("boom")
    return it


def test_run_passes_with_mocked_checks(monkeypatch):
    monkeypatch.setattr(doctor, "_check_database", lambda: _item("PASS"))
    monkeypatch.setattr(doctor, "_check_migration", lambda: _item("PASS"))
    monkeypatch.setattr(doctor, "_check_port_status", lambda: _item("PASS"))
    monkeypatch.setattr(doctor, "_check_backend_health", lambda: _item("PASS"))
    monkeypatch.setattr(doctor, "_check_env_warnings", lambda: [])
    monkeypatch.setattr(doctor, "_check_readiness", lambda c, b: [_item("PASS")])
    monkeypatch.setattr(doctor, "_check_authed_endpoint", lambda c, b, p, l: _item("PASS"))
    assert doctor.run(verbose=False) == 0


def test_run_critical_fail_exit_2(monkeypatch):
    monkeypatch.setattr(doctor, "_check_database", lambda: _item("FAIL"))
    monkeypatch.setattr(doctor, "_check_migration", lambda: _item("PASS"))
    monkeypatch.setattr(doctor, "_check_port_status", lambda: _item("PASS"))
    monkeypatch.setattr(doctor, "_check_backend_health", lambda: _item("PASS"))
    monkeypatch.setattr(doctor, "_check_env_warnings", lambda: [])
    monkeypatch.setattr(doctor, "_check_readiness", lambda c, b: [_item("PASS")])
    monkeypatch.setattr(doctor, "_check_authed_endpoint", lambda c, b, p, l: _item("PASS"))
    assert doctor.run(verbose=False) == 2


def test_readiness_warns_optional_off():
    client = MagicMock()
    with patch.object(doctor, "get_json", return_value=(200, {"data": {"database_ready": True, "redis_ready": False, "worker_ready": False}}, None)):
        items = doctor._check_readiness(client, "http://127.0.0.1:8010")
    assert items[0].level == "PASS"
    assert any(i.label == "redis optional" and i.level == "WARN" for i in items)
