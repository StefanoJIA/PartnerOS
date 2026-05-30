from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "readme_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("readme_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_readme_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "README Check" in output
    assert "Result: PASS" in output


def test_readme_check_flags_missing_current_stage_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "README.md"
    doc.write_text("D8\nD9\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "README contains current stage and handoff gates" in output


def test_readme_check_flags_stale_d7_boundary(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "README.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "**D7** is Order / Production / Shipment."]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "README avoids stale stage claims" in output


def test_readme_check_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "README.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "README is redacted" in output
