from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_production_coordination_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_production_coordination_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_production_coordination_waits_for_staging_validation(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "_readiness_status", lambda: (True, "READY_FOR_STAGING"))

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "WAITING_FOR_STAGING_VALIDATION" in output
    assert "Result: PASS" in output


def test_production_coordination_ready_after_staging_validated(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "_readiness_status", lambda: (True, "STAGING_VALIDATED"))

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "READY_FOR_PRODUCTION_COORDINATION" in output
    assert "Result: PASS" in output


def test_production_coordination_fails_on_missing_plan_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "PLAN_DOC", tmp_path / "d8_production_coordination_plan.md")
    monkeypatch.setattr(module, "_readiness_status", lambda: (True, "STAGING_VALIDATED"))
    module.PLAN_DOC.write_text("STAGING_VALIDATED\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "production coordination safety markers" in output
    assert "Result: FAIL" in output
