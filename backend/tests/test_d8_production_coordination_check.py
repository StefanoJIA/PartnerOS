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
    monkeypatch.setattr(module, "_evidence_review_status", lambda: (True, "WAITING_FOR_STAGING_EVIDENCE"))

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "WAITING_FOR_STAGING_VALIDATION" in output
    assert "Result: PASS" in output


def test_production_coordination_ready_after_staging_validated(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "_readiness_status", lambda: (True, "STAGING_VALIDATED"))
    monkeypatch.setattr(
        module,
        "_evidence_review_status",
        lambda: (True, "READY_FOR_PRODUCTION_COORDINATION_REVIEW"),
    )

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "READY_FOR_PRODUCTION_COORDINATION" in output
    assert "Result: PASS" in output


def test_production_coordination_fails_on_missing_plan_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "PLAN_DOC", tmp_path / "d8_production_coordination_plan.md")
    monkeypatch.setattr(module, "_readiness_status", lambda: (True, "STAGING_VALIDATED"))
    monkeypatch.setattr(
        module,
        "_evidence_review_status",
        lambda: (True, "READY_FOR_PRODUCTION_COORDINATION_REVIEW"),
    )
    module.PLAN_DOC.write_text("STAGING_VALIDATED\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "production coordination safety markers" in output
    assert "Result: FAIL" in output


def test_production_coordination_blocks_when_evidence_review_not_ready(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "_readiness_status", lambda: (True, "STAGING_VALIDATED"))
    monkeypatch.setattr(module, "_evidence_review_status", lambda: (True, "STAGING_GAPS_REQUIRE_TRIAGE"))

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "BLOCKED_BY_EVIDENCE_REVIEW" in output
    assert "Result: FAIL" in output


def test_production_coordination_result_pass_uses_final_result_line():
    module = _load_module()
    passing = type("Result", (), {"returncode": 0})()
    failing = type("Result", (), {"returncode": 0})()
    nonzero = type("Result", (), {"returncode": 1})()

    assert module._result_pass(passing, "Overall: READY\nResult: PASS\n") is True
    assert module._result_pass(failing, "Overall: READY\nnested Result: PASS\nResult: FAIL\n") is False
    assert module._result_pass(nonzero, "Result: PASS\n") is False


def test_production_coordination_readiness_status_rejects_final_fail(monkeypatch):
    module = _load_module()

    def fake_run(*args, **kwargs):  # noqa: ARG001
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": "Overall: STAGING_VALIDATED\nnested Result: PASS\nResult: FAIL\n",
                "stderr": "",
            },
        )()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    ok, status = module._readiness_status()

    assert ok is False
    assert status == "STAGING_VALIDATED"
