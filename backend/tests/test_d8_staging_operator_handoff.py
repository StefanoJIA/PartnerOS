from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d8_staging_operator_handoff.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d8_staging_operator_handoff", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_handoff_text_contains_runbooks_commands_and_boundaries(monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "_git_head", lambda: "abc1234")

    text = module._handoff_text("READY_FOR_STAGING", "Overall: READY_FOR_STAGING")

    assert "Repository commit: `abc1234`" in text
    assert "docs/phase3/d8_staging_handoff_bundle.md" in text
    assert "docs/phase3/d8_staging_operator_runbook.md" in text
    assert "docs/phase3/d8_production_coordination_runbook.md" in text
    assert "python scripts/d8_strict_staging_evidence_check.py --evidence-json" in text
    assert "python scripts/project_execution_status.py" in text
    assert '$env:BACKEND_BASE_URL="<partneros-staging-backend-origin>"' in text
    assert "partneros-staging.example.com" not in text
    assert "Do not deploy or modify `service.intelli-opus.com`" in text
    assert "Do not print, screenshot, commit, or paste portal tokens" in text
    assert "SERVICE_PORTAL_PARTNEROS_TOKEN=<" not in text


def test_handoff_text_omits_secret_like_audit_output(monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "_git_head", lambda: "abc1234")

    text = module._handoff_text("READY_FOR_STAGING", "SERVICE_PORTAL_API_KEY=actual-secret-value")

    assert "actual-secret-value" not in text
    assert "Readiness audit output omitted" in text


def test_handoff_text_omits_audit_output_with_committed_staging_host(monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "_git_head", lambda: "abc1234")

    text = module._handoff_text(
        "LOCAL_ARTIFACTS_INCOMPLETE",
        "D8 records failed: partneros-staging.example.com",
    )

    assert "partneros-staging.example.com" not in text
    assert "Readiness audit output omitted" in text


def test_handoff_rejects_backend_storage_output_path():
    module = _load_module()

    with pytest.raises(ValueError, match="backend/storage"):
        module._safe_output_path("storage/d8_staging_operator_handoff_20260530.md")


def test_handoff_rejects_local_data_output_path():
    module = _load_module()

    with pytest.raises(ValueError, match="local_data"):
        module._safe_output_path("../local_data/d8_staging_operator_handoff_20260530.md")


def test_handoff_rejects_noncanonical_output_name(tmp_path):
    module = _load_module()

    with pytest.raises(ValueError, match="d8_staging_operator_handoff_YYYYMMDD.md"):
        module._safe_output_path(str(tmp_path / "d8_staging_operator_handoff_latest.md"))


def test_handoff_accepts_canonical_output_name(tmp_path):
    module = _load_module()

    assert module._safe_output_path(str(tmp_path / "d8_staging_operator_handoff_20260530.md")).name == (
        "d8_staging_operator_handoff_20260530.md"
    )
