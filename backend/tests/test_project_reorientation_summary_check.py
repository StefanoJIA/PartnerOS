from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_reorientation_summary_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("project_reorientation_summary_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_project_reorientation_summary_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Project Reorientation Summary Check" in output
    assert "Result: PASS" in output


def test_project_reorientation_summary_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "project_reorientation_summary.md"
    doc.write_text("Project Reorientation Summary\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "project reorientation summary matches current execution state" in output


def test_project_reorientation_summary_check_flags_stale_priority(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "project_reorientation_summary.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "Current priority: complete **D0 documentation**"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "project reorientation summary avoids stale D0/D1 priority" in output


def test_project_reorientation_summary_check_flags_secret_like_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "project_reorientation_summary.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "project reorientation summary is redacted" in output
