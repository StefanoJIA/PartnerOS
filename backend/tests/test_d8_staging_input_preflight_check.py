from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_input_preflight_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_input_preflight_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_staging_input_preflight_waits_when_values_missing(monkeypatch, capsys):
    module = _load_module()
    for name in ("BACKEND_BASE_URL", "SERVICE_PORTAL_PARTNEROS_TOKEN", "PORTAL_CUSTOMER_API_TOKEN", "SERVICE_PORTAL_ORIGIN"):
        monkeypatch.delenv(name, raising=False)

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "WAITING_FOR_PRIVATE_VALUES" in output


def test_staging_input_preflight_passes_with_safe_values(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setenv("BACKEND_BASE_URL", "https://partneros-staging.example.com")
    monkeypatch.setenv("SERVICE_PORTAL_PARTNEROS_TOKEN", "staging-secret-token-123")
    monkeypatch.setenv("SERVICE_PORTAL_ORIGIN", "https://service.intelli-opus.com")

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "INPUTS_READY" in output
    assert "st***23" in output
    assert "staging-secret-token-123" not in output


def test_staging_input_preflight_fails_for_unsafe_values(monkeypatch, capsys):
    module = _load_module()
    monkeypatch.setenv("BACKEND_BASE_URL", "http://partneros-staging.example.com")
    monkeypatch.setenv("SERVICE_PORTAL_PARTNEROS_TOKEN", "change-me")
    monkeypatch.setenv("SERVICE_PORTAL_ORIGIN", "http://service.intelli-opus.com")

    assert module.main() == 1
    output = capsys.readouterr().out
    assert "INPUTS_UNSAFE" in output
