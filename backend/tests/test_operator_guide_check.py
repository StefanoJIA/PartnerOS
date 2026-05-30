from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "operator_guide_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("operator_guide_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_operator_guide_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Operator Guide Check" in output
    assert "Result: PASS" in output


def test_operator_guide_check_flags_missing_gate_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "operator_guide.md"
    doc.write_text("D8 Integration Hardening\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "operator guide contains current D8/D9 handoff gates" in output


def test_operator_guide_check_flags_secret_like_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "operator_guide.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "SERVICE_PORTAL_SECRET=actual-secret-value"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "operator guide is redacted" in output
    assert "operator_guide.md" in output
