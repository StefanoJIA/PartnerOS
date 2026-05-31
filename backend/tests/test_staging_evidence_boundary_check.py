from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "staging_evidence_boundary_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("staging_evidence_boundary_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_staging_evidence_boundary_check_passes_for_repo_docs(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Staging Evidence Boundary Check" in output
    assert "Result: PASS" in output


def test_staging_evidence_boundary_check_flags_unpaired_staging_marker(tmp_path, monkeypatch, capsys):
    module = _load_module()
    doc = tmp_path / "doc.md"
    doc.write_text("This claims STAGING_VALIDATED without the wait-state boundary.\n", encoding="utf-8")
    monkeypatch.setattr(module, "SCAN_ROOTS", (tmp_path,))

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "doc.md" in output
    assert "Result: FAIL" in output


def test_staging_evidence_boundary_check_ignores_records(tmp_path, monkeypatch, capsys):
    module = _load_module()
    records = tmp_path / "docs" / "records"
    records.mkdir(parents=True)
    (records / "d8_production_go_no_go_20990101.md").write_text(
        "Readiness: STAGING_VALIDATED\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "SCAN_ROOTS", (tmp_path / "docs",))

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Result: PASS" in output
