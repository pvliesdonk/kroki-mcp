"""Tests for Kroki-specific configuration loading."""

from __future__ import annotations

import pytest

from kroki_mcp.config import load_config


class TestKrokiBaseUrl:
    def test_base_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KROKI_MCP_BASE_URL", "http://localhost:8000")
        config = load_config()
        assert config.kroki_base_url == "http://localhost:8000"

    def test_base_url_strips_trailing_slash(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("KROKI_MCP_BASE_URL", "http://localhost:8000/")
        config = load_config()
        assert config.kroki_base_url == "http://localhost:8000"

    def test_base_url_missing_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("KROKI_MCP_BASE_URL", raising=False)
        with pytest.raises(ValueError, match="KROKI_MCP_BASE_URL"):
            load_config()

    def test_base_url_empty_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KROKI_MCP_BASE_URL", "  ")
        with pytest.raises(ValueError, match="KROKI_MCP_BASE_URL"):
            load_config()
