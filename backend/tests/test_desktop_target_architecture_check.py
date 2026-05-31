from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "desktop_target_architecture_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("desktop_target_architecture_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_desktop_target_architecture_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Desktop Target Architecture Check" in output
    assert "Result: PASS" in output


def test_desktop_target_architecture_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "architecture_desktop_target.md"
    doc.write_text("Desktop Target Architecture\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "desktop target architecture matches current state" in output


def test_desktop_target_architecture_check_flags_mojibake(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "architecture_desktop_target.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "涓 bad encoding"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "desktop target architecture avoids stale or mojibake markers" in output


def test_desktop_target_architecture_check_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "architecture_desktop_target.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "desktop target architecture is redacted" in output
