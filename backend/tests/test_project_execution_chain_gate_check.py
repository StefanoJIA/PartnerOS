from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_execution_chain_gate_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("project_execution_chain_gate_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_project_execution_chain_gate_check_passes_for_repo_doc(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Project Execution Chain Gate Check" in output
    assert "Result: PASS" in output


def test_project_execution_chain_gate_check_flags_token_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "project_execution_chain_gate.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "SERVICE_PORTAL_PARTNEROS_TOKEN=secret"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "chain gate remains redacted" in output
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN=" in output


def test_project_execution_chain_gate_check_flags_missing_proof_record(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "project_execution_chain_gate.md"
    doc.write_text("\n".join(module.REQUIRED_MARKERS), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "chain gate proof records exist" in output
    assert "docs/records/project_execution_chain_20260531.md" in output
