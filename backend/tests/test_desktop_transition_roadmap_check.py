from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "desktop_transition_roadmap_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("desktop_transition_roadmap_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_desktop_transition_roadmap_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Desktop Transition Roadmap Check" in output
    assert "Result: PASS" in output


def test_desktop_transition_roadmap_check_flags_missing_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "roadmap_desktop_transition.md"
    doc.write_text("Desktop Transition Roadmap\n", encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "desktop transition roadmap matches current D7-D9 execution state" in output


def test_desktop_transition_roadmap_check_flags_stale_checklist(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "roadmap_desktop_transition.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "[ ] README"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "desktop transition roadmap avoids stale checklist markers" in output


def test_desktop_transition_roadmap_check_flags_secret_like_marker(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "roadmap_desktop_transition.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"']),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "desktop transition roadmap is redacted" in output
