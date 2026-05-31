from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "codex_skill_pack_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("codex_skill_pack_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pack(module, root: Path, extra: str = "") -> None:
    root.mkdir()
    markers = "\n".join(module.REQUIRED_MARKERS)
    for name in module.REQUIRED_FILES:
        (root / name).write_text(f"{name}\n{markers}\n{extra}", encoding="utf-8")


def test_codex_skill_pack_check_passes(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Codex Skill Pack Check" in output
    assert "Result: PASS" in output


def test_codex_skill_pack_check_flags_missing_file(monkeypatch, tmp_path, capsys):
    module = _load_module()
    pack = tmp_path / "codex_skills"
    pack.mkdir()
    for name in module.REQUIRED_FILES[:-1]:
        (pack / name).write_text("\n".join(module.REQUIRED_MARKERS), encoding="utf-8")
    monkeypatch.setattr(module, "DOC_DIR", pack)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Codex skill pack files exist" in output


def test_codex_skill_pack_check_flags_stale_guidance(monkeypatch, tmp_path, capsys):
    module = _load_module()
    pack = tmp_path / "codex_skills"
    _write_pack(module, pack, "D7.7 covers customer portal bridge APIs and feedback intake")
    monkeypatch.setattr(module, "DOC_DIR", pack)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Codex skill pack avoids stale stage guidance" in output


def test_codex_skill_pack_check_flags_secret_like_assignment(monkeypatch, tmp_path, capsys):
    module = _load_module()
    pack = tmp_path / "codex_skills"
    _write_pack(module, pack, 'SERVICE_PORTAL_PARTNEROS_TOKEN="actual-secret-value"')
    monkeypatch.setattr(module, "DOC_DIR", pack)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Codex skill pack is redacted" in output
