"""Unit tests for D8.3 service portal staging contract helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = BACKEND_ROOT / "scripts" / "d8_3_service_portal_staging_check.py"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _load_script():
    spec = importlib.util.spec_from_file_location("d8_3_service_portal_staging_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


script = _load_script()


def test_no_forbidden_blob_accepts_customer_safe_payload():
    clean, detail = script.no_forbidden_blob(
        {
            "data": {
                "items": [
                    {
                        "order_number": "O-2026-0001",
                        "status": "confirmed",
                        "shipment": {"tracking_number": "TEST123"},
                    }
                ]
            }
        },
        token="portal-secret",
    )

    assert clean is True
    assert detail == "clean"


def test_no_forbidden_blob_rejects_internal_fields_and_token():
    internal, marker = script.no_forbidden_blob({"storage_key": "secret/path"})
    token, token_marker = script.no_forbidden_blob({"message": "abc portal-secret xyz"}, token="portal-secret")

    assert internal is False
    assert marker == "storage_key"
    assert token is False
    assert token_marker == "portal token leaked"


def test_redacted_url_hides_remote_backend_origin():
    assert script._redacted_url("https://private-staging.example.com/api") == "https://<redacted-backend>/api"
    assert script._redacted_url("http://127.0.0.1:8014") == "http://127.0.0.1:8014"


def test_staging_contract_rejects_placeholder_backend_without_network(monkeypatch, capsys):
    monkeypatch.setenv("BACKEND_BASE_URL", "https://<partneros-staging-backend-origin>")
    monkeypatch.setenv("SERVICE_PORTAL_PARTNEROS_TOKEN", "staging-secret-token-123")
    monkeypatch.setenv("SERVICE_PORTAL_ORIGIN", "https://service.intelli-opus.com")

    assert script.main() == 1
    output = capsys.readouterr().out
    assert "BACKEND_BASE_URL=https://<redacted-backend>" in output
    assert "placeholder BACKEND_BASE_URL" in output
    assert "not attempted; staging inputs unsafe" in output


def test_staging_contract_rejects_default_token_without_network(monkeypatch, capsys):
    monkeypatch.setenv("BACKEND_BASE_URL", "https://private-staging.example.com")
    monkeypatch.setenv("SERVICE_PORTAL_PARTNEROS_TOKEN", "test-portal-token")
    monkeypatch.setenv("SERVICE_PORTAL_ORIGIN", "https://service.intelli-opus.com")

    assert script.main() == 1
    output = capsys.readouterr().out
    assert "BACKEND_BASE_URL=https://<redacted-backend>" in output
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN must be non-default and private" in output
    assert "test-portal-token" not in output


def test_staging_contract_finish_reports_fail(capsys):
    check = script.Check("preflight")
    check.fail("unreachable")

    assert (
        script._finish(
            checks=[check],
            base="https://private-staging.example.com",
            origin="https://service.intelli-opus.com",
            create_feedback=False,
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "D8.3 Service Portal Staging Contract Check" in output
    assert "BACKEND_BASE_URL=https://<redacted-backend>" in output
    assert "[FAIL] preflight (unreachable)" in output
    assert "Result: FAIL" in output
