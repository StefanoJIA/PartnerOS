from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "phase3_roadmap_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("phase3_roadmap_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase3_roadmap_check_passes_for_current_roadmap(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "roadmap contains D7-D9 stages" in output
    assert "Result: PASS" in output


def test_phase3_roadmap_check_fails_when_required_stage_missing(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "ROADMAP", tmp_path / "phase3_roadmap.md")
    module.ROADMAP.write_text("**D7.1**\nD6 --> D71\nNo auto-send\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "roadmap contains D7-D9 stages" in output
    assert "D9" in output


def test_phase3_roadmap_check_fails_when_safety_boundary_missing(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "ROADMAP", tmp_path / "phase3_roadmap.md")
    text = "\n".join(f"**{stage}**" for stage in module.REQUIRED_STAGES)
    text += "\n" + "\n".join(module.REQUIRED_DOC_LINKS)
    text += "\n" + "\n".join(module.REQUIRED_GRAPH_MARKERS)
    module.ROADMAP.write_text(text + "\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "roadmap preserves safety boundaries" in output
    assert "No auto-send" in output
