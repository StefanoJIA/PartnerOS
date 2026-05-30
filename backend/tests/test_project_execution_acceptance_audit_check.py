from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_execution_acceptance_audit_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("project_execution_acceptance_audit_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_project_execution_acceptance_audit_check_passes_with_repo_doc(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        if script.endswith("d8_readiness_audit.py"):
            return SimpleNamespace(returncode=0, stdout="Overall: READY_FOR_STAGING\n", stderr="")
        if script.endswith("d8_production_coordination_check.py"):
            return SimpleNamespace(returncode=0, stdout="Coordination State: WAITING_FOR_STAGING_VALIDATION\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="Result: PASS\n", stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Project Execution Acceptance Audit Check" in output
    assert "Result: PASS" in output


def test_project_execution_acceptance_audit_check_fails_when_readiness_is_already_validated(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        if script.endswith("d8_readiness_audit.py"):
            return SimpleNamespace(returncode=0, stdout="Overall: STAGING_VALIDATED\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="Coordination State: READY_FOR_PRODUCTION_COORDINATION\n", stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 readiness remains pre-staging" in output
    assert "STAGING_VALIDATED" in output


def test_project_execution_acceptance_audit_check_fails_when_next_action_loses_runbook(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        if script.endswith("d8_readiness_audit.py"):
            return SimpleNamespace(returncode=0, stdout="Overall: READY_FOR_STAGING\n", stderr="")
        if script.endswith("d8_production_coordination_check.py"):
            return SimpleNamespace(returncode=0, stdout="Coordination State: WAITING_FOR_STAGING_VALIDATION\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="Result: PASS\n", stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)
    monkeypatch.setattr(
        module,
        "_status_next_action",
        lambda chain_state, readiness_state, coordination_state: (
            "READY_FOR_STAGING_HANDOFF",
            "Use docs/phase3/d8_staging_handoff_bundle.md, then run strict staging evidence.",
        ),
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "current next action points to staging handoff runbook" in output
    assert "d8_staging_operator_runbook.md" in output
