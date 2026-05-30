from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_local_staging_rehearsal_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_local_staging_rehearsal_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_local_staging_rehearsal_check_passes_for_repo_doc(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 Local Staging Rehearsal Check" in output
    assert "Result: PASS" in output


def test_d8_local_staging_rehearsal_check_flags_real_token(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "rehearsal.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "SERVICE_PORTAL_PARTNEROS_TOKEN=secret"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN=" in output
