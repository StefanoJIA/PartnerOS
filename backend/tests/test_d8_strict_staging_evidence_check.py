from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_strict_staging_evidence_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_strict_staging_evidence_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_strict_staging_evidence_fails_without_backend_url_with_redacted_outputs(
    tmp_path, monkeypatch, capsys
):
    module = _load_module()
    evidence = tmp_path / "d8_strict_staging_evidence_20260530.json"
    gaps = tmp_path / "d8_strict_staging_gaps_20260530.md"
    monkeypatch.delenv("BACKEND_BASE_URL", raising=False)
    monkeypatch.delenv("SERVICE_PORTAL_PARTNEROS_TOKEN", raising=False)
    monkeypatch.delenv("PORTAL_CUSTOMER_API_TOKEN", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "d8_strict_staging_evidence_check.py",
            "--evidence-json",
            str(evidence),
            "--gap-markdown",
            str(gaps),
        ],
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "BACKEND_BASE_URL=<missing>" in output
    assert "Result: FAIL" in output

    payload = json.loads(evidence.read_text(encoding="utf-8"))
    assert payload["backend_base_url"] == "<missing>"
    assert payload["result"] == "FAIL"
    assert payload["safety"] == {
        "token_redacted": True,
        "response_bodies_stored": False,
        "customer_portal_deployed": False,
        "nginx_changed": False,
        "business_records_mutated": False,
    }
    assert "actual-secret" not in evidence.read_text(encoding="utf-8").lower()
    assert "Safety boundary" in gaps.read_text(encoding="utf-8")


def test_strict_staging_evidence_rejects_backend_storage_output_path():
    module = _load_module()

    with pytest.raises(ValueError, match="backend/storage"):
        module._safe_evidence_path("storage/d8_strict_staging_evidence_20260530.json")


def test_strict_staging_evidence_rejects_local_data_output_path():
    module = _load_module()

    with pytest.raises(ValueError, match="local_data"):
        module._safe_evidence_path("../local_data/d8_strict_staging_evidence_20260530.json")


def test_strict_staging_evidence_rejects_noncanonical_evidence_name(tmp_path):
    module = _load_module()

    with pytest.raises(ValueError, match="d8_strict_staging_evidence_YYYYMMDD.json"):
        module._safe_evidence_path(str(tmp_path / "d8_strict_staging_evidence_latest.json"))


def test_strict_staging_evidence_rejects_noncanonical_gap_name(tmp_path):
    module = _load_module()

    with pytest.raises(ValueError, match="d8_strict_staging_gaps_YYYYMMDD.md"):
        module._safe_output_path(str(tmp_path / "d8_strict_staging_gaps_latest.md"))


def test_strict_staging_evidence_accepts_canonical_gap_name(tmp_path):
    module = _load_module()

    assert module._safe_output_path(str(tmp_path / "d8_strict_staging_gaps_20260530.md")).name == (
        "d8_strict_staging_gaps_20260530.md"
    )


def test_strict_staging_evidence_fails_for_short_token_without_printing_it(
    tmp_path, monkeypatch, capsys
):
    module = _load_module()
    evidence = tmp_path / "d8_strict_staging_evidence_20260530.json"
    monkeypatch.delenv("BACKEND_BASE_URL", raising=False)
    monkeypatch.setenv("SERVICE_PORTAL_PARTNEROS_TOKEN", "short-secret")
    monkeypatch.setenv("SERVICE_PORTAL_ORIGIN", "https://service.intelli-opus.com")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "d8_strict_staging_evidence_check.py",
            "--evidence-json",
            str(evidence),
        ],
    )

    assert module.main() == 1
    output = capsys.readouterr().out
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    token_check = next(check for check in payload["checks"] if check["label"] == "portal token safe")

    assert token_check["status"] == "FAIL"
    assert "set a non-default SERVICE_PORTAL_PARTNEROS_TOKEN" in token_check["detail"]
    assert "short-secret" not in output
    assert "short-secret" not in evidence.read_text(encoding="utf-8")
