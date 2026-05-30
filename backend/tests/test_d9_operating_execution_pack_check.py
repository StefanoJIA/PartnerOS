from __future__ import annotations

import importlib.util
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
