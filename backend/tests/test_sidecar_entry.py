"""D3: Frozen sidecar entry forces desktop runtime and starts uvicorn with host/port."""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest


def _save_and_remove_app_modules() -> dict[str, object]:
    saved = {
        k: sys.modules[k]
        for k in list(sys.modules)
        if k == "app" or k.startswith("app.")
    }
    for k in saved:
        del sys.modules[k]
    return saved


def _restore_app_modules(saved: dict[str, object]) -> None:
    for k in list(sys.modules):
        if k == "app" or k.startswith("app."):
            del sys.modules[k]
    sys.modules.update(saved)


def test_sidecar_main_forces_desktop_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_RUNTIME_MODE", raising=False)
    monkeypatch.setenv("PORT", "17666")
    saved = _save_and_remove_app_modules()
    sys.modules["app"] = MagicMock()
    sys.modules["app.main"] = MagicMock()
    try:
        with patch("uvicorn.run") as uv_run:
            import sidecar_entry

            sidecar_entry.main()
        assert os.environ["APP_RUNTIME_MODE"] == "desktop"
        uv_run.assert_called_once()
        kwargs = uv_run.call_args[1]
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 17666
    finally:
        _restore_app_modules(saved)
