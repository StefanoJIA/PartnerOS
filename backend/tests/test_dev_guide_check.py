from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "dev_guide_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("dev_guide_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dev_guide_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Developer Guide Check" in output
    assert "Result: PASS" in output


def test_dev_guide_check_flags_missing_handoff_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "dev_guide.md"
    doc.write_text("PartnerOS Developer Guide\n8014\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "developer guide contains current D8 handoff workflow" in output


def test_dev_guide_check_flags_stale_phase_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "dev_guide.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "D5.2.2 smoke test"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "developer guide avoids stale D0/D5 local setup markers" in output


def test_dev_guide_check_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "dev_guide.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "developer guide is redacted" in output
