from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "desktop_packaging_docs_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("desktop_packaging_docs_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_desktop_packaging_docs_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Desktop Packaging Docs Check" in output
    assert "Result: PASS" in output


def test_desktop_packaging_docs_check_flags_missing_packaging_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    packaging = tmp_path / "packaging_strategy.md"
    questions = tmp_path / "open_questions_desktop.md"
    packaging.write_text("Packaging Strategy\n", encoding="utf-8")
    questions.write_text("\n".join(module.REQUIRED_QUESTIONS_MARKERS), encoding="utf-8")
    monkeypatch.setattr(module, "PACKAGING_DOC", packaging)
    monkeypatch.setattr(module, "QUESTIONS_DOC", questions)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "packaging strategy matches current desktop boundary" in output


def test_desktop_packaging_docs_check_flags_stale_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    packaging = tmp_path / "packaging_strategy.md"
    questions = tmp_path / "open_questions_desktop.md"
    packaging.write_text("\n".join([*module.REQUIRED_PACKAGING_MARKERS, "local checks prove STAGING_VALIDATED"]), encoding="utf-8")
    questions.write_text("\n".join(module.REQUIRED_QUESTIONS_MARKERS), encoding="utf-8")
    monkeypatch.setattr(module, "PACKAGING_DOC", packaging)
    monkeypatch.setattr(module, "QUESTIONS_DOC", questions)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "desktop packaging docs avoid stale or mojibake markers" in output


def test_desktop_packaging_docs_check_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    packaging = tmp_path / "packaging_strategy.md"
    questions = tmp_path / "open_questions_desktop.md"
    packaging.write_text("\n".join([*module.REQUIRED_PACKAGING_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']), encoding="utf-8")
    questions.write_text("\n".join(module.REQUIRED_QUESTIONS_MARKERS), encoding="utf-8")
    monkeypatch.setattr(module, "PACKAGING_DOC", packaging)
    monkeypatch.setattr(module, "QUESTIONS_DOC", questions)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "desktop packaging docs are redacted" in output
