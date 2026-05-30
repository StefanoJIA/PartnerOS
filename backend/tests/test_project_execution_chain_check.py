from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_execution_chain_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("project_execution_chain_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_project_execution_chain_check_passes_when_all_gates_pass(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "CHAIN", (("one", "one.py"), ("two", "two.py")))
    monkeypatch.setattr(
        module,
        "_run_script",
        lambda script: SimpleNamespace(returncode=0, stdout="Result: PASS\n", stderr=""),
    )

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "READY_FOR_STAGING_HANDOFF" in output
    assert "[PASS] one" in output


def test_project_execution_chain_check_fails_when_any_gate_fails(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "CHAIN", (("one", "one.py"), ("two", "two.py")))

    def fake_run(script: str):
        if script == "two.py":
            return SimpleNamespace(returncode=1, stdout="[FAIL] two bad\nResult: FAIL\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="Result: PASS\n", stderr="")

    monkeypatch.setattr(module, "_run_script", fake_run)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "LOCAL_EXECUTION_CHAIN_INCOMPLETE" in output
    assert "[FAIL] two" in output
