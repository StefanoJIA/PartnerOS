from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_records_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_records_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_required_current_records(records_root: Path) -> None:
    (records_root / "d8_staging_operator_handoff_20260530.md").write_text(
        "Operator handoff: redacted\n",
        encoding="utf-8",
    )
    (records_root / "d8_staging_access_request_20260530.md").write_text(
        "BACKEND_BASE_URL: provided privately\n"
        "SERVICE_PORTAL_PARTNEROS_TOKEN: provided privately\n"
        "SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com\n",
        encoding="utf-8",
    )


REQUIRED_POLICY_MARKERS_FIXTURE = (
    "d8_staging_operator_handoff_YYYYMMDD.md",
    "d8_staging_access_request_YYYYMMDD.md",
    "d8_strict_staging_evidence_YYYYMMDD.json",
    "d8_strict_staging_gaps_YYYYMMDD.md",
    "current operator handoff and staging access request records",
    "Strict staging evidence and gap records are not required before the real staging run",
    "WAITING_FOR_STAGING_EVIDENCE",
    "Do not paste real `SERVICE_PORTAL_PARTNEROS_TOKEN`",
    "Do not store raw API response bodies",
)


def test_d8_staging_records_check_rejects_stale_policy_doc(tmp_path, monkeypatch, capsys):
    module = _load_module()
    records = tmp_path / "records"
    records.mkdir()
    policy = tmp_path / "policy.md"
    policy.write_text("D8 Staging Records Policy\n", encoding="utf-8")
    _write_required_current_records(records)
    monkeypatch.setattr(module, "RECORDS_ROOT", records)
    monkeypatch.setattr(module, "POLICY_DOC", policy)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging records policy matches current gate" in output
    assert "current operator handoff and staging access request records" in output


def test_d8_staging_records_check_rejects_missing_current_records(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "current D8 handoff records exist" in output
    assert "d8_staging_operator_handoff_YYYYMMDD.md" in output
    assert "d8_staging_access_request_YYYYMMDD.md" in output


def test_d8_staging_records_check_rejects_noncanonical_name(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_staging_notes.md").write_text("redacted notes\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging record names are canonical" in output
    assert "d8_staging_notes.md" in output


def test_d8_staging_records_check_rejects_undated_operator_handoff(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_staging_operator_handoff.md").write_text("redacted handoff\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging record names are canonical" in output
    assert "d8_staging_operator_handoff.md" in output


def test_d8_staging_records_check_requires_gap_register_for_failed_evidence(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        """
{
  "result": "FAIL",
  "checks": [],
  "safety": {
    "token_redacted": true,
    "response_bodies_stored": false
  }
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "missing d8_strict_staging_gaps_20260530.md" in output


def test_d8_staging_records_check_accepts_production_go_no_go_record(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_production_go_no_go_20260530.md").write_text(
        "Decision: Pause\nEvidence source: redacted summary only\n",
        encoding="utf-8",
    )

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 staging record names are canonical" in output
    assert "Result: PASS" in output


def test_d8_staging_records_check_accepts_staging_access_request_record(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 staging record names are canonical" in output
    assert "Result: PASS" in output


def test_d8_staging_records_check_rejects_bearer_token(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_staging_access_request_20260530.md").write_text(
        "BACKEND_BASE_URL: provided privately\n"
        "SERVICE_PORTAL_PARTNEROS_TOKEN: provided privately\n"
        "SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com\n",
        encoding="utf-8",
    )
    (tmp_path / "d8_staging_operator_handoff_20260530.md").write_text(
        "Authorization: Bearer actual-secret-value\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging records are redacted" in output
    assert "d8_staging_operator_handoff_20260530.md:1" in output
