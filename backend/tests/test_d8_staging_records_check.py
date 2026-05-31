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
        _valid_access_request_body() + "\n",
        encoding="utf-8",
    )


def _valid_access_request_body() -> str:
    return (
        "# D8 Staging Access Request - 2026-05-30\n\n"
        "Status: open\n"
        "Repository state: `READY_FOR_STAGING_HANDOFF`\n"
        "Evidence target: strict staging validation\n\n"
        "```text\n"
        "BACKEND_BASE_URL: provided privately\n"
        "SERVICE_PORTAL_PARTNEROS_TOKEN: provided privately\n"
        "SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com\n"
        "DEPLOYED_COMMIT: <short-sha-or-release>\n"
        "TEST_DATA_SCOPE: TEST customer/order/product/resource/feedback fixtures only\n"
        "```\n\n"
        "```powershell\n"
        "python scripts/d8_staging_input_preflight_check.py\n"
        "python scripts/d8_staging_operator_response_intake_check.py\n"
        "python scripts/d8_strict_staging_evidence_check.py --evidence-json ../docs/records/d8_strict_staging_evidence_YYYYMMDD.json --gap-markdown ../docs/records/d8_strict_staging_gaps_YYYYMMDD.md\n"
        "python scripts/d8_staging_records_check.py\n"
        "python scripts/d8_readiness_audit.py\n"
        "python scripts/d8_staging_evidence_review_check.py\n"
        "```\n\n"
        "- No `.env`\n"
        "- Do not deploy or modify `service.intelli-opus.com`\n"
    )


REQUIRED_POLICY_MARKERS_FIXTURE = (
    "d8_staging_operator_handoff_YYYYMMDD.md",
    "d8_staging_access_request_YYYYMMDD.md",
    "d8_strict_staging_evidence_YYYYMMDD.json",
    "d8_strict_staging_gaps_YYYYMMDD.md",
    "current operator handoff and staging access request records",
    "current access request record must include the redacted reply format and validation commands",
    "Any evidence record with `allow_local_http=true` or a localhost `backend_base_url` is rejected",
    "Strict staging evidence and gap records are not required before the real staging run",
    "WAITING_FOR_STAGING_EVIDENCE",
    "production Go / No-Go decision record",
    "Readiness: STAGING_VALIDATED",
    "Evidence review: READY_FOR_PRODUCTION_COORDINATION_REVIEW",
    "Do not paste real `SERVICE_PORTAL_PARTNEROS_TOKEN`",
    "Do not store raw API response bodies",
)


def _valid_production_go_no_go_body(module) -> str:
    return "\n".join(
        [
            "# D8 Production Go / No-Go - 2026-05-30",
            "",
            "Decision: Pause",
            "Evidence source: redacted summary only",
            "",
            *module.PRODUCTION_DECISION_REQUIRED_MARKERS[2:],
        ]
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


def test_d8_staging_records_check_rejects_unredacted_evidence_backend_url(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        """
{
  "backend_base_url": "https://private-staging.example.com",
  "result": "PASS",
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
    assert "backend_base_url_redaction" in output


def test_d8_staging_records_check_accepts_redacted_evidence_backend_url(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        """
{
  "backend_base_url": "https://<redacted-backend>",
  "result": "PASS",
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

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "Result: PASS" in output


def test_d8_staging_records_check_rejects_pass_local_rehearsal_evidence(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        """
{
  "backend_base_url": "http://127.0.0.1:8014",
  "allow_local_http": true,
  "result": "PASS",
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
    assert "local_rehearsal_allows_local_http" in output
    assert "local_rehearsal_uses_local_backend" in output


def test_d8_staging_records_check_rejects_fail_local_rehearsal_evidence(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        """
{
  "backend_base_url": "http://127.0.0.1:8014",
  "allow_local_http": true,
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
    (tmp_path / "d8_strict_staging_gaps_20260530.md").write_text("redacted gap\n", encoding="utf-8")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "local_rehearsal_allows_local_http" in output
    assert "local_rehearsal_uses_local_backend" in output


def test_d8_staging_records_check_accepts_production_go_no_go_record(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_production_go_no_go_20260530.md").write_text(
        _valid_production_go_no_go_body(module) + "\n",
        encoding="utf-8",
    )

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 staging record names are canonical" in output
    assert "Result: PASS" in output


def test_d8_staging_records_check_rejects_production_go_no_go_without_safety(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_production_go_no_go_20260530.md").write_text(
        "Decision: Go\nEvidence source: redacted summary only\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 production decision records include safety markers" in output
    assert "d8_production_go_no_go_20260530.md:missing" in output


def test_d8_staging_records_check_rejects_invalid_production_decision_value(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)
    (tmp_path / "d8_production_go_no_go_20260530.md").write_text(
        _valid_production_go_no_go_body(module).replace("Decision: Pause", "Decision: Maybe") + "\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 production decision records include safety markers" in output
    assert "invalid Decision 'Maybe'" in output


def test_d8_staging_records_check_accepts_staging_access_request_record(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    _write_required_current_records(tmp_path)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "D8 staging record names are canonical" in output
    assert "Result: PASS" in output


def test_d8_staging_records_check_rejects_incomplete_access_request_record(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_staging_operator_handoff_20260530.md").write_text("Operator handoff: redacted\n", encoding="utf-8")
    (tmp_path / "d8_staging_access_request_20260530.md").write_text(
        "BACKEND_BASE_URL: provided privately\n"
        "SERVICE_PORTAL_PARTNEROS_TOKEN: provided privately\n"
        "SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 access request records are actionable" in output
    assert "Status: open" in output
    assert "python scripts/d8_staging_input_preflight_check.py" in output


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


def test_d8_staging_records_check_rejects_private_backend_url_status(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_staging_access_request_20260530.md").write_text(
        "BACKEND_BASE_URL: https://private-staging.example.com\n"
        "SERVICE_PORTAL_PARTNEROS_TOKEN: provided privately\n"
        "SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com\n",
        encoding="utf-8",
    )
    (tmp_path / "d8_staging_operator_handoff_20260530.md").write_text(
        "Operator handoff: redacted\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging records are redacted" in output
    assert "BACKEND_BASE_URL:<non-private-status>" in output


def test_d8_staging_records_check_rejects_committed_example_staging_host(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_staging_access_request_20260530.md").write_text(
        "BACKEND_BASE_URL: provided privately\n"
        "SERVICE_PORTAL_PARTNEROS_TOKEN: provided privately\n"
        "SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com\n",
        encoding="utf-8",
    )
    (tmp_path / "d8_staging_operator_handoff_20260530.md").write_text(
        '$env:BACKEND_BASE_URL="https://partneros-staging.example.com"\n',
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging records are redacted" in output
    assert "partneros-staging.example.com" in output


def test_d8_staging_records_check_rejects_portal_token_status_value(tmp_path, monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_staging_access_request_20260530.md").write_text(
        "BACKEND_BASE_URL: provided privately\n"
        "SERVICE_PORTAL_PARTNEROS_TOKEN: actual-secret-value\n"
        "SERVICE_PORTAL_ORIGIN: https://service.intelli-opus.com\n",
        encoding="utf-8",
    )
    (tmp_path / "d8_staging_operator_handoff_20260530.md").write_text(
        "Operator handoff: redacted\n",
        encoding="utf-8",
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "D8 staging records are redacted" in output
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN:<non-private-status>" in output
