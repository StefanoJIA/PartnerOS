from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "integrated_backend_standards_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("integrated_backend_standards_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_integrated_backend_standards_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Integrated Backend Standards Check" in output
    assert "Result: PASS" in output


def test_integrated_backend_standards_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "integrated_backend_standards.md"
    doc.write_text("Integrated Backend Standards\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "integrated backend standards match current D7-D9 state" in output


def test_integrated_backend_standards_check_flags_stale_phase(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "integrated_backend_standards.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "Phase 1 is current"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "integrated backend standards avoid stale early-phase markers" in output


def test_integrated_backend_standards_check_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "integrated_backend_standards.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "integrated backend standards are redacted" in output
