from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_execution_records_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("project_execution_records_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_project_execution_records_check_passes_without_reports(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)

    assert module.main() == 0
    assert "Result: PASS" in capsys.readouterr().out


def test_project_execution_records_check_rejects_noncanonical_name(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "project_execution_chain_latest.md").write_text("Project Execution Chain Report\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "project execution report names are canonical" in output
    assert "project_execution_chain_latest.md" in output


def test_project_execution_records_check_rejects_token_assignment(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "project_execution_chain_20260530.md").write_text(
        """
# Project Execution Chain Report
State: `READY_FOR_STAGING_HANDOFF`
| Gate | Status | Summary |
|---|---|---|
SERVICE_PORTAL_PARTNEROS_TOKEN=actual-secret-value
""".strip()
        + "\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "project execution reports are redacted" in output
    assert "project_execution_chain_20260530.md:5" in output


def test_project_execution_records_check_rejects_generic_secret_assignment(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "project_execution_chain_20260530.md").write_text(
        """
# Project Execution Chain Report
State: `READY_FOR_STAGING_HANDOFF`
| Gate | Status | Summary |
|---|---|---|
SERVICE_PORTAL_API_KEY=actual-secret-value
""".strip()
        + "\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "project execution reports are redacted" in output
    assert "project_execution_chain_20260530.md:5" in output
