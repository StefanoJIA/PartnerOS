from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "testing_guide_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("testing_guide_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_testing_guide_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Testing Guide Check" in output
    assert "Result: PASS" in output


def test_testing_guide_check_flags_missing_matrix_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "testing.md"
    doc.write_text("Testing Guide\n8014\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "testing guide contains current D7.6+/D8 validation matrix" in output


def test_testing_guide_check_flags_stale_primary_matrix(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "testing.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "D5.2.11 Internal MVP Release Pack"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "testing guide avoids stale primary D5/D6 test matrix" in output


def test_testing_guide_check_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "testing.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "testing guide is redacted" in output
