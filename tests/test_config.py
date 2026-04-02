"""Tests for Kroki-specific configuration loading."""

from __future__ import annotations

import pytest

from kroki_mcp.config import load_config


class TestKrokiUrl:
    def test_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KROKI_MCP_KROKI_URL", "http://localhost:8000")
        config = load_config()
        assert config.kroki_url == "http://localhost:8000/"

    def test_url_normalises_trailing_slash(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("KROKI_MCP_KROKI_URL", "http://localhost:8000/")
        config = load_config()
        assert config.kroki_url == "http://localhost:8000/"

    def test_url_missing_uses_public_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("KROKI_MCP_KROKI_URL", raising=False)
        config = load_config()
        assert config.kroki_url == "https://kroki.io/"

    def test_url_empty_uses_public_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("KROKI_MCP_KROKI_URL", "  ")
        config = load_config()
        assert config.kroki_url == "https://kroki.io/"

    def test_using_public_instance_true_when_no_url(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("KROKI_MCP_KROKI_URL", raising=False)
        config = load_config()
        assert config.using_public_instance is True

    def test_using_public_instance_false_when_url_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("KROKI_MCP_KROKI_URL", "http://localhost:8000")
        config = load_config()
        assert config.using_public_instance is False
