"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove all KROKI_MCP_* env vars before each test.

    Prevents env var leakage between tests that call :func:`create_server`.
    Sets KROKI_MCP_KROKI_URL to a default so create_server() doesn't fail.
    """
    import os

    for key in list(os.environ):
        if key.startswith("KROKI_MCP_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("KROKI_MCP_KROKI_URL", "http://kroki.test:8000")
