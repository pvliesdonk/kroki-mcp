"""Tests for MCP resources — kroki://health."""

from __future__ import annotations

import json

import httpx
import respx

from kroki_mcp.mcp_server import create_server


class TestHealthResource:
    async def test_health_ok(self) -> None:
        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/").mock(return_value=httpx.Response(200, text="OK"))
            server = create_server()
            async with server._lifespan_manager():
                result = await server.read_resource("kroki://health")
                data = json.loads(result.contents[0].content)
                assert data["status"] == "ok"
                assert "kroki.test" in data["kroki_url"]

    async def test_health_unreachable(self) -> None:
        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/").mock(side_effect=httpx.ConnectError("Connection refused"))
            server = create_server()
            async with server._lifespan_manager():
                result = await server.read_resource("kroki://health")
                data = json.loads(result.contents[0].content)
                assert data["status"] == "unreachable"
                assert "error" in data
