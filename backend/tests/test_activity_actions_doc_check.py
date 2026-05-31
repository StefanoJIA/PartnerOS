from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "activity_actions_doc_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("activity_actions_doc_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_activity_actions_doc_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Activity Actions Doc Check" in output
    assert "Result: PASS" in output


def test_activity_actions_doc_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "activity_actions.md"
    doc.write_text("Activity Actions\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "activity actions doc contains current canonical actions" in output


def test_activity_actions_doc_check_flags_stale_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "activity_actions.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "D0-D5.2"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "activity actions doc avoids stale or mojibake markers" in output


def test_activity_actions_doc_check_flags_secret_like_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "activity_actions.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "Bearer secret"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "activity actions doc is redacted" in output
