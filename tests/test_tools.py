"""Tests for MCP tools — list_diagram_types and render_diagram."""

from __future__ import annotations

import base64
import json

import httpx
import pytest
import respx

from kroki_mcp._diagram_types import DIAGRAM_TYPES
from kroki_mcp.mcp_server import create_server


@pytest.fixture()
def mock_kroki() -> respx.MockRouter:
    """Create a respx mock router for Kroki API calls."""
    health_body = {
        "status": "pass",
        "version": {k: "1.0.0" for k in DIAGRAM_TYPES},
    }
    with respx.mock(base_url="http://kroki.test:8000") as router:
        router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
        yield router


class TestListDiagramTypes:
    async def test_returns_all_types(self) -> None:
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool("list_diagram_types", {})
            data = json.loads(result.content[0].text)
            types = {entry["type"] for entry in data}
            assert "plantuml" in types
            assert "mermaid" in types
            assert "graphviz" in types
            assert len(data) > 20

    async def test_each_entry_has_formats(self) -> None:
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool("list_diagram_types", {})
            data = json.loads(result.content[0].text)
            for entry in data:
                assert "type" in entry
                assert "formats" in entry
                assert len(entry["formats"]) >= 1


class TestRenderDiagram:
    async def test_render_svg(self, mock_kroki: respx.MockRouter) -> None:
        mock_kroki.post("/graphviz/svg").mock(
            return_value=httpx.Response(200, text="<svg>test</svg>")
        )
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool(
                "render_diagram",
                {
                    "diagram_type": "graphviz",
                    "source": "digraph { a -> b }",
                    "output_format": "svg",
                },
            )
            assert result.content[0].text == "<svg>test</svg>"

    async def test_render_png_as_image(self, mock_kroki: respx.MockRouter) -> None:
        png_bytes = b"\x89PNG fake image data"
        mock_kroki.post("/graphviz/png").mock(
            return_value=httpx.Response(200, content=png_bytes)
        )
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool(
                "render_diagram",
                {
                    "diagram_type": "graphviz",
                    "source": "digraph { a -> b }",
                    "output_format": "png",
                },
            )
            # MCP Image content is returned as base64-encoded data
            assert result.content[0].data == base64.b64encode(png_bytes).decode()
            assert result.content[0].mimeType == "image/png"

    async def test_render_png_as_base64(self, mock_kroki: respx.MockRouter) -> None:
        png_bytes = b"\x89PNG fake image data"
        mock_kroki.post("/graphviz/png").mock(
            return_value=httpx.Response(200, content=png_bytes)
        )
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool(
                "render_diagram",
                {
                    "diagram_type": "graphviz",
                    "source": "digraph { a -> b }",
                    "output_format": "png",
                    "as_base64": True,
                },
            )
            expected = base64.b64encode(png_bytes).decode()
            assert result.content[0].text == expected

    async def test_invalid_diagram_type(self) -> None:
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool(
                "render_diagram",
                {
                    "diagram_type": "not_a_type",
                    "source": "test",
                },
            )
            assert result.content[0].text
            assert "Unknown diagram type" in result.content[0].text

    async def test_invalid_format_for_type(self) -> None:
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool(
                "render_diagram",
                {
                    "diagram_type": "svgbob",
                    "source": "test",
                    "output_format": "png",
                },
            )
            assert "not supported" in result.content[0].text

    async def test_kroki_syntax_error(self, mock_kroki: respx.MockRouter) -> None:
        mock_kroki.post("/graphviz/svg").mock(
            return_value=httpx.Response(400, text="syntax error: unexpected token")
        )
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool(
                "render_diagram",
                {
                    "diagram_type": "graphviz",
                    "source": "bad { diagram",
                },
            )
            assert "syntax error" in result.content[0].text

    async def test_kroki_unreachable(self) -> None:
        """When Kroki is unreachable, the tool returns a helpful error."""
        server = create_server()
        async with server._lifespan_manager():
            with respx.mock(base_url="http://kroki.test:8000") as router:
                router.post("/graphviz/svg").mock(
                    side_effect=httpx.ConnectError("Connection refused")
                )
                result = await server.call_tool(
                    "render_diagram",
                    {
                        "diagram_type": "graphviz",
                        "source": "digraph { a -> b }",
                    },
                )
                assert "Cannot reach Kroki" in result.content[0].text

    async def test_kroki_timeout(self) -> None:
        server = create_server()
        async with server._lifespan_manager():
            with respx.mock(base_url="http://kroki.test:8000") as router:
                router.post("/graphviz/svg").mock(
                    side_effect=httpx.TimeoutException("timed out")
                )
                result = await server.call_tool(
                    "render_diagram",
                    {
                        "diagram_type": "graphviz",
                        "source": "digraph { a -> b }",
                    },
                )
                assert "did not respond" in result.content[0].text

    async def test_default_format_is_svg(self, mock_kroki: respx.MockRouter) -> None:
        route = mock_kroki.post("/mermaid/svg").mock(
            return_value=httpx.Response(200, text="<svg>mermaid</svg>")
        )
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool(
                "render_diagram",
                {
                    "diagram_type": "mermaid",
                    "source": "graph TD; A-->B",
                },
            )
            assert route.called
            assert result.content[0].text == "<svg>mermaid</svg>"


class TestAvailableFiltering:
    async def test_list_diagram_types_respects_available(self) -> None:
        """list_diagram_types only returns types present in the health response."""
        health_body = {
            "status": "pass",
            "version": {"graphviz": "9.0.0", "mermaid": "11.0.0"},
        }
        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            server = create_server()
            async with server._lifespan_manager():
                result = await server.call_tool("list_diagram_types", {})
                data = json.loads(result.content[0].text)
                types = {entry["type"] for entry in data}
                assert types == {"graphviz", "mermaid"}

    async def test_render_diagram_type_not_in_available(self) -> None:
        """render_diagram rejects a type absent from the health-derived available set."""
        health_body = {
            "status": "pass",
            "version": {"graphviz": "9.0.0"},
        }
        with respx.mock(base_url="http://kroki.test:8000") as router:
            router.get("/health").mock(return_value=httpx.Response(200, json=health_body))
            server = create_server()
            async with server._lifespan_manager():
                result = await server.call_tool(
                    "render_diagram",
                    {"diagram_type": "mermaid", "source": "graph TD; A-->B"},
                )
                assert "Unknown diagram type" in result.content[0].text

    async def test_render_diagram_type_in_available(
        self, mock_kroki: respx.MockRouter
    ) -> None:
        """render_diagram succeeds for a type present in the available set."""
        mock_kroki.post("/graphviz/svg").mock(
            return_value=httpx.Response(200, text="<svg>ok</svg>")
        )
        server = create_server()
        async with server._lifespan_manager():
            result = await server.call_tool(
                "render_diagram",
                {"diagram_type": "graphviz", "source": "digraph { a -> b }"},
            )
            assert result.content[0].text == "<svg>ok</svg>"
