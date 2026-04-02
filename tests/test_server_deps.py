"""Tests for service lifespan and dependency injection."""

from __future__ import annotations

import httpx

from kroki_mcp.config import ServerConfig


class TestServiceLifespan:
    async def test_lifespan_creates_httpx_client(self) -> None:
        """The lifespan should yield an httpx.AsyncClient as the service."""
        from kroki_mcp.mcp_server import create_server

        server = create_server()
        async with server._lifespan_manager():
            assert server._lifespan_result is not None
            assert isinstance(server._lifespan_result.get("service"), httpx.AsyncClient)

    async def test_service_is_httpx_client(self) -> None:
        """get_service() should return an httpx.AsyncClient."""
        from kroki_mcp._server_deps import make_service_lifespan

        config = ServerConfig(kroki_base_url="http://kroki.test:8000")
        lifespan_fn = make_service_lifespan(config)

        from fastmcp import FastMCP

        mcp = FastMCP("test")
        mcp._lifespan = lifespan_fn

        async with mcp._lifespan_manager():
            assert mcp._lifespan_result is not None
            assert isinstance(mcp._lifespan_result.get("service"), httpx.AsyncClient)
