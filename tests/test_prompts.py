"""Tests for MCP prompts — diagram_helper."""

from __future__ import annotations

from kroki_mcp.mcp_server import create_server


class TestDiagramHelperPrompt:
    async def test_known_type_returns_syntax(self) -> None:
        server = create_server()
        result = await server.render_prompt(
            "diagram_helper", {"diagram_type": "mermaid"}
        )
        text = result.messages[0].content.text
        assert "mermaid" in text.lower()
        assert "render_diagram" in text

    async def test_unknown_type_returns_generic(self) -> None:
        server = create_server()
        result = await server.render_prompt(
            "diagram_helper", {"diagram_type": "wireviz"}
        )
        text = result.messages[0].content.text
        assert "render_diagram" in text

    async def test_plantuml_has_example(self) -> None:
        server = create_server()
        result = await server.render_prompt(
            "diagram_helper", {"diagram_type": "plantuml"}
        )
        text = result.messages[0].content.text
        assert "@startuml" in text
