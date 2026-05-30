from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_evidence_review_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_evidence_review_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d8_staging_evidence_review_waits_without_evidence(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Review State: WAITING_FOR_STAGING_EVIDENCE" in output
    assert "Result: PASS" in output


def test_d8_staging_evidence_review_accepts_pass_evidence(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        """
{
  "result": "PASS",
  "checks": [{"label": "health", "status": "PASS", "detail": "ok"}],
  "safety": {
    "token_redacted": true,
    "response_bodies_stored": false
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Review State: READY_FOR_PRODUCTION_COORDINATION_REVIEW" in output


def test_d8_staging_evidence_review_rejects_unsafe_evidence(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        """
{
  "result": "PASS",
  "checks": [],
  "safety": {
    "token_redacted": false,
    "response_bodies_stored": false
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "EVIDENCE_UNSAFE" in output


def test_d8_staging_evidence_review_flags_generic_private_key_in_doc(monkeypatch, tmp_path, capsys):
    module = _load_module()
    doc = tmp_path / "review.md"
    doc.write_text(
        "\n".join([*module.REQUIRED_DOC_MARKERS, "SERVICE_PORTAL_PRIVATE_KEY=actual-secret-value"]),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "DOC", doc)
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "evidence review doc is redacted" in output
    assert "review.md" in output
