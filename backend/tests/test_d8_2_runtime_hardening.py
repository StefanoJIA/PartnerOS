"""Unit tests for D8.2 runtime hardening checks."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from app.core.config import Settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = BACKEND_ROOT / "scripts" / "d8_2_runtime_hardening_check.py"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _load_script():
    spec = importlib.util.spec_from_file_location("d8_2_runtime_hardening_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


script = _load_script()


def test_strict_staging_fails_development_defaults():
    runtime = script._check_runtime_mode(True, "development")
    secret = script._check_secret(True, "dev-secret-change-in-production")
    public = script._check_public_base_url(True, "http://example.com")

    assert runtime.level == "FAIL"
    assert secret.level == "FAIL"
    assert public.level == "FAIL"


def test_local_mode_warns_instead_of_failing_defaults():
    runtime = script._check_runtime_mode(False, "development")
    secret = script._check_secret(False, "dev-secret-change-in-production")
    public = script._check_public_base_url(False, "")

    assert runtime.level == "WARN"
    assert secret.level == "WARN"
    assert public.level == "WARN"


def test_portal_token_checks_do_not_print_secret_value():
    settings = Settings(
        PORTAL_CUSTOMER_API_ENABLED=True,
        PORTAL_CUSTOMER_API_REQUIRE_TOKEN=True,
        PORTAL_CUSTOMER_API_TOKEN="test-portal-token",
        PORTAL_CUSTOMER_ALLOWED_ORIGINS="https://service.intelli-opus.com",
    )

    items = script._check_portal_token(True, settings)
    rendered = "\n".join(item.line() for item in items)

    assert items[1].level == "FAIL"
    assert "test-portal-token" not in rendered
    assert "service portal origin configured" in rendered


def test_finish_reports_pass_and_warning_count(capsys):
    warning = script.Check("local warning")
    warning.warn("development mode")

    assert script._finish([warning], strict=False) == 0
    output = capsys.readouterr().out
    assert "D8.2 Runtime Hardening Check" in output
    assert "[WARN] local warning (development mode)" in output
    assert "Result: PASS" in output
    assert "Warnings: 1" in output


def test_finish_reports_fail(capsys):
    failure = script.Check("strict failure")
    failure.fail("bad config")

    assert script._finish([failure], strict=True) == 1
    output = capsys.readouterr().out
    assert "strict_staging=True" in output
    assert "[FAIL] strict failure (bad config)" in output
    assert "Result: FAIL" in output
