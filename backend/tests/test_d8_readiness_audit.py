from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_readiness_audit.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_readiness_audit", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_readiness_audit_waits_without_strict_staging_evidence(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)

    assert module._staging_status() == ("READY_FOR_STAGING", "no strict staging evidence JSON found")


def test_readiness_audit_reports_staging_validated_for_pass_evidence(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        '{"result":"PASS","checks":[],"safety":{"token_redacted":true,"response_bodies_stored":false}}\n',
        encoding="utf-8",
    )

    assert module._staging_status() == ("STAGING_VALIDATED", "d8_strict_staging_evidence_20260530.json")


def test_readiness_audit_rejects_pass_local_rehearsal_evidence(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
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

    assert module._staging_status() == (
        "STAGING_EVIDENCE_LOCAL_REHEARSAL",
        "d8_strict_staging_evidence_20260530.json",
    )


def test_readiness_audit_rejects_noncanonical_evidence_name(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_strict_staging_evidence_latest.json").write_text(
        '{"result":"PASS","checks":[],"safety":{"token_redacted":true,"response_bodies_stored":false}}\n',
        encoding="utf-8",
    )

    assert module._staging_status() == (
        "STAGING_EVIDENCE_NONCANONICAL",
        "d8_strict_staging_evidence_latest.json",
    )


def test_readiness_audit_reports_open_gaps_for_failed_evidence(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text(
        '{"result":"FAIL","checks":[],"safety":{"token_redacted":true,"response_bodies_stored":false}}\n',
        encoding="utf-8",
    )
    (tmp_path / "d8_strict_staging_gaps_20260530.md").write_text("# gaps\n", encoding="utf-8")

    state, detail = module._staging_status()

    assert state == "STAGING_GAPS_OPEN"
    assert "d8_strict_staging_evidence_20260530.json" in detail
    assert "d8_strict_staging_gaps_20260530.md" in detail


def test_readiness_audit_rejects_unreadable_evidence(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "RECORDS_ROOT", tmp_path)
    (tmp_path / "d8_strict_staging_evidence_20260530.json").write_text("{not-json}\n", encoding="utf-8")

    assert module._staging_status() == (
        "STAGING_EVIDENCE_UNREADABLE",
        "d8_strict_staging_evidence_20260530.json",
    )


def test_readiness_audit_records_gate_uses_final_result_line(monkeypatch):
    module = _load_module()

    def fake_run(*args, **kwargs):  # noqa: ARG001
        return type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": "nested Result: PASS\nResult: FAIL\n",
                "stderr": "",
            },
        )()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    ok, detail = module._records_gate_status()

    assert ok is False
    assert "Result: FAIL" in detail


def test_readiness_audit_records_gate_requires_result_line(monkeypatch):
    module = _load_module()

    def fake_run(*args, **kwargs):  # noqa: ARG001
        return type("Result", (), {"returncode": 0, "stdout": "[PASS] records\n", "stderr": ""})()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    ok, detail = module._records_gate_status()

    assert ok is False
    assert "[PASS] records" in detail
