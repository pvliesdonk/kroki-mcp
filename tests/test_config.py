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

    def test_url_missing_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("KROKI_MCP_KROKI_URL", raising=False)
        with pytest.raises(ValueError, match="KROKI_MCP_KROKI_URL"):
            load_config()

    def test_url_empty_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KROKI_MCP_KROKI_URL", "  ")
        with pytest.raises(ValueError, match="KROKI_MCP_KROKI_URL"):
            load_config()
