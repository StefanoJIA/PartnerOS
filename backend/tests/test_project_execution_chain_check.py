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


def test_project_execution_chain_check_writes_redacted_report(monkeypatch, tmp_path, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "CHAIN", (("one", "one.py"),))
    monkeypatch.setattr(
        module,
        "_run_script",
        lambda script: SimpleNamespace(returncode=0, stdout="Overall: READY_FOR_STAGING\nraw body ignored\n", stderr=""),
    )
    report = tmp_path / "project_execution_chain_20260530.md"

    assert module.main(["--report-markdown", str(report)]) == 0
    output = capsys.readouterr().out
    text = report.read_text(encoding="utf-8")
    assert "READY_FOR_STAGING_HANDOFF" in output
    assert "Project Execution Chain Report" in text
    assert "Overall: READY_FOR_STAGING" in text
    assert "raw body ignored" not in text


def test_project_execution_chain_check_omits_secret_like_summary(monkeypatch, tmp_path):
    module = _load_module()
    monkeypatch.setattr(module, "CHAIN", (("one", "one.py"),))
    monkeypatch.setattr(
        module,
        "_run_script",
        lambda script: SimpleNamespace(
            returncode=0,
            stdout="Result: PASS SERVICE_PORTAL_API_KEY=actual-secret-value\n",
            stderr="",
        ),
    )
    report = tmp_path / "project_execution_chain_20260530.md"

    assert module.main(["--report-markdown", str(report)]) == 0
    text = report.read_text(encoding="utf-8")
    assert "actual-secret-value" not in text
    assert "summary omitted because it contained secret-like" in text


def test_project_execution_chain_check_rejects_backend_storage_report_path(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "CHAIN", (("one", "one.py"),))
    monkeypatch.setattr(
        module,
        "_run_script",
        lambda script: SimpleNamespace(returncode=0, stdout="Result: PASS\n", stderr=""),
    )

    assert module.main(["--report-markdown", "storage/project_execution_chain.md"]) == 1
    output = capsys.readouterr().out
    assert "report output path" in output


def test_project_execution_chain_check_rejects_noncanonical_report_name(monkeypatch, tmp_path, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "CHAIN", (("one", "one.py"),))
    monkeypatch.setattr(
        module,
        "_run_script",
        lambda script: SimpleNamespace(returncode=0, stdout="Result: PASS\n", stderr=""),
    )

    assert module.main(["--report-markdown", str(tmp_path / "project_execution_chain_latest.md")]) == 1
    output = capsys.readouterr().out
    assert "project_execution_chain_YYYYMMDD.md" in output
