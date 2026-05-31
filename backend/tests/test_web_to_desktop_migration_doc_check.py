from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "web_to_desktop_migration_doc_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("web_to_desktop_migration_doc_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_web_to_desktop_migration_doc_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Web To Desktop Migration Doc Check" in output
    assert "Result: PASS" in output


def test_web_to_desktop_migration_doc_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "migration_from_web_to_desktop.md"
    doc.write_text("Migration From Web Development To Desktop Product\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Web-to-desktop migration doc matches current state" in output


def test_web_to_desktop_migration_doc_check_flags_stale_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "migration_from_web_to_desktop.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "local checks prove STAGING_VALIDATED"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Web-to-desktop migration doc avoids stale or mojibake markers" in output


def test_web_to_desktop_migration_doc_check_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "migration_from_web_to_desktop.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Web-to-desktop migration doc is redacted" in output
