from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d9_operating_execution_pack_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d9_operating_execution_pack_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d9_operating_execution_pack_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D9 Operating Execution Pack Check" in output
    assert "Result: PASS" in output


def test_d9_operating_execution_pack_check_flags_missing_doc_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "pack.md"
    doc.write_text("D9 Operating Execution Pack\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 execution pack doc is actionable" in output


def test_d9_operating_execution_pack_check_flags_generic_secret(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "pack.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_DOC_MARKERS, "SERVICE_PORTAL_SECRET=actual-secret-value"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)
    monkeypatch.setattr(module, "_run_script", lambda script: type("Result", (), {"returncode": 0, "stdout": "Result: PASS", "stderr": ""})())

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D9 execution pack doc is redacted" in output
    assert "pack.md" in output


def test_d9_operating_execution_pack_uses_final_result_line():
    module = _load_module()

    passing = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="[PASS] child\nResult: PASS\n",
        stderr="",
    )
    nested_fail = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="nested Result: PASS\nResult: FAIL\n",
        stderr="",
    )
    no_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="[PASS] child\n", stderr="")

    assert module._result_pass(passing) is True
    assert module._result_pass(nested_fail) is False
    assert module._result_pass(no_result) is False


def test_d9_operating_execution_pack_accepts_readiness_overall_output():
    module = _load_module()
    result = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="D8 Readiness Audit\nOverall: READY_FOR_STAGING\n",
        stderr="",
    )

    assert module._script_pass("scripts/d8_readiness_audit.py", result) is True
