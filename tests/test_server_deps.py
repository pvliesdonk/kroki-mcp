"""Tests for service lifespan and dependency injection."""

from __future__ import annotations

import httpx
import respx

from kroki_mcp._diagram_types import DIAGRAM_TYPES
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

        config = ServerConfig(kroki_url="http://kroki.test:8000/")
        lifespan_fn = make_service_lifespan(config)

        from fastmcp import FastMCP

        mcp = FastMCP("test")
        mcp._lifespan = lifespan_fn

        async with mcp._lifespan_manager():
            assert mcp._lifespan_result is not None
            assert isinstance(mcp._lifespan_result.get("service"), httpx.AsyncClient)

    async def test_lifespan_context_contains_available(self) -> None:
        """The lifespan context should expose an 'available' frozenset."""
        from kroki_mcp._server_deps import make_service_lifespan

        health_body = {
            "status": "pass",
            "version": {"graphviz": "9.0.0", "mermaid": "11.0.0", "plantuml": "1.2026.1"},
        }
        config = ServerConfig(kroki_url="http://kroki.test:8000/")
        lifespan_fn = make_service_lifespan(config)

        from fastmcp import FastMCP

        mcp = FastMCP("test")
        mcp._lifespan = lifespan_fn

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            async with mcp._lifespan_manager():
                available = mcp._lifespan_result.get("available")
                assert isinstance(available, frozenset)
                assert "graphviz" in available
                assert "mermaid" in available
                assert "plantuml" in available


class TestProbeAvailableTypes:
    async def test_success_returns_filtered_frozenset(self) -> None:
        """Health probe success -> frozenset of DIAGRAM_TYPES keys present in version."""
        from kroki_mcp._server_deps import _probe_available_types

        health_body = {
            "status": "pass",
            "version": {
                "graphviz": "9.0.0",
                "mermaid": "11.0.0",
                "plantuml": "1.2026.1",
                "dot": "9.0.0",
                "kroki": {"number": "0.30.1"},
                "diagramsnet": "21.0",
            },
        }
        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert isinstance(result, frozenset)
        assert "graphviz" in result
        assert "mermaid" in result
        assert "plantuml" in result
        assert "dot" not in result
        assert "kroki" not in result
        assert "diagramsnet" not in result

    async def test_connection_failure_returns_full_registry(self) -> None:
        """Health probe connection error -> full DIAGRAM_TYPES keyset returned."""
        from kroki_mcp._server_deps import _probe_available_types

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(side_effect=httpx.ConnectError("refused"))
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert result == frozenset(DIAGRAM_TYPES)

    async def test_non_200_response_returns_full_registry(self) -> None:
        """Health probe non-200 -> full DIAGRAM_TYPES keyset returned."""
        from kroki_mcp._server_deps import _probe_available_types

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(503, text="unavailable"))
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert result == frozenset(DIAGRAM_TYPES)

    async def test_malformed_json_returns_full_registry(self) -> None:
        """Health probe malformed JSON -> full DIAGRAM_TYPES keyset returned."""
        from kroki_mcp._server_deps import _probe_available_types

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(
                return_value=httpx.Response(200, text="not-json")
            )
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert result == frozenset(DIAGRAM_TYPES)

    async def test_only_known_types_returned(self) -> None:
        """Probe only returns keys that exist in DIAGRAM_TYPES."""
        from kroki_mcp._server_deps import _probe_available_types

        version_keys = dict.fromkeys(DIAGRAM_TYPES, "1.0")
        version_keys["unknown_future_type"] = "2.0"
        health_body = {"status": "pass", "version": version_keys}

        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            async with httpx.AsyncClient(base_url="http://kroki.test:8000/") as client:
                result = await _probe_available_types(client)

        assert "unknown_future_type" not in result
        assert result.issubset(frozenset(DIAGRAM_TYPES))
