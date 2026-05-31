from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_execution_status.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("project_execution_status", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_project_execution_status_reports_staging_handoff(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        outputs = {
            "scripts/project_execution_chain_gate_check.py": "Result: PASS\n",
            "scripts/project_execution_chain_check.py": "State: READY_FOR_STAGING_HANDOFF\nResult: PASS\n",
            "scripts/d8_readiness_audit.py": "Overall: READY_FOR_STAGING\n",
            "scripts/d8_production_coordination_check.py": "Coordination State: WAITING_FOR_STAGING_VALIDATION\n",
        }
        return SimpleNamespace(returncode=0, stdout=outputs[script], stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "[PASS] project execution chain gate" in output
    assert "Current Stage: READY_FOR_STAGING_HANDOFF" in output
    assert "d8_staging_handoff_bundle.md" in output
    assert "d8_staging_operator_runbook.md" in output
    assert "docs/records/d8_staging_access_request_20260531.md" in output
    assert "d8_staging_access_request.md" in output
    assert "Result: PASS" in output


def test_project_execution_status_reports_production_coordination(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        outputs = {
            "scripts/project_execution_chain_gate_check.py": "Result: PASS\n",
            "scripts/project_execution_chain_check.py": "State: READY_FOR_STAGING_HANDOFF\nResult: PASS\n",
            "scripts/d8_readiness_audit.py": "Overall: STAGING_VALIDATED\n",
            "scripts/d8_production_coordination_check.py": "Coordination State: READY_FOR_PRODUCTION_COORDINATION\n",
        }
        return SimpleNamespace(returncode=0, stdout=outputs[script], stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Current Stage: READY_FOR_PRODUCTION_COORDINATION" in output
    assert "d8_production_coordination_runbook.md" in output
    assert "Go / No-Go" in output


def test_project_execution_status_reports_staging_gaps_open(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        outputs = {
            "scripts/project_execution_chain_gate_check.py": "Result: PASS\n",
            "scripts/project_execution_chain_check.py": "State: READY_FOR_STAGING_HANDOFF\nResult: PASS\n",
            "scripts/d8_readiness_audit.py": "Overall: STAGING_GAPS_OPEN\n",
            "scripts/d8_production_coordination_check.py": "Coordination State: WAITING_FOR_STAGING_VALIDATION\n",
        }
        return SimpleNamespace(returncode=0, stdout=outputs[script], stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Current Stage: STAGING_GAPS_OPEN" in output
    assert "Close the latest strict staging gap register" in output
    assert "rerun strict staging evidence" in output


def test_project_execution_status_reports_staging_validated_before_coordination(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        outputs = {
            "scripts/project_execution_chain_gate_check.py": "Result: PASS\n",
            "scripts/project_execution_chain_check.py": "State: READY_FOR_STAGING_HANDOFF\nResult: PASS\n",
            "scripts/d8_readiness_audit.py": "Overall: STAGING_VALIDATED\n",
            "scripts/d8_production_coordination_check.py": "Coordination State: WAITING_FOR_STAGING_VALIDATION\n",
        }
        return SimpleNamespace(returncode=0, stdout=outputs[script], stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Current Stage: STAGING_VALIDATED" in output
    assert "d8_production_coordination_runbook.md" in output
    assert "Run production coordination" in output


def test_project_execution_status_reports_evidence_review_block(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        outputs = {
            "scripts/project_execution_chain_gate_check.py": "Result: PASS\n",
            "scripts/project_execution_chain_check.py": "State: READY_FOR_STAGING_HANDOFF\nResult: PASS\n",
            "scripts/d8_readiness_audit.py": "Overall: STAGING_VALIDATED\n",
            "scripts/d8_production_coordination_check.py": "Coordination State: BLOCKED_BY_EVIDENCE_REVIEW\n",
        }
        return SimpleNamespace(returncode=0, stdout=outputs[script], stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Current Stage: BLOCKED_BY_EVIDENCE_REVIEW" in output
    assert "d8_staging_evidence_review_check.py" in output
    assert "rerun production coordination" in output


def test_project_execution_status_fails_when_chain_fails(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        if script == "scripts/project_execution_chain_gate_check.py":
            return SimpleNamespace(returncode=0, stdout="Result: PASS\n", stderr="")
        if script == "scripts/project_execution_chain_check.py":
            return SimpleNamespace(returncode=1, stdout="[FAIL] chain bad\nState: LOCAL_EXECUTION_CHAIN_INCOMPLETE\n", stderr="")
        if script == "scripts/d8_readiness_audit.py":
            return SimpleNamespace(returncode=0, stdout="Overall: READY_FOR_STAGING\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="Coordination State: WAITING_FOR_STAGING_VALIDATION\n", stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Current Stage: LOCAL_EXECUTION_CHAIN_INCOMPLETE" in output
    assert "[FAIL] project execution chain" in output


def test_project_execution_status_fails_when_chain_gate_fails(monkeypatch, capsys):
    module = _load_module()

    def fake_run(script: str):
        outputs = {
            "scripts/project_execution_chain_gate_check.py": "[FAIL] gate doc missing\nResult: FAIL\n",
            "scripts/project_execution_chain_check.py": "State: READY_FOR_STAGING_HANDOFF\nResult: PASS\n",
            "scripts/d8_readiness_audit.py": "Overall: READY_FOR_STAGING\n",
            "scripts/d8_production_coordination_check.py": "Coordination State: WAITING_FOR_STAGING_VALIDATION\n",
        }
        return SimpleNamespace(
            returncode=1 if script == "scripts/project_execution_chain_gate_check.py" else 0,
            stdout=outputs[script],
            stderr="",
        )

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Current Stage: LOCAL_EXECUTION_CHAIN_INCOMPLETE" in output
    assert "[FAIL] project execution chain gate" in output
    assert "gate doc missing" in output
