from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d9_1_operating_health_review_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d9_1_operating_health_review_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d9_1_operating_health_review_check_passes_for_repo_doc(capsys):
    module = _load_module()

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D9.1 Operating Health Review Check" in output
    assert "Result: PASS" in output


def test_d9_1_operating_health_review_requires_real_evidence_wait_gate():
    module = _load_module()

    assert "WAITING_FOR_REAL_STAGING_EVIDENCE" in module.REQUIRED_MARKERS


def test_d9_1_operating_health_review_check_flags_cookie(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "health.md"
    doc.write_text("\n".join([*module.REQUIRED_MARKERS, "Cookie: session=secret"]), encoding="utf-8")
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Cookie:" in output


def test_d9_1_operating_health_review_check_flags_generic_secret(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "health.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_MARKERS, "SERVICE_PORTAL_SECRET=actual-secret-value"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "health.md" in output
