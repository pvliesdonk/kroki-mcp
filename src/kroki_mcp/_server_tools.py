"""MCP tool registrations — Kroki diagram rendering.

Exposes :func:`list_diagram_types` and :func:`render_diagram` tools.
"""

from __future__ import annotations

import base64
import json
import logging

import httpx
from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from fastmcp.utilities.types import Image

from ._diagram_types import DIAGRAM_TYPES
from ._server_deps import get_available_types, get_service

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP, *, transport: str = "stdio") -> None:
    """Register all MCP tools on *mcp*.

    Args:
        mcp: The :class:`~fastmcp.FastMCP` instance to register tools on.
        transport: Active transport (``"stdio"``, ``"sse"``, or ``"http"``).
    """

    @mcp.tool()
    def list_diagram_types(
        available: frozenset[str] = Depends(get_available_types),
    ) -> str:
        """List all supported diagram types and their output formats.

        Returns:
            JSON array of objects with ``type`` and ``formats`` keys, filtered
            to only include types available on this Kroki instance.
        """
        entries = [
            {"type": dtype, "formats": formats}
            for dtype, formats in sorted(DIAGRAM_TYPES.items())
            if dtype in available
        ]
        return json.dumps(entries)

    @mcp.tool()
    async def render_diagram(
        diagram_type: str,
        source: str,
        output_format: str = "svg",
        as_base64: bool = False,
        client: httpx.AsyncClient = Depends(get_service),
        available: frozenset[str] = Depends(get_available_types),
    ) -> str | Image:
        """Render a diagram using Kroki.

        Args:
            diagram_type: Diagram language (e.g. ``"plantuml"``, ``"mermaid"``,
                ``"graphviz"``). Use ``list_diagram_types`` to see all options.
            source: The diagram source code.
            output_format: Output format — ``"svg"`` (default) or ``"png"``.
            as_base64: When True and format is ``"png"``, return a base64
                string instead of an MCP Image.

        Returns:
            SVG string, MCP Image (PNG), or base64 string (PNG + as_base64).
        """
        diagram_type = diagram_type.lower().strip()

        if diagram_type not in available:
            return (
                f"Unknown diagram type '{diagram_type}'. "
                "Use list_diagram_types to see what is available on this instance."
            )

        supported = DIAGRAM_TYPES[diagram_type]
        if output_format not in supported:
            return (
                f"'{output_format}' is not supported for '{diagram_type}'. "
                f"Supported: {', '.join(supported)}"
            )

        try:
            response = await client.post(
                f"{diagram_type}/{output_format}",
                content=source,
                headers={"Content-Type": "text/plain"},
            )
        except httpx.TransportError as exc:
            base_url = str(client.base_url)
            if isinstance(exc, httpx.TimeoutException):
                return "Kroki did not respond within 30s"
            return f"Cannot reach Kroki at {base_url} — is it running?"

        if response.status_code == 400:
            return response.text
        if response.status_code >= 400:
            return f"Kroki returned an error: {response.status_code} {response.text}"

        if output_format == "svg":
            return response.text

        # PNG
        png_bytes = response.content
        if as_base64:
            return base64.b64encode(png_bytes).decode()
        return Image(data=png_bytes, format="png")
