from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "d7_8_portal_live_integration_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("d7_8_portal_live_integration_check", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_portal_live_check_redacts_remote_backend_url():
    module = _load_module()

    assert module._redacted_backend_url("https://private-staging.example.com/api") == "https://<redacted-backend>/api"


def test_portal_live_check_keeps_local_backend_url():
    module = _load_module()

    assert module._redacted_backend_url("http://127.0.0.1:8014") == "http://127.0.0.1:8014"


def test_portal_live_forbidden_scan_tolerates_non_json_response():
    module = _load_module()

    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._no_forbidden_blob(response) == (True, "clean")


def test_portal_live_forbidden_scan_rejects_extended_markers():
    module = _load_module()

    response = SimpleNamespace(
        json=lambda: {
            "data": {
                "backend_path": "hidden",
                "download": "backend/storage/private.pdf",
                "auth": "password_hash",
            }
        }
    )

    clean, marker = module._no_forbidden_blob(response)
    assert clean is False
    assert marker in {"backend_path", "backend/storage", "password_hash"}


def test_portal_live_json_helper_tolerates_non_json_response():
    module = _load_module()

    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError("not json")))

    assert module._json(response) == {}
