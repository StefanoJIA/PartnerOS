from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import httpx


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
    gap_text = gaps.read_text(encoding="utf-8")
    assert "Safety boundary" in gap_text
    assert "Owner: TBD` is a human owner placeholder only" in gap_text
    assert "not an auto-assignee, notification target, or permission to create tickets" in gap_text


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


def test_strict_staging_evidence_redacts_remote_backend_url():
    module = _load_module()

    assert module._redacted_url("https://partneros-staging.private.example.com") == "https://<redacted-backend>"
    assert (
        module._redacted_url("https://user:secret@partneros-staging.private.example.com/api?token=value")
        == "https://<redacted-backend>/api"
    )


def test_strict_staging_evidence_keeps_localhost_backend_url():
    module = _load_module()

    assert module._redacted_url("http://127.0.0.1:8014") == "http://127.0.0.1:8014"
    assert module._redacted_url("http://user:secret@localhost:8014/api") == "http://***:***@localhost:8014/api"


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


def test_strict_staging_evidence_rejects_placeholder_backend_without_network(
    tmp_path, monkeypatch, capsys
):
    module = _load_module()
    evidence = tmp_path / "d8_strict_staging_evidence_20260530.json"
    monkeypatch.setenv("BACKEND_BASE_URL", "https://<partneros-staging-backend-origin>")
    monkeypatch.setenv("SERVICE_PORTAL_PARTNEROS_TOKEN", "staging-secret-token-123")
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
    backend_check = next(check for check in payload["checks"] if check["label"] == "BACKEND_BASE_URL configured")
    health_check = next(check for check in payload["checks"] if check["label"] == "health reachable")

    assert "Result: FAIL" in output
    assert payload["backend_base_url"] == "https://<redacted-backend>"
    assert backend_check["detail"] == "placeholder BACKEND_BASE_URL"
    assert health_check["detail"] == "not attempted; staging inputs unsafe"


def test_strict_staging_evidence_rejects_placeholder_origin_without_network(
    tmp_path, monkeypatch, capsys
):
    module = _load_module()
    evidence = tmp_path / "d8_strict_staging_evidence_20260530.json"
    monkeypatch.setenv("BACKEND_BASE_URL", "https://partneros-staging.example.com")
    monkeypatch.setenv("SERVICE_PORTAL_PARTNEROS_TOKEN", "staging-secret-token-123")
    monkeypatch.setenv("SERVICE_PORTAL_ORIGIN", "https://<service-portal-origin>")
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
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    origin_check = next(check for check in payload["checks"] if check["label"] == "portal origin HTTPS")
    health_check = next(check for check in payload["checks"] if check["label"] == "health reachable")

    assert origin_check["detail"] == "SERVICE_PORTAL_ORIGIN must be a real HTTPS origin"
    assert health_check["detail"] == "not attempted; staging inputs unsafe"


def test_strict_staging_evidence_rejects_placeholder_token_without_network(
    tmp_path, monkeypatch, capsys
):
    module = _load_module()
    evidence = tmp_path / "d8_strict_staging_evidence_20260530.json"
    monkeypatch.setenv("BACKEND_BASE_URL", "https://partneros-staging.example.com")
    monkeypatch.setenv("SERVICE_PORTAL_PARTNEROS_TOKEN", "<private-token-from-operator>")
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
    health_check = next(check for check in payload["checks"] if check["label"] == "health reachable")

    assert token_check["detail"] == "set a non-default SERVICE_PORTAL_PARTNEROS_TOKEN"
    assert health_check["detail"] == "not attempted; staging inputs unsafe"
    assert "private-token-from-operator" not in output
    assert "private-token-from-operator" not in evidence.read_text(encoding="utf-8")


def test_strict_staging_forbidden_scan_handles_httpx_json_response():
    module = _load_module()
    response = httpx.Response(200, json={"data": {"storage_key": "backend/storage/private.txt"}})

    clean, detail = module._no_forbidden_blob("portal-secret", response)

    assert clean is False
    assert detail == "storage_key"


def test_strict_staging_forbidden_scan_handles_httpx_text_response():
    module = _load_module()
    response = httpx.Response(500, text="temporary error included portal-secret")

    clean, detail = module._no_forbidden_blob("portal-secret", response)

    assert clean is False
    assert detail == "portal token leaked"
