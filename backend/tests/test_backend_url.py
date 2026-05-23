"""Tests for configurable backend base URL (D5.2.6)."""

from __future__ import annotations

import pytest

from app.core.backend_url import (
    DEFAULT_BACKEND_BASE_URL,
    get_backend_base_url,
    get_health_url,
    log_backend_base_url,
    parse_backend_host_port,
)


def test_default_backend_base_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("BACKEND_BASE_URL", raising=False)
    assert get_backend_base_url() == DEFAULT_BACKEND_BASE_URL
    assert get_health_url() == "http://127.0.0.1:8010/health"
    host, port = parse_backend_host_port()
    assert host == "127.0.0.1"
    assert port == 8010


def test_custom_backend_base_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BACKEND_BASE_URL", "http://127.0.0.1:8010/")
    assert get_backend_base_url() == "http://127.0.0.1:8010"
    assert get_health_url() == "http://127.0.0.1:8010/health"
    host, port = parse_backend_host_port()
    assert host == "127.0.0.1"
    assert port == 8010


def test_log_backend_base_url(capsys, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BACKEND_BASE_URL", "http://127.0.0.1:8010")
    url = log_backend_base_url()
    captured = capsys.readouterr().out
    assert url == "http://127.0.0.1:8010"
    assert "Using BACKEND_BASE_URL=http://127.0.0.1:8010" in captured
