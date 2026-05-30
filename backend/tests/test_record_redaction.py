from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "record_redaction.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("record_redaction", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_record_redaction_flags_generic_secret_assignments():
    module = _load_module()

    issues = module.redaction_issues(Path("record.md"), "SERVICE_PORTAL_API_KEY=actual-secret-value\n")

    assert issues == ["record.md:1"]


def test_record_redaction_allows_placeholders():
    module = _load_module()
    text = "\n".join(
        [
            "SERVICE_PORTAL_API_KEY=<redacted>",
            "SERVICE_PORTAL_PRIVATE_KEY=<provided-privately>",
            "SERVICE_PORTAL_TOKEN=***",
        ]
    )

    assert module.redaction_issues(Path("record.md"), text) == []


def test_record_redaction_flags_authorization_bearer_value():
    module = _load_module()

    issues = module.redaction_issues(Path("record.md"), "Authorization: Bearer actual-secret-value\n")

    assert issues == ["record.md:1"]


def test_record_redaction_can_skip_common_markers_for_runbook_boundary_text():
    module = _load_module()
    text = "No raw response body, local_data, or backend/storage artifact may be committed.\n"

    assert module.redaction_issues(Path("runbook.md"), text, include_common_markers=False) == []
    assert module.redaction_issues(Path("record.md"), text) == [
        "record.md:backend/storage",
        "record.md:local_data",
        "record.md:raw response body",
    ]


def test_record_redaction_allows_plural_safety_statement():
    module = _load_module()
    text = "No tokens or raw response bodies included.\n"

    assert module.redaction_issues(Path("record.md"), text) == []
