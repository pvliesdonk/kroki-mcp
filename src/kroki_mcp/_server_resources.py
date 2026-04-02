"""MCP resource registrations — Kroki health check.

Exposes ``kroki://health`` to check Kroki instance reachability.
"""

from __future__ import annotations

import json
import logging

import httpx
from fastmcp import FastMCP
from fastmcp.dependencies import Depends

from ._server_deps import get_service

logger = logging.getLogger(__name__)


def register_resources(mcp: FastMCP) -> None:
    """Register all MCP resources on *mcp*.

    Args:
        mcp: The :class:`~fastmcp.FastMCP` instance to register resources on.
    """

    @mcp.resource("kroki://health")
    async def health(
        client: httpx.AsyncClient = Depends(get_service),
    ) -> str:
        """Check if the Kroki instance is reachable.

        Returns:
            JSON with ``status`` (``"ok"`` or ``"unreachable"``),
            ``kroki_url``, and optionally ``error``.
        """
        base_url = str(client.base_url)
        try:
            response = await client.get("")
            response.raise_for_status()
            return json.dumps({"status": "ok", "kroki_url": base_url})
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError,
        ) as exc:
            return json.dumps(
                {
                    "status": "unreachable",
                    "kroki_url": base_url,
                    "error": str(exc),
                }
            )
